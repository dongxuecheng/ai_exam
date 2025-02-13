from config import DetectionSettings
from video import VideoStreamManager
from inference import YOLOInferenceManager
from detection import DetectionResultProcessor


class DetectionService:
    def __init__(self, settings: DetectionSettings):
        self.settings = settings
        self.is_running = False
        self.stream_manager = None
        self.inference_manager = None
        self.result_processor = None  

    def initialize_managers(self):
        if not self.stream_manager or not self.inference_manager:
            self.result_processor = DetectionResultProcessor(
                self.settings.weights_paths,
                self.settings.images_dir,
                self.settings.img_url_path)
            self.stream_manager = VideoStreamManager(
                self.settings.stream_configs,
                len(self.settings.weights_paths)
            )
            self.inference_manager = YOLOInferenceManager(
                self.settings.weights_paths,
                self.stream_manager.frame_queues,
                self.result_processor)

    def start(self):
        self.initialize_managers()
        self.stream_manager.start_streams()
        self.inference_manager.start_inference()
        self.init_exam_variables()#每次开始检测时，初始化检测变量
        self.is_running = True

    def stop(self):
        if self.stream_manager and self.inference_manager:
            #必须先停止视频流，再停止推理
            self.stream_manager.stop_streams()
            self.inference_manager.stop_inference()
            self.stream_manager = None
            self.inference_manager = None
            self.result_processor = None 
        self.is_running = False
    
    def set_exam_status(self,status):
        self.result_processor.exam_status.value = status
    
    def get_exam_status(self):
        return self.result_processor.exam_status.value

    def get_rest_flag(self):
        return self.result_processor.reset_flag

    def get_rest_imgs(self):
        return self.result_processor.reset_imgs

    def get_exam_order(self):
        return self.result_processor.exam_order

    def get_exam_imgs(self):
        return self.result_processor.exam_imgs

    def init_exam_variables(self):
        self.result_processor.init_exam_variables()
    def init_reset_variables(self):
        self.result_processor.init_reset_variables()
