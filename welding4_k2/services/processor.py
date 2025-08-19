from multiprocessing import Array,Manager,Value
from datetime import datetime
from shared.utils import is_boxes_intersect,calculate_mask_rect_iou,is_point_in_polygon
from ..core import logger
from shared.services import BaseResultProcessor

class ResultProcessor(BaseResultProcessor):

    

    #机电学院焊接区域
    SAFE_AREA = [(1563, 0), (1520, 399), (2006, 554), (2159, 0)]#油桶和扫把安全区域

    WINDPIPE_AREA = (644, 879, 926, 1245)#一次线区域
    WELDING_GUN_AREA = (936, 880, 1546, 1279)#焊机区域
    VAVLE_AREA = (1578, 1028, 1866, 1116)#气管区域
    WELDING_TABLE_AREA = [(1563, 0), (1520, 399), (2006, 554), (2159, 0)]#焊台区域


    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        super().__init__(weights_paths,images_dir,img_url_path)

        self.reset_flag = Array('b', [True] * 3)
        self.exam_flag = Array('b', [False] * 9)
        self.manager = Manager()
        self.reset_imgs = self.manager.dict()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_score = self.manager.dict()#某一步骤考试分数
        self.exam_status = Value('b', False)

    
    def init_exam_variables(self):
        for i in range(len(self.exam_flag)):
            self.exam_flag[i] = False    
        self.exam_imgs.clear()
        self.exam_order[:]=[]

    def init_reset_variables(self):
        for i in range(len(self.reset_flag)):
            self.reset_flag[i] = True
        self.reset_imgs.clear()

    def process_result(self, r, weights_path):
        """Process results from the model - implementation of BaseResultProcessor method"""
        self.main_fun(r, weights_path)
        
    def main_fun(self, r, weights_path):

        if weights_path==self.weights_paths[0]:#目标检测（油桶和扫把）
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "oil_tank":
                    box=list(map(int, box))#转换为int类型
                    center_point = ((box[0]+box[2])//2,(box[1]+box[3])//2)
                    if is_point_in_polygon(center_point, self.SAFE_AREA):
                        self.reset_flag[0] = True#表面油桶不在危险区域，所以需要复位
                        self.exam_flag[0]=True#油桶已经排除在危险区域外
                    else:
                        self.reset_flag[0] = False#表面油桶在危险区域，所以不需要复位
                        self.reset_flag[1]=False# 临时赋值
                        self.exam_flag[0]=False#油桶已经检测到，所以还没有排除油桶


                elif r.names[int(cls)] == "sweep":
                    box=list(map(int, box))
                    center_point = ((box[0]+box[2])//2,(box[1]+box[3])//2)
                    if not is_point_in_polygon(center_point, self.SAFE_AREA):#表明扫把在工作区
                        self.exam_flag[7]=True
                    
                        
        elif weights_path==self.weights_paths[1]:#分割
            if r.masks is not None:
                masks = r.masks.xy #已经是list数组了
                #Todo: 加上判断分割出的物体是否是人
                for mask in masks:
                    iou1=calculate_mask_rect_iou(mask, self.WINDPIPE_AREA)#气管区域
                    iou2=calculate_mask_rect_iou(mask, self.WELDING_GUN_AREA)#焊枪区域
                    #logger.info(f"iou1:{iou1},iou2:{iou2},iou3:{iou3},iou4:{iou4}")
                    if iou1>0.01:
                        self.exam_flag[1]=True#检查气管
                    if iou2>0.01:
                        self.exam_flag[2]=True#检查切刀

        
        elif weights_path==self.weights_paths[2]:#分割
            if r.masks is not None:
                masks = r.masks.xy #已经是list数组了
                #Todo: 加上判断分割出的物体是否是人
                for mask in masks:
                    iou=calculate_mask_rect_iou(mask, self.VAVLE_AREA)#气瓶区域

                    #logger.info(f"iou1:{iou1},iou2:{iou2},iou3:{iou3},iou4:{iou4}")
                    if iou>0.01:
                        self.exam_flag[3]=True#气瓶区域检测到
                        if self.exam_flag[5]:#如果焊枪接地夹检测到
                            self.exam_flag[6]=True#焊枪接地夹检测到
                            self.exam_flag[7]=True
                            self.exam_flag[8]=True



        elif weights_path==self.weights_paths[3]:#目标检测开关灯，焊机，焊枪，搭铁线
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            
            iron_sheet_nums = 0#焊件数量
            for box, cls in zip(boxes, classes):


                if r.names[int(cls)] == "iron_sheet":#焊件
                    

                    box=list(map(int, box))#转换为int类型
                    # Calculate the area of the detection box
                    
                    center_point = ((box[0]+box[2])//2,(box[1]+box[3])//2)
                    if is_point_in_polygon(center_point, self.WELDING_TABLE_AREA):
                        self.reset_flag[2]=True
                        self.exam_flag[4]=True
                        box_area = (box[2] - box[0]) * (box[3] - box[1])
                        if box_area < 10000:  # 假设面积大于10000为有效焊件
                            iron_sheet_nums += 1
                    logger.info(f"box_area: {box_area}")
                    



            if iron_sheet_nums > 1:
                self.exam_flag[5]=True
          
            
        self.save_step(r,weights_path)
    
    def save_step(self,r,weights_path):

        reset_steps = {
        self.weights_paths[0]: [(self.reset_flag[0], 'reset_step_1'),
                                (self.reset_flag[1], 'reset_step_2'),
                                (self.reset_flag[2], 'reset_step_3')]
        }


        if not self.exam_status.value and weights_path in reset_steps:
            for flag, step in reset_steps[weights_path]:
                if flag and step not in self.reset_imgs:
                    self.save_image_reset(self.reset_imgs, r, step)


        exam_steps = {
            #油桶模型
            self.weights_paths[0]: [
            (self.exam_flag[0], 'welding_exam_1')
            ],
            #分割模型
            self.weights_paths[1]: [
            (self.exam_flag[1], 'welding_exam_2'),
            (self.exam_flag[2], 'welding_exam_3')
            ],
            #分割模型
            self.weights_paths[2]: [
            (self.exam_flag[3], 'welding_exam_4'),
            (self.exam_flag[6], 'welding_exam_7'),
            (self.exam_flag[7], 'welding_exam_8'),
            (self.exam_flag[8], 'welding_exam_9'),
            ],
            #目标检测
            self.weights_paths[3]: [
            (self.exam_flag[4], 'welding_exam_5'),
            (self.exam_flag[5], 'welding_exam_6')
            ]
        }

        if self.exam_status.value and weights_path in exam_steps:
            for flag, step in exam_steps[weights_path]:
                if flag and step not in self.exam_imgs:
                    self.save_image_exam(self.exam_imgs, r, step, self.exam_order)
                    if self.exam_flag[19]:          
                        self.exam_score[step]=8#TODO:计算分数,临时测试,10分值
                    else:
                        self.exam_score[step]=0
                     
    def save_image_reset(self,welding_reset_imgs,r, step_name):#保存图片
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{self.images_dir}/{step_name}_{save_time}.jpg"
        postpath = f"{self.img_url_path}/{step_name}_{save_time}.jpg"
        # annotated_frame = r.plot()
        # cv2.imwrite(imgpath, annotated_frame)
        r.save(imgpath)
        welding_reset_imgs[step_name]=postpath

    def save_image_exam(self,welding_exam_imgs,r, step_name,welding_exam_order):
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{self.images_dir}/{step_name}_{save_time}.jpg"
        postpath = f"{self.img_url_path}/{step_name}_{save_time}.jpg"
        r.save(imgpath)
        # annotated_frame = r.plot()
        # cv2.imwrite(imgpath, annotated_frame)
        welding_exam_imgs[step_name]=postpath
        welding_exam_order.append(step_name)
        logger.info(f"{step_name}完成")

