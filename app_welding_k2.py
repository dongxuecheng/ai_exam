from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from typing import Dict, List
import logging
import yaml
from pathlib import Path
import cv2
from multiprocessing import Queue, Event, Process,Array,Manager,Value
from ultralytics import YOLO
from datetime import datetime
import re

# Constants
CONFIG_FILE = Path("config.yaml")
IMAGES_DIR = Path("./images/welding_k2")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Config management
def load_config() -> Dict:
    """Load application configuration"""
    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}")

def get_rtsp_urls(config: dict) -> List[str]:
    base_url = config["rtsp"]["base_url"]
    common_path = config["rtsp"]["common_path"]
    channels = config["rtsp"]["welding_k2"]["channels"]
    
    return [f"{base_url}{channel}{common_path}" for channel in channels]

# Logger setup
logger = logging.getLogger("uvicorn")

# Load config
config = load_config()
SERVER_IP = config["server"]["ip"]
SERVER_PORT = int(config["server"]["welding_k2"]["port"])
RTSP_URLS = get_rtsp_urls(config)
IMG_URL_PATH = f'http://{config["server"]["ip"]}:{config["server"]["welding_k2"]["port"]}/{config["paths"]["welding_k2"]["save_img"]}'
MODEL_PATHS = [
    config["models"]["welding_k2"][f"ch{i}"]
    for i in range(1, 7)
]


# Response types
SUCCESS_RESPONSE = {"status": "SUCCESS"}
FAILURE_RESPONSE = {"status": "FAILURE"}

# FastAPI app
app = FastAPI(
    title="Welding K2 API",
    description="API for welding examination control system",
    version="1.0.0"
)

# Static files
app.mount("/images/welding_k2", StaticFiles(directory=IMAGES_DIR))



class VideoStreamManager:
    def __init__(self, rtsp_urls: List[str]):
        self.rtsp_urls = rtsp_urls
        self.frame_queues = [Queue(maxsize=100) for _ in range(6)]
        self.processes: List[Process] = []
        self.start_events = [Event() for _ in range(6)]
        self.stop_events = [Event() for _ in range(6)]

    def start_streams(self):
        for i, url in enumerate(self.rtsp_urls):
            process = Process(
                target=self._fetch_video_stream,
                args=(url, i, self.start_events[i], self.stop_events[i])
            )
            process.start()
            self.processes.append(process)
            
        # Wait for all processes to start
        for event in self.start_events:
            event.wait()
            
    def stop_streams(self):
        # Stop all processes
        for stop_event in self.stop_events:
            stop_event.set()
            
        for process in self.processes:
            try:
                process.join(timeout=3)
                if process.is_alive():
                    logger.warning(f"Terminating process {process.pid}")
                    process.terminate()
                    # process.join(timeout=1)
                    # if process.is_alive():
                    #     process.kill()
            except Exception as e:
                logger.error(f"Failed to stop inference process {process.pid}: {e}")
        
        self._reset_queues()
        self.processes.clear()
        # self.start_events.clear()
        # self.stop_events.clear()
        logger.info("All streams stopped")

    def _fetch_video_stream(self, rtsp_url: str, index: int, start_event: Event, stop_event: Event):
        cap = cv2.VideoCapture(rtsp_url)
        while cap.isOpened():
            if stop_event.is_set():  # 控制停止推理
                logger.info("fetch_video_stream is stopped")
                break
            ret, frame = cap.read()
            if not ret:
                break

            if cap.get(cv2.CAP_PROP_POS_FRAMES) % 5 != 0:
                continue
            if not start_event.is_set():
                start_event.set()
                logger.info(f"Started stream: {rtsp_url}")
            self.frame_queues[index].put_nowait(frame)
        cap.release()

    def _reset_queues(self):
        for queue in self.frame_queues:
            while not queue.empty():
                queue.get_nowait()
                logger.info("Queue get-----")
            #logger.info("queues reset")

class DetectionResultProcessor:
    def __init__(self):
        self.reset_flag = Array('b', [False] * 6)
        self.exam_flag = Array('b', [False] * 24)
        self.manager = Manager()
        self.reset_imgs = self.manager.dict()
        self.exam_imgs = self.manager.dict()
        self.exam_order = self.manager.list()
        self.exam_status = Value('b', False)
        self.model_paths = MODEL_PATHS
    
    def init_exam_variables(self):
        for i in range(len(self.exam_flag)):
            self.exam_flag[i] = False    
        self.exam_imgs.clear()
        self.exam_order[:]=[]


    def init_reset_variables(self):
        for i in range(len(self.reset_flag)):
            self.reset_flag[i] = False
        self.reset_imgs.clear()

    def main_fun(self, r, model_path):
        if model_path==self.model_paths[0]:
            boxes = r.boxes.xyxy.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy()
            for box, cls in zip(boxes, classes):
                if r.names[int(cls)] == "close":
                    #logger.info(f"turn_on box: {box}")
                    self.exam_flag[4] = True
        self.save_step(r,model_path)
    
    def save_step(self,r,model_path):
        reset_steps = {
            self.model_paths[0]: (self.reset_flag[1], 'reset_step_2', "当前总开关没有复位"),
            self.model_paths[1]: (self.reset_flag[0], 'reset_step_1', "当前油桶没有复位"),
            self.model_paths[2]: (self.reset_flag[4], 'reset_step_5', "当前焊机开关没有复位"),
            self.model_paths[3]: (self.reset_flag[2], 'reset_step_3', "搭铁线没有复位"),
            self.model_paths[4]: (self.reset_flag[3], 'reset_step_4', "当前焊件没有复位")
        }

        if not self.exam_status.value and model_path in reset_steps:
            flag, step, message = reset_steps[model_path]
            if flag and step not in self.reset_imgs:
                logging.info(message)
                self.save_image_reset(self.reset_imgs, r, step)


        exam_steps = {
            self.model_paths[1]: [
            (self.exam_flag[11], 'welding_exam_12'),
            (self.exam_flag[3], 'welding_exam_4'),
            (self.exam_flag[10], 'welding_exam_11'),
            (self.exam_flag[6], 'welding_exam_7')
            ],
            self.model_paths[2]: [
            (self.exam_flag[0], 'welding_exam_1'),
            (self.exam_flag[13], 'welding_exam_14')
            ],
            self.model_paths[3]: [
            (self.exam_flag[1], 'welding_exam_2'),
            (self.exam_flag[12], 'welding_exam_13')
            ],
            self.model_paths[0]: [
            (self.exam_flag[4], 'welding_exam_5'),
            (self.exam_flag[8], 'welding_exam_9')
            ],
            self.model_paths[4]: [
            (self.exam_flag[7], 'welding_exam_8'),
            (self.exam_flag[2], 'welding_exam_3'),
            (self.exam_flag[9], 'welding_exam_10'),
            (self.exam_flag[5], 'welding_exam_6')
            ]
        }

        if self.exam_status.value and model_path in exam_steps:
            for flag, step in exam_steps[model_path]:
                if flag and step not in self.exam_imgs:
                    self.save_image_exam(self.exam_imgs, r, step, self.exam_order)

    def save_image_reset(welding_reset_imgs,r, step_name):#保存图片
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{IMAGES_DIR}/{step_name}_{save_time}.jpg"
        postpath = f"{IMG_URL_PATH}/{step_name}_{save_time}.jpg"
        annotated_frame = r.plot()
        cv2.imwrite(imgpath, annotated_frame)
        welding_reset_imgs[step_name]=postpath

    def save_image_exam(self,welding_exam_imgs,r, step_name,welding_exam_order):
        save_time = datetime.now().strftime('%Y%m%d_%H%M')
        imgpath = f"{IMAGES_DIR}/{step_name}_{save_time}.jpg"
        postpath = f"{IMG_URL_PATH}/{step_name}_{save_time}.jpg"
        annotated_frame = r.plot()
        cv2.imwrite(imgpath, annotated_frame)
        welding_exam_imgs[step_name]=postpath
        welding_exam_order.append(step_name)
        logger.info(f"{step_name}完成")

class YOLOInferenceManager:
    def __init__(self, model_paths: List[str], frame_queues: List[Queue]):
        self.model_paths = model_paths
        self.frame_queues = frame_queues
        self.processes: List[Process] = []
        self.start_events = [Event() for _ in range(6)]
        self.stop_events = [Event() for _ in range(6)]
        self.result_processor = DetectionResultProcessor()


    def start_inference(self):
        for i, (model_path, frame_queue) in enumerate(zip(self.model_paths, self.frame_queues)):
            process = Process(
                target=self._inference_worker,
                args=(model_path, frame_queue, 
                      self.start_events[i], self.stop_events[i])
            )
            process.start()
            self.processes.append(process)

        for event in self.start_events:
            event.wait()
    
    def stop_inference(self):
        for stop_event in self.stop_events:
            stop_event.set()
            
        for process in self.processes:
            try:
                process.join(timeout=3)
                if process.is_alive():
                    process.terminate()
                    # process.join(timeout=1)
                    # if process.is_alive():
                    #     process.kill()
            except Exception as e:
                logger.error(f"Failed to stop inference process {process.pid}: {e}")

        self.processes.clear()
        logger.info("All inference processes stopped")
    


    def _inference_worker(self, model_path: str, frame_queue: Queue,
                         start_event: Event, stop_event: Event):
        try:
            model = self._load_model(model_path)
            if not start_event.is_set():
                start_event.set()
                logger.info(f"{model_path} infer_yolo is running")
            #logger.info(f"Started inference with model: {model_path}")

            while not stop_event.is_set():
                if frame_queue.empty():
                    continue
                frame = frame_queue.get()

                self._run_inference(model, frame, model_path)

        except Exception as e:
            logger.error(f"Inference error for {model_path}: {e}")
        finally:
            logger.info(f"Inference stopped for {model_path}")



    def _load_model(self, model_path: str):
        try:
            model = YOLO(model_path)
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            raise

    def _run_inference(self, model, frame, model_path):
        try:
            results = model.predict(frame,verbose=False,device=1)

            self.result_processor.main_fun(results[0], model_path)
        except Exception as e:
            logger.error(f"Inference failed: {e}")
    


class DetectionState:
    def __init__(self):
        self.is_running = False
        self.stream_manager = None
        self.inference_manager = None

    def initialize_managers(self):
        if not self.stream_manager or not self.inference_manager:
            self.stream_manager = VideoStreamManager(RTSP_URLS)
            self.inference_manager = YOLOInferenceManager(MODEL_PATHS, self.stream_manager.frame_queues)

    def start(self):
        self.initialize_managers()
        self.stream_manager.start_streams()
        self.inference_manager.start_inference()
        self.is_running = True

    def stop(self):
        if self.stream_manager and self.inference_manager:
            #必须先停止视频流，再停止推理
            self.stream_manager.stop_streams()
            self.inference_manager.stop_inference()
            self.stream_manager = None
            self.inference_manager = None
        self.is_running = False
    
    def set_exam_status(self,status):
        self.inference_manager.result_processor.exam_status.value = status
    
    def get_exam_status(self):
        return self.inference_manager.result_processor.exam_status.value

    def get_rest_flag(self):
        return self.inference_manager.result_processor.reset_flag

    def get_rest_imgs(self):
        return self.inference_manager.result_processor.reset_imgs

    def get_exam_order(self):
        return self.inference_manager.result_processor.exam_order

    def get_exam_imgs(self):
        return self.inference_manager.result_processor.exam_imgs

    def reset_exam_variables(self):
        self.inference_manager.result_processor.init_exam_variables()
    def reset_reset_variables(self):
        self.inference_manager.result_processor.init_reset_variables()

# Initialize state manager
detection_state = DetectionState()

@app.get("/start_detection")
async def start_detection() -> Dict[str, str]:
    """Start welding detection service"""
    try:
        if detection_state.is_running:
            logger.info("Detection already running")
            return {"status": "ALREADY_RUNNING"}
        
        logger.info("Starting detection service")
        detection_state.start()
        return SUCCESS_RESPONSE
    except Exception as e:
        logger.error(f"Detection start failed: {e}")
        detection_state.stop()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_detection")
async def stop_detection() -> Dict[str, str]:
    """Stop welding detection service"""
    try:
        if not detection_state.is_running:
            logger.info("No detection running")
            return {"status": "NO_DETECTION_RUNNING"}
        
        logger.info("Stopping detection service")
        detection_state.stop()
        return SUCCESS_RESPONSE
    except Exception as e:
        logger.error(f"Detection stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reset_status")
async def reset_status():
    """Reset system status"""
    try:
        logger.info("Reset status")

        if not any(detection_state.get_rest_flag()):  # 表明不需要复位,如果 welding_reset_flag 列表中的所有元素都为 False，则 any(welding_reset_flag) 返回 False，not any(welding_reset_flag) 返回 True。
            logger.info('reset_all!')
            return {"status": "RESET_ALL"}
        else:
            logger.info('reset_all is false')
            json_array = [
                {"resetStep": re.search(r'reset_step_(\d+)', key).group(1), "image": value}
                for key, value in detection_state.get_rest_imgs().items()
            ]
            detection_state.reset_reset_variables()#初始化复位变量
            return {"status": "NOT_RESET_ALL", "data": json_array}
        #return SUCCESS_RESPONSE
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_exam")
async def start_exam() -> Dict[str, str]:
    """Start welding examination"""
    try:
        logger.info("Starting exam")
        if not detection_state.get_exam_status():  # 防止重复开启检测服务
            detection_state.set_exam_status(True)
            detection_state.reset_exam_variables()
            logging.info('start_exam')
            return SUCCESS_RESPONSE
        else:
            logging.info("start_exam is already running")
            return {"status": "ALREADY_RUNNING"}

    except Exception as e:
        logger.error(f"Exam start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exam_status")
async def exam_status():#TODO 返回的数据格式还没确定
    """Get examination status"""
    try:
        logger.info("Checking exam status")
        if not detection_state.get_exam_order():#使用not来判断列表是否为空
            logging.info('welding_exam_order is none')
            return {"status": "NONE"}
        else:
            json_array = [
                {"step": re.search(r'welding_exam_(\d+)', value).group(1), "image": detection_state.get_exam_imgs().get(value)}
                for value in detection_state.get_exam_order()
            ]
            return {"status": "SUCCESS", "data": json_array}
        #return SUCCESS_RESPONSE
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_exam")
async def stop_exam() -> Dict[str, str]:
    """Stop welding examination"""
    try:
        logger.info("Stopping exam")
        if detection_state.get_exam_status():
            detection_state.set_exam_status(False)
            #detection_state.reset_exam_variables()
            return SUCCESS_RESPONSE

    except Exception as e:
        logger.error(f"Exam stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=SERVER_IP,
        port=SERVER_PORT,
        log_level="info"
    )
