from multiprocessing import Array,Manager,Value
from datetime import datetime
from ..core import logger
from shared.utils import is_point_in_rect,is_boxes_intersect,is_point_in_polygon
from shared.services import BaseResultProcessor

class ResultProcessor(BaseResultProcessor):
    ANCHOR_POINT_REGION = [
        (0, 0, 1920, 1080)
    ]
    WORKING_ROPE_REGION = [
        (0, 0, 1920, 1080)
    ]
    SAFETY_ROPE_REGION = [
        (0, 0, 1920, 1080)
    ]


    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        super().__init__(weights_paths, images_dir, img_url_path)
        self.exam_flag = Array('b', [False] * 12)
        self.warning_zone_flag=Array('b', [False] * 2)#存储两个视角下的警戒区域的检测结果
        self.manager = Manager()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_status = Value('b', False)

    
    def init_exam_variables(self):
        for i in range(len(self.exam_flag)):
            self.exam_flag[i] = False    
        self.exam_imgs.clear()
        self.exam_order[:]=[]

    def process_result(self, r, weights_path):
        """Process results from the model - implementation of BaseResultProcessor method"""
        self.main_fun(r, weights_path)

    def main_fun(self, r, weights_path):
        if weights_path==self.weights_paths[0]:  # 姿态估计
            keypoints = r.keypoints.xy.cpu().numpy()
            if keypoints.size != 0:
                for keypoint in keypoints:
                    left_wrist = list(map(int, keypoint[9]))
                    right_wrist = list(map(int, keypoint[10]))


                    points = [left_wrist, right_wrist]


                    if not self.exam_flag[1]:
                        is_inside = any(is_point_in_polygon(point,self.ANCHOR_POINT_REGION) for point in points)
                        if is_inside:
                            self.exam_flag[1]=True
                    
        if weights_path==self.weights_paths[1]:#目标检测(警戒区)
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            self.warning_zone_flag[0]=False
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "warning_zone":
                    if is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[0]=True#警戒区域检测到
                        self.warning_zone_flag[0]=True
        
        if weights_path==self.weights_paths[2]:#姿态估计，判断手部是否检查对应物品
            keypoints = r.keypoints.xy.cpu().numpy()
            if keypoints.size != 0:
                for keypoint in keypoints:
                    left_wrist = list(map(int, keypoint[9]))
                    right_wrist = list(map(int, keypoint[10]))


                    points = [left_wrist, right_wrist]


                    if not self.exam_flag[3]:
                        is_inside = any(is_point_in_polygon(point,self.WORKING_ROPE_REGION) for point in points)
                        if is_inside:
                            self.exam_flag[3]=True
                    
                    if not self.exam_flag[4]:
                        is_inside = any(is_point_in_polygon(point,self.SAFETY_ROPE_REGION) for point in points)
                        if is_inside:
                            self.exam_flag[4]=True



        if weights_path==self.weights_paths[3]:
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()           
            safety_belt_position=None
            self_locking_position=None
            self.warning_zone_flag[1]=False
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "brush":
                    if is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[9]=True
                
                if r.names[int(cls)] == "warning_zone":
                    if is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.exam_flag[0]=True#警戒区域检测到
                        self.warning_zone_flag[1]=True

                if r.names[int(cls)] == "safety_belt":
                    safety_belt_position=tuple(map(int, box))

                if r.names[int(cls)] == "self_locking":
                    self_locking_position=tuple(map(int, box))
            
            if safety_belt_position is not None and self_locking_position is not None:
                if is_boxes_intersect(safety_belt_position,self_locking_position):
                    self.exam_flag[7]=True



        self.save_step(r, weights_path)
    
    def save_step(self,r,weights_path):

        # Restructure exam_steps to be a dictionary with weights_path as keys
        exam_steps = {
            self.weights_paths[0]: [(self.exam_flag[1], "sling_step_2")],
            self.weights_paths[2]: [
                (self.exam_flag[2], "sling_step_3"),
                (self.exam_flag[3], "sling_step_4"),
                (self.exam_flag[4], "sling_step_5"),
                (self.exam_flag[5], "sling_step_6"),
                (self.exam_flag[6], "sling_step_7"),
                (self.exam_flag[7], "sling_step_8"),
            ],
            self.weights_paths[3]: [
                (self.exam_flag[0], "sling_step_1"),
                (self.exam_flag[11], "sling_step_12"),
                (self.exam_flag[9], "sling_step_10"),
                (self.exam_flag[10], "sling_step_11"),
                (self.exam_flag[8], "sling_step_9"),
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

