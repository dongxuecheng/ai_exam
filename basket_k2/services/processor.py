from multiprocessing import Array,Manager,Value
from datetime import datetime
from ..core import logger
from shared.utils import is_point_in_rect,is_boxes_intersect,is_point_in_polygon
from shared.services import BaseResultProcessor

class ResultProcessor(BaseResultProcessor):
    #悬挂机构
    SUSPENSION_REGION = [
        (491, 0, 762, 910),  
        (1281, 102, 1535, 793),
        (1668, 231, 1936, 778)
    ]
    #正面警戒区
    WARNING_ZONE_REGION = (986, 734, 1802, 1239)
    #WARNING_ZONE_REGION = (1888, 756, 2112, 1236)
    
    #钢丝绳区域
    STEEL_WIRE_REGION = [
        [(490, 239), (544, 423), (706, 374), (663, 201)],
        (1312, 661), (1615, 886), (1369, 1245), (1141, 1061)
    ]

    #吊篮平台区域
    PLATFORM_REGION=[(424, 654), (1127, 1439), (1377, 1359), (1518, 1046), (797, 391)]

    SAFETY_LOCK_REGION = [
        [(1152, 1095), (1393, 1312), (1536, 1124), (1291, 918)],
        [(472, 362), (621, 621), (803, 515), (664, 263)]
    ]  # 安全锁区域

    
    #左边和右边的提升机区域
    HOIST_REGION = [
        [(622, 608), (759, 841), (930, 726), (793, 506)],
        [(1073, 1156), (1205, 1296), (1355, 1127), (1222, 1017)]
    ] 

    ELECTRICAL_SYSTEM_REGION = [(1002, 783), (1288, 1049), (1495, 837), (1220, 608)]

    # BASKET_HOIST_HIGH_REGION=(0, 0, 400, 1080)#提升机的空载区域

    # 清洗工作区
    WORK_REGIONS = [(8, 1439), (1232, 1437), (1337, 1141), (181, 0), (0, 1)]

    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        super().__init__(weights_paths,images_dir, img_url_path)
        self.exam_flag = Array('b', [False] * 12)
        #self.warning_zone_flag=Array('b', [False] * 2)#存储两个视角下的警戒区域的检测结果
        self.manager = Manager()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_status = Value('b', False)
        self.person_status=Value('b', False)

        #self.seg_region=self.manager.dict()#用于存储吊篮的分割区域

    
    def init_exam_variables(self):
        for i in range(len(self.exam_flag)):
            self.exam_flag[i] = False    
        self.exam_imgs.clear()
        self.exam_order[:]=[]

    def process_result(self, r, weights_path):
        """Process results from the model - implementation of BaseResultProcessor method"""
        self.main_fun(r, weights_path)

    def main_fun(self, r, weights_path):
        if weights_path==self.weights_paths[0] and not self.exam_flag[1]:  # 姿态估计,检查悬挂机构
            if r.keypoints is None:
                return
            keypoints = r.keypoints.xy.cpu().numpy()
            if keypoints.size != 0:
                for keypoint in keypoints:
                    try:
                        left_wrist = list(map(int, keypoint[9]))
                        right_wrist = list(map(int, keypoint[10]))
                        for region in self.SUSPENSION_REGION:
                            if is_point_in_rect(left_wrist, region) or is_point_in_rect(right_wrist, region):
                                self.exam_flag[1]=True               
                                break                                                                
                    except (IndexError, ValueError) as e:
                        logger.error(f"处理关键点时出错: {e}")
                        continue

        if weights_path==self.weights_paths[1]:#正面警戒区
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "warning_zone":#当警戒区的中点在指定区域内
                    center_point=(int((box[0]+box[2])/2), int((box[1]+box[3])/2))
                    if not self.exam_flag[0] and is_point_in_rect(center_point, self.WARNING_ZONE_REGION):
                        self.exam_flag[0]=True
                    if self.exam_flag[0] and not self.exam_flag[10] and is_point_in_rect(center_point,(1841, 737, 2558, 1438)):
                        self.exam_flag[10]=True
                        self.exam_flag[11]=True

        if weights_path==self.weights_paths[2]:#姿态估计，吊篮顶部视角
        
            if r.keypoints is None:
                return
            keypoints = r.keypoints.xy.cpu().numpy()
            if keypoints.size != 0:
                for keypoint in keypoints:
                    try:
                        left_wrist = list(map(int, keypoint[9]))
                        right_wrist = list(map(int, keypoint[10]))
                        
                        left_eye=list(map(int, keypoint[1]))
                        right_eye=list(map(int, keypoint[2]))
                        nose=list(map(int, keypoint[0]))

                        if is_point_in_polygon(nose, self.PLATFORM_REGION) or is_point_in_polygon(left_eye, self.PLATFORM_REGION) or is_point_in_polygon(right_eye, self.PLATFORM_REGION):
                            self.person_status.value=True
                        else:
                            self.person_status.value=False

                        for region in self.STEEL_WIRE_REGION:
                            if not self.exam_flag[2] and (is_point_in_polygon(left_wrist, region) or is_point_in_polygon(right_wrist, region)):
                                self.exam_flag[2]=True               
                                break    

                        if not self.exam_flag[3] and (is_point_in_polygon(left_wrist, self.PLATFORM_REGION) or is_point_in_polygon(right_wrist, self.PLATFORM_REGION)):
                            self.exam_flag[3]=True

                        for region in self.HOIST_REGION:
                            if not self.exam_flag[4] and (is_point_in_polygon(left_wrist, region) or is_point_in_polygon(right_wrist, region)):
                                self.exam_flag[4]=True               
                                break

                        for region in self.SAFETY_LOCK_REGION:
                            if not self.exam_flag[5] and (is_point_in_polygon(left_wrist, region) or is_point_in_polygon(right_wrist, region)):
                                self.exam_flag[5]=True               
                                break
                        if not self.exam_flag[6] and (is_point_in_polygon(left_wrist, self.ELECTRICAL_SYSTEM_REGION) or is_point_in_polygon(right_wrist, self.ELECTRICAL_SYSTEM_REGION)):
                            self.exam_flag[6]=True

                    except (IndexError, ValueError) as e:
                        logger.error(f"处理关键点时出错: {e}")
                        continue

        if weights_path==self.weights_paths[3]:#hoist
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "hoist":#当其中一个提升机与指定的区域相交
                    if is_boxes_intersect(tuple(map(int, box)), (633, 354, 795, 526)) or is_boxes_intersect(tuple(map(int, box)), (1176, 878, 1340, 1038)) and self.person_status.value:
                        self.exam_flag[7]=True

        if weights_path==self.weights_paths[4]:#吊篮顶部 检查安全带挂设相关
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()           
            safety_belt_position=None
            self_locking_position=None
            #hoist_position=[]
            #self.warning_zone_flag[1]=False
            
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "brush":#刷子出现在指定区域则完成清洗
                    center_point=(int((box[0]+box[2])/2), int((box[1]+box[3])/2))
                    if is_point_in_polygon(center_point, self.WORK_REGIONS):
                        self.exam_flag[9]=True                  

                if r.names[int(cls)] == "safety_belt":
                    safety_belt_position=tuple(map(int, box))

                if r.names[int(cls)] == "self_locking":
                    self_locking_position=tuple(map(int, box))

            if safety_belt_position is not None and self_locking_position is not None:
                if is_boxes_intersect(safety_belt_position,self_locking_position):
                    self.exam_flag[8]=True
    

        self.save_step(r, weights_path)
    
    def save_step(self,r,weights_path):

        # Restructure exam_steps to be a dictionary with weights_path as keys
        exam_steps = {
            self.weights_paths[1]: [
                (self.exam_flag[0], "basket_step_1"),                
                (self.exam_flag[10], "basket_step_11"),
                (self.exam_flag[11], "basket_step_12")
            ],
            self.weights_paths[0]: [(self.exam_flag[1], "basket_step_2")],
            self.weights_paths[2]: [
                (self.exam_flag[1], "basket_step_2"),
                (self.exam_flag[2], "basket_step_3"),
                (self.exam_flag[3], "basket_step_4"),
                (self.exam_flag[4], "basket_step_5"),
                (self.exam_flag[5], "basket_step_6"),
                (self.exam_flag[6], "basket_step_7"),
                
            ],
            self.weights_paths[3]: [(self.exam_flag[7], "basket_step_8")],
            self.weights_paths[4]: [
                (self.exam_flag[0], "basket_step_1"),
                (self.exam_flag[8], "basket_step_9"),
                (self.exam_flag[9], "basket_step_10"),

            ]
        }
        
        if self.exam_status.value and weights_path in exam_steps:
            for flag, step in exam_steps[weights_path]:
                if flag and step not in self.exam_imgs:
                    self.save_image_exam(self.exam_imgs, r, step, self.exam_order)

    #TODO 还需要修改
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

