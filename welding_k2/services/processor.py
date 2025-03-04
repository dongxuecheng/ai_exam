import cv2
from multiprocessing import Array,Manager,Value
from datetime import datetime
import numpy as np
from ..core import logger

class ResultProcessor:
    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        self.reset_flag = Array('b', [False] * 6)
        self.exam_flag = Array('b', [False] * 24)
        self.manager = Manager()
        self.reset_imgs = self.manager.dict()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_score = self.manager.dict()#某一步骤考试分数
        self.exam_status = Value('b', False)
        self.weights_paths = weights_paths
        self.images_dir=images_dir
        self.img_url_path=img_url_path
    
    def init_exam_variables(self):
        for i in range(len(self.exam_flag)):
            self.exam_flag[i] = False    
        self.exam_imgs.clear()
        self.exam_order[:]=[]


    def init_reset_variables(self):
        for i in range(len(self.reset_flag)):
            self.reset_flag[i] = False
        self.reset_imgs.clear()

    def main_fun(self, r, weights_path):

        if weights_path==self.weights_paths[0]:#目标检测（油桶和扫把）
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "oil_tank":
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.reset_flag[0] = False#表面油桶在危险区域，所以不需要复位
                        self.exam_flag[0]=False#油桶已经检测到，所以还没有排除油桶
                    else:
                        self.reset_flag[0] = True#表面油桶不在危险区域，所以需要复位
                        self.exam_flag[0]=True#油桶已经排除在危险区域外

                elif r.names[int(cls)] == "sweep":
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[21]=False


        elif weights_path==self.weights_paths[1]:#焊机垂直向下的分割，检测焊机二次线的视角
            if r.masks is not None:
                masks = r.masks.xy #已经是list数组了
                for mask in masks:
                    iou1=self.calculate_mask_rect_iou(mask, (622, 472, 1039, 886))#焊机区域
                    iou2=self.calculate_mask_rect_iou(mask, (0, 0, 1920, 1080))#焊枪二次线区域
                    iou3=self.calculate_mask_rect_iou(mask, (870, 907, 1505, 1282))#接地夹二次线区域
                    logger.info(f"iou1:{iou1},iou2:{iou2},iou3:{iou3}")
                    if iou1>0.5:
                        self.exam_flag[4]=True#焊机区域检测到
                        self.exam_flag[5]=True#焊机接地线直接判定完成
                    if iou2>0.5 and iou1<0.5:
                        self.exam_flag[2]=True#焊枪二次线区域检测到
                    if iou3>0.5 and iou1<0.5:
                        self.exam_flag[3]=True#接地夹二次线区域检测到


        

        elif weights_path==self.weights_paths[2]:#目标检测开关灯，焊机，焊枪，搭铁线
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            
            self.reset_flag[2] = True
            self.reset_flag[1] = True

            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "welding_gun":
                    if self.is_boxes_intersect(tuple(map(int, box)), (622, 472, 1039, 886)):#(x1,y1,x2,y2)
                        self.reset_flag[1] = False #焊枪在指定区域，不需要复位
                        if self.exam_flag[13]:#完成焊接作业
                            self.exam_flag[22]=True
                    else:
                        self.exam_flag[22]=False 

                elif r.names[int(cls)] == "grounding_wire":
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.reset_flag[2] = False
                        if self.exam_flag[13]:
                            self.exam_flag[23]=True
                    else:
                        self.exam_flag[23]=False

                elif r.names[int(cls)] == "red_light_on":#红灯亮,打开总开关
                    self.reset_flag[3]=True
                    self.exam_flag[6]=True
                    self.exam_flag[10]=True

                elif r.names[int(cls)] == "green_light_on":#绿灯亮，打开漏电保护开关
                    self.reset_flag[4]=True
                    self.exam_flag[7]=True

                elif r.names[int(cls)] == "red_light_off":#红灯灭，关闭总开关
                    if self.exam_flag[6]:
                        self.exam_flag[17]=True
                        self.exam_flag[18]=True

                elif r.names[int(cls)] == "green_light_off":#绿灯灭，关闭漏电保护开关
                    if self.exam_flag[7]:
                        self.exam_flag[16]=True

        if weights_path==self.weights_paths[3]:#目标检测（焊台上的搭铁线，焊件，刷子，铁锤）
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "grounding_wire":#接地夹
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[9]=True#夹好接地夹


                elif r.names[int(cls)] == "welding_piece":#焊件
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[11]=False
                
                elif r.names[int(cls)] == "brush":#刷子
                    if self.exam_flag[13]:
                        self.exam_flag[19]=True
                elif r.names[int(cls)] == "hammer":#铁锤
                    if self.exam_flag[13]:
                        self.exam_flag[19]=True

        elif weights_path==self.weights_paths[4]:#分类，焊台
            label=r.names[r.probs.top1]
            if label=="welding":
   
                self.exam_flag[12]=True
                self.exam_flag[13]=True


            
        elif weights_path==self.weights_paths[5]:# 焊机开关
            
            classes = r.boxes.cls.cpu().numpy()
            for cls in classes:
                if r.names[int(cls)] == "open":
                    self.reset_flag[5] = True
                    self.exam_flag[8]=True
                elif r.names[int(cls)] == "close":
                    if self.exam_flag[8]:
                        self.exam_flag[15]=True           

        elif weights_path==self.weights_paths[6]:#焊机垂直向下的分割，检测焊机二次线的视角
            if r.masks is not None:
                masks = r.masks.xy #已经是list数组了
                for mask in masks:
                    iou=self.calculate_mask_rect_iou(mask, (622, 472, 1039, 886))#焊机区域

                    logger.info(f"焊机一次线iou:{iou}")
                    if iou>0.5:
                        self.exam_flag[1]=True
             
            
        self.save_step(r,weights_path)
    
    def save_step(self,r,weights_path):
        # reset_steps = {
        #     self.weights_paths[3]: (self.reset_flag[1], 'reset_step_2', "当前焊枪没有复位"),
        #     self.weights_paths[0]: (self.reset_flag[0], 'reset_step_1', "当前油桶没有复位"),
        #     self.weights_paths[2]: (self.reset_flag[4], 'reset_step_5', "当前焊机开关没有复位"),
        #     self.weights_paths[3]: (self.reset_flag[2], 'reset_step_3', "搭铁线没有复位"),
        #     self.weights_paths[4]: (self.reset_flag[3], 'reset_step_4', "当前焊件没有复位")
        # }
        reset_steps = {
        self.weights_paths[0]: [(self.reset_flag[0], 'reset_step_1'),],
        self.weights_paths[3]: [(self.reset_flag[1], 'reset_step_2'),
                                (self.reset_flag[2], 'reset_step_3'),
                                (self.reset_flag[3], 'reset_step_4'),
                                (self.reset_flag[4], 'reset_step_5')],
        self.weights_paths[5]: [(self.reset_flag[5], 'reset_step_6')]
    }

        # if not self.exam_status.value and weights_path in reset_steps:
        #     flag, step, message = reset_steps[weights_path]
        #     if flag and step not in self.reset_imgs:
        #         logger.info(message)
        #         self.save_image_reset(self.reset_imgs, r, step)

        if not self.exam_status.value and weights_path in reset_steps:
            for flag, step in reset_steps[weights_path]:
                if flag and step not in self.reset_imgs:
                    self.save_image_reset(self.reset_imgs, r, step)


        exam_steps = {
            self.weights_paths[0]: [
            (self.exam_flag[0], 'welding_exam_1'),
            (self.exam_flag[21], 'welding_exam_22'),
            ],
            self.weights_paths[1]: [
            (self.exam_flag[9], 'welding_exam_10'),
            (self.exam_flag[14], 'welding_exam_15'),
            ],
            self.weights_paths[2]: [
            (self.exam_flag[11], 'welding_exam_12'),
            (self.exam_flag[12], 'welding_exam_13'),
            (self.exam_flag[13], 'welding_exam_14'),
            (self.exam_flag[19], 'welding_exam_20'),
            (self.exam_flag[20], 'welding_exam_21'),
            ],
            self.weights_paths[3]: [

            (self.exam_flag[6], 'welding_exam_7'),
            (self.exam_flag[7], 'welding_exam_8'),
            (self.exam_flag[10], 'welding_exam_11'),
            (self.exam_flag[16], 'welding_exam_17'),
            (self.exam_flag[17], 'welding_exam_18'),
            (self.exam_flag[18], 'welding_exam_19'),
            (self.exam_flag[22], 'welding_exam_23'),
            (self.exam_flag[23], 'welding_exam_24'),
            ],
            self.weights_paths[4]: [
            (self.exam_flag[1], 'welding_exam_2'),
            (self.exam_flag[2], 'welding_exam_3'),
            (self.exam_flag[3], 'welding_exam_4'),
            (self.exam_flag[4], 'welding_exam_5'),
            (self.exam_flag[5], 'welding_exam_6'),
            ],
            self.weights_paths[5]: [
            (self.exam_flag[8], 'welding_exam_9'),
            (self.exam_flag[15], 'welding_exam_16'),
            ]
        }

        if self.exam_status.value and weights_path in exam_steps:
            for flag, step in exam_steps[weights_path]:
                if flag and step not in self.exam_imgs:
                    self.save_image_exam(self.exam_imgs, r, step, self.exam_order)
                    self.exam_score[step]=10#TODO:计算分数,临时测试

    def save_image_reset(self,welding_reset_imgs,r, step_name):#保存图片
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{self.images_dir}/{step_name}_{save_time}.jpg"
        postpath = f"{self.img_url_path}/{step_name}_{save_time}.jpg"
        annotated_frame = r.plot()
        cv2.imwrite(imgpath, annotated_frame)
        welding_reset_imgs[step_name]=postpath

    def save_image_exam(self,welding_exam_imgs,r, step_name,welding_exam_order):
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{self.images_dir}/{step_name}_{save_time}.jpg"
        postpath = f"{self.img_url_path}/{step_name}_{save_time}.jpg"
        annotated_frame = r.plot()
        cv2.imwrite(imgpath, annotated_frame)
        welding_exam_imgs[step_name]=postpath
        welding_exam_order.append(step_name)
        logger.info(f"{step_name}完成")

    @staticmethod
    def is_boxes_intersect(box1: tuple[int, int, int, int], 
                      box2: tuple[int, int, int, int]) -> bool:

        box1_x1, box1_y1, box1_x2, box1_y2 = box1
        box2_x1, box2_y1, box2_x2, box2_y2 = box2
        
        # Check if one box is to the left of the other
        if box1_x2 < box2_x1 or box2_x2 < box1_x1:
            return False
            
        # Check if one box is above the other
        if box1_y2 < box2_y1 or box2_y2 < box1_y1:
            return False
        
        return True
    
    @staticmethod
    def is_point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:

        # Convert point to float32
        point = np.float32(point)
        
        # Convert polygon vertices to the format required by cv2.pointPolygonTest
        contour = np.array(polygon, dtype=np.float32)
        
        # Reshape contour to required format (n,1,2)
        contour = contour.reshape((-1, 1, 2))
        
        # Use pointPolygonTest to check if point is inside polygon
        # Return value > 0 means point is inside
        # Return value = 0 means point is on the boundary
        # Return value < 0 means point is outside
        result = cv2.pointPolygonTest(contour, tuple(point), False)
        
        return result >= 0

    @staticmethod
    def calculate_mask_rect_iou(mask: np.ndarray, rect: tuple[int, int, int, int]) -> float:
        """
        计算掩码与矩形区域的交并比(IoU)
        
        参数:
            mask: 掩码点的坐标数组，形状为(n,2)，每行是一个(x,y)点坐标
            rect: 矩形区域，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
            
        返回:
            float: IoU值，范围从0到1
        """
        if len(mask) == 0:
            return 0.0
        
        # 创建掩码的二值图像
        x1_rect, y1_rect, x2_rect, y2_rect = rect
        width = max(x2_rect, np.max(mask[:, 0]).astype(int)) + 1
        height = max(y2_rect, np.max(mask[:, 1]).astype(int)) + 1
        
        # 创建掩码图像
        mask_img = np.zeros((height, width), dtype=np.uint8)
        mask_points = np.array(mask, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask_img, [mask_points], 1)
        
        # 创建矩形图像
        rect_img = np.zeros((height, width), dtype=np.uint8)
        cv2.rectangle(rect_img, (x1_rect, y1_rect), (x2_rect, y2_rect), 1, -1)
        
        # 计算交集和并集
        intersection = np.logical_and(mask_img, rect_img).sum()
        union = np.logical_or(mask_img, rect_img).sum()
        
        # 计算IoU
        if union == 0:
            return 0.0
        iou = intersection / union
        
        return iou