from multiprocessing import Array,Manager,Value
from datetime import datetime
from ..core import logger
from shared.utils import is_point_in_rect,is_boxes_intersect
from shared.services import BaseResultProcessor

class ResultProcessor(BaseResultProcessor):
    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        super().__init__(weights_paths, images_dir, img_url_path)

        self.human_postion=Value('b', False)  # 用来判断穿戴的人是否在指定位置
        self.save_img_flag=Value('b', False)  # 用来传递保存图片的标志
        self.img_saved=Value('b', False) # 若已保存图片，则设置为True

        self.manager = Manager()
        self.img_rul = self.manager.dict()#用来存放图片url

        self.wearing_items = self.manager.dict({
            "pants": 0,
            'jacket': 0,
            'helmet': 0,
            'gloves': 0,
            'shoes': 0
        })#存放穿戴物品的数量和种类，用来直接在多进程中进行传递数据

        self.detection_items = {
            "pants": 0,
            'jacket': 0,
            'helmet': 0,
            'gloves': 0,
            'shoes': 0
        }#用来在检测中记录，但不传递

    def reset_variables(self):
        #每次重置检测的变量
        for key in self.detection_items:
            self.detection_items[key] = 0

    def init_variables(self):
        logger.info("Resetting variables for wearing exam")
        #每次考试前重置变量
        self.human_postion.value = False
        self.save_img_flag.value = False
        self.img_saved.value = False
        for key in self.wearing_items:
            self.wearing_items[key] = 0
        for key in self.detection_items:
            self.detection_items[key] = 0


    def process_result(self, r, weights_path):
        """Process results from the model - implementation of BaseResultProcessor method"""
        self.main_fun(r, weights_path)

    def main_fun(self, r, weights_path):
        if weights_path==self.weights_paths[0]: #使用pose检测人
            self.human_postion.value=False
            boxes = r.boxes.xyxy.cpu().numpy()
            for box in boxes:
                if is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                    self.human_postion.value=True #人在指定位置
                                        
        if weights_path==self.weights_paths[1]:#目标检测
            
            self.reset_variables()
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            
            for box, cls in zip(boxes, classes):
                if is_boxes_intersect(tuple(map(int, box)), (0, 0, 1920, 1080)):
                    self.detection_items[r.names[int(cls)]] += 1#对应的物品数量加1
        
        self.save_step(r, weights_path)
    
    def save_step(self,r,weights_path):
        if weights_path==self.weights_paths[1]:
            if self.human_postion.value:
                self.wearing_items['pants'] = min(max(self.wearing_items['pants'], self.detection_items["pants"]), 1)
                self.wearing_items['jacket'] = min(max(self.wearing_items['jacket'] , self.detection_items["jacket"]), 1)
                self.wearing_items['helmet']  = min(max(self.wearing_items['helmet'] , self.detection_items["helmet"]), 1)
                self.wearing_items['gloves']  = min(max(self.wearing_items['gloves'] , self.detection_items["gloves"]), 2)
                self.wearing_items['shoes']  = min(max(self.wearing_items['shoes'] , self.detection_items["shoes"]), 2)

            if self.save_img_flag.value and not self.img_saved.value:
                save_time = datetime.now().strftime('%Y%m%d_%H%M')
                img_path = f"{self.images_dir}/welding_wearing_{save_time}.jpg"
                post_path = f"{self.img_url_path}/welding_wearing_{save_time}.jpg"
                r.save(img_path)
                self.img_rul['welding_wearing']=post_path
                self.img_saved.value=True
                logger.info(f"Image saved at {img_path}")
            



