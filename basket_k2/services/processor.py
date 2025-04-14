from multiprocessing import Array,Manager,Value
from datetime import datetime
from ..core import logger
from shared.utils import is_point_in_rect,is_boxes_intersect,is_point_in_polygon,calculate_rect_polygon_iou
from shared.services import BaseResultProcessor

class ResultProcessor(BaseResultProcessor):
    def __init__(self,weights_paths: list[str],images_dir, img_url_path):
        super().__init__(weights_paths,images_dir, img_url_path)
        self.exam_flag = Array('b', [False] * 12)
        self.warning_zone_flag=Array('b', [False] * 2)#存储两个视角下的警戒区域的检测结果
        self.manager = Manager()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_status = Value('b', False)

        self.seg_region=self.manager.dict()#用于存储吊篮的分割区域

    
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
                    try:
                        left_wrist = list(map(int, keypoint[9]))
                        right_wrist = list(map(int, keypoint[10]))
                        
                        # 定义悬挂区域的四个方形区域
                        SUSPENSION_REGIONS = [
                            (0, 0, 400, 400),       # 左上区域 (x1, y1, x2, y2)
                            (0, 680, 400, 1080),    # 左下区域
                            (1520, 0, 1920, 400),   # 右上区域
                            (1520, 680, 1920, 1080) # 右下区域
                        ]
                        
                        # 检查左右手腕是否在任意悬挂区域内
                        for region in SUSPENSION_REGIONS:
                            # 检查左手腕
                            if is_point_in_rect(left_wrist, region):
                                self.exam_flag[1] = True
                                logger.info(f"左手腕 {left_wrist} 在悬挂区域 {region} 中")
                                break
                                
                            # 检查右手腕
                            if is_point_in_rect(right_wrist, region):
                                self.exam_flag[1] = True
                                logger.info(f"右手腕 {right_wrist} 在悬挂区域 {region} 中")
                                break
                                
                    except (IndexError, ValueError) as e:
                        logger.error(f"处理关键点时出错: {e}")
                        continue
                    
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

                    BASKET_STEEL_WIRE_REGION = [
                        [(374, 846), (601, 970), (630, 900), (441, 786)],  # 右一多边形区域
                        [(1518, 736), (1649, 945), (2005, 917), (1888, 677)]  # 右二多边形区域
                    ]#钢丝绳区域，暂时没有钢丝绳的区域

                    BASKET_SAFETY_LOCK_REGION = [
                        [(1635, 813), (1742, 927), (1955, 910), (1906, 747)],
                        [(650, 944), (800, 1000), (800, 923), (680, 872)]
                    ]  # 安全锁区域

                    points = [left_wrist, right_wrist]
                    if not self.exam_flag[2]:
                        is_inside1 = any(is_point_in_polygon(point, BASKET_STEEL_WIRE_REGION[0]) for point in points)
                        is_inside2 = any(is_point_in_polygon(point, BASKET_STEEL_WIRE_REGION[1]) for point in points)
                        if is_inside1 or is_inside2:
                            self.exam_flag[2]=True

                    if not self.exam_flag[3] and 'platform' in self.seg_region:
                        is_inside = any(is_point_in_polygon(point,self.seg_region['platform']) for point in points)
                        if is_inside:
                            self.exam_flag[3]=True

                    if not self.exam_flag[4] and 'hoist_l' in self.seg_region and 'hoist_r' in self.seg_region:
                        is_inside1 = any(is_point_in_polygon(point,self.seg_region['hoist_l']) for point in points)
                        is_inside2 = any(is_point_in_polygon(point,self.seg_region['hoist_r']) for point in points)   
                        if is_inside1 or is_inside2:
                            self.exam_flag[4]=True

                    if not self.exam_flag[5]:
                        is_inside1 = any(is_point_in_polygon(point, BASKET_SAFETY_LOCK_REGION[0]) for point in points)
                        is_inside2 = any(is_point_in_polygon(point, BASKET_SAFETY_LOCK_REGION[1]) for point in points)
                        
                        if is_inside1 or is_inside2:
                            self.exam_flag[5]=True

                    if not self.exam_flag[6] and 'electricalSystem' in self.seg_region:
                        is_inside = any(is_point_in_polygon(point,self.seg_region['electricalSystem']) for point in points)
                        if is_inside:
                            self.exam_flag[6]=True

            #暂时没有加检测人的逻辑
            if 'platform' in self.seg_region and not self.exam_flag[7]:
                #self.exam_flag[7]=True
                if calculate_rect_polygon_iou([446,883,765,1163],self.seg_region['platform'])>0.01:
                    self.exam_flag[7]=True#空载

        if weights_path==self.weights_paths[3]:#分割，实时获取吊篮区域
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()            
            if r.masks is not None:
                masks = r.masks.xy #已经是list数组了
                for box, cls,mask in zip(boxes, classes,masks):
                    # 将掩码转换为 list[tuple[int, int]] 格式
                    mask = [(int(x), int(y)) for x, y in mask]
                    #logger.info(mask)
                    if r.names[int(cls)] == "basket":
                        self.seg_region['basket']=mask
                    if r.names[int(cls)] == "hoist_l":
                        self.seg_region['hoist_l']=mask
                    if r.names[int(cls)] == "hoist_r":
                        self.seg_region['hoist_r']=mask
                    if r.names[int(cls)] == "electricalSystem":
                        self.seg_region['electricalSystem']=mask

        if weights_path==self.weights_paths[4]:
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

            if not self.warning_zone_flag[0] and not self.warning_zone_flag[1] and self.exam_flag[0] and self.exam_flag[9]:#当检测不到警戒区时,判定未拆除警戒区域
                self.exam_flag[11]=True
                self.exam_flag[10]=True

            if safety_belt_position is not None and self_locking_position is not None:
                if is_boxes_intersect(safety_belt_position,self_locking_position):
                    self.exam_flag[8]=True

        self.save_step(r, weights_path)
    
    def save_step(self,r,weights_path):

        # Restructure exam_steps to be a dictionary with weights_path as keys
        exam_steps = {
            self.weights_paths[0]: [(self.exam_flag[1], "basket_step_2")],
            self.weights_paths[2]: [
                (self.exam_flag[2], "basket_step_3"),
                (self.exam_flag[3], "basket_step_4"),
                (self.exam_flag[4], "basket_step_5"),
                (self.exam_flag[5], "basket_step_6"),
                (self.exam_flag[6], "basket_step_7"),
                (self.exam_flag[7], "basket_step_8"),
            ],
            self.weights_paths[3]: [
                (self.exam_flag[0], "basket_step_1"),
                (self.exam_flag[11], "basket_step_12"),
                (self.exam_flag[9], "basket_step_10"),
                (self.exam_flag[10], "basket_step_11"),
                (self.exam_flag[8], "basket_step_9"),
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

