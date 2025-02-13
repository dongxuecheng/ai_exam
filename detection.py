import logging
import cv2
from multiprocessing import Array,Manager,Value
from datetime import datetime
import numpy as np

logger = logging.getLogger("uvicorn")

class DetectionResultProcessor:
    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        self.reset_flag = Array('b', [False] * 6)
        self.exam_flag = Array('b', [False] * 24)
        self.manager = Manager()
        self.reset_imgs = self.manager.dict()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
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
            self.reset_flag[0] = True#默认油桶没有检测到，所以需要复位到危险区域
            self.exam_flag[0]=True#默认油桶没有检测到，所以需要排除油桶已完成

            classes = r.boxes.cls.cpu().numpy()
            for cls in classes:
                if r.names[int(cls)] == "oil_tank":
                    self.reset_flag[0] = False#表面油桶在危险区域，所以不需要复位
                    self.exam_flag[0]=False#油桶已经检测到，所以还没有排除油桶
                elif r.names[int(cls)] == "sweep":
                    self.exam_flag[21]=True#识别到扫把，代表场地清理已完成

        elif weights_path==self.weights_paths[1]:#目标检测，搭铁线
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "grounding_wire":
                    if self.is_boxes_intersect(tuple(map(int, box)), (851, 347, 2172, 1378)):
                        self.exam_flag[9]=True #搭铁线连接焊台
                    else:
                        if self.exam_flag[9]:
                            self.exam_flag[14]=False #搭铁线已取下

        elif weights_path==self.weights_paths[2]:#分类，焊台
            label=r.names[r.probs.top1]
            if label=="welding":
                self.exam_flag[11]=True
                self.exam_flag[12]=True
                self.exam_flag[13]=True
                self.exam_flag[14]=True
                self.exam_flag[15]=True

        elif weights_path==self.weights_paths[3]:#目标检测开关灯，焊机，焊枪，搭铁线
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            
            self.reset_flag[2] = True
            self.reset_flag[1] = True

            self.exam_flag[2]=True
            self.exam_flag[3]=True

            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "welding_gun":
                    if self.is_boxes_intersect(tuple(map(int, box)), (622, 472, 1039, 886)):#(x1,y1,x2,y2)
                        self.reset_flag[1] = False #焊枪在指定区域，不需要复位
                        self.exam_flag[2]=False
                    else:
                        self.exam_flag[2]=True 

                elif r.names[int(cls)] == "grounding_wire":
                    if self.is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                        self.reset_flag[2] = False
                        self.exam_flag[3]=False
                    else:
                        self.exam_flag[3]=True

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

        elif weights_path==self.weights_paths[4]:
            keypoints = r.keypoints.xy.cpu().numpy()
            #一次线区域
            LINE_REGION=[(1787, 442), (1498, 1378), (1765, 1378), (1993, 502)]
            WELDING_MACHINE_REGION=[(870, 907), (867, 1282), (152, 1282), (1505, 899)]
            if keypoints.size != 0:   
                for keypoint in keypoints:
                    left_wrist = tuple(map(int,keypoint[9]))#(x1,y1)
                    right_wrist = tuple(map(int,keypoint[10]))
                    if self.is_point_in_polygon(left_wrist, LINE_REGION):
                        self.exam_flag[1]=True
                    if self.is_point_in_polygon(right_wrist, LINE_REGION):
                        self.exam_flag[1]=True
                    if self.is_point_in_polygon(left_wrist, WELDING_MACHINE_REGION):
                        self.exam_flag[4]=True
                        self.exam_flag[5]=True
                    if self.is_point_in_polygon(right_wrist, WELDING_MACHINE_REGION):
                        self.exam_flag[4]=True
                        self.exam_flag[5]=True
            
        elif weights_path==self.weights_paths[5]:# 焊机开关
            
            classes = r.boxes.cls.cpu().numpy()
            for cls in classes:
                if r.names[int(cls)] == "open":
                    self.reset_flag[5] = True
                    self.exam_flag[5]=True
                elif r.names[int(cls)] == "close":
                    if self.exam_flag[5]:
                        self.exam_flag[15]=True           
            pass
            
        self.save_step(r,weights_path)
    
    def save_step(self,r,weights_path):
        reset_steps = {
            self.weights_paths[0]: (self.reset_flag[1], 'reset_step_2', "当前总开关没有复位"),
            self.weights_paths[1]: (self.reset_flag[0], 'reset_step_1', "当前油桶没有复位"),
            self.weights_paths[2]: (self.reset_flag[4], 'reset_step_5', "当前焊机开关没有复位"),
            self.weights_paths[3]: (self.reset_flag[2], 'reset_step_3', "搭铁线没有复位"),
            self.weights_paths[4]: (self.reset_flag[3], 'reset_step_4', "当前焊件没有复位")
        }

        if not self.exam_status.value and weights_path in reset_steps:
            flag, step, message = reset_steps[weights_path]
            if flag and step not in self.reset_imgs:
                logging.info(message)
                self.save_image_reset(self.reset_imgs, r, step)


        exam_steps = {
            self.weights_paths[1]: [
            (self.exam_flag[11], 'welding_exam_12'),
            (self.exam_flag[3], 'welding_exam_4'),
            (self.exam_flag[10], 'welding_exam_11'),
            (self.exam_flag[6], 'welding_exam_7')
            ],
            self.weights_paths[2]: [
            (self.exam_flag[0], 'welding_exam_1'),
            (self.exam_flag[13], 'welding_exam_14')
            ],
            self.weights_paths[3]: [
            (self.exam_flag[1], 'welding_exam_2'),
            (self.exam_flag[12], 'welding_exam_13')
            ],
            self.weights_paths[0]: [
            (self.exam_flag[4], 'welding_exam_5'),
            (self.exam_flag[8], 'welding_exam_9')
            ],
            self.weights_paths[4]: [
            (self.exam_flag[7], 'welding_exam_8'),
            (self.exam_flag[2], 'welding_exam_3'),
            (self.exam_flag[9], 'welding_exam_10'),
            (self.exam_flag[5], 'welding_exam_6')
            ]
        }

        if self.exam_status.value and weights_path in exam_steps:
            for flag, step in exam_steps[weights_path]:
                if flag and step not in self.exam_imgs:
                    self.save_image_exam(self.exam_imgs, r, step, self.exam_order)

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