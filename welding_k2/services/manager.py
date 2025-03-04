from ..schemas import ServerConfig
from .streamer import VideoStreamer
from .predictor import YOLOPredictor
from .processor import ResultProcessor


class DetectionManager:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.is_running = False
        self.stream_manager = None
        self.inference_manager = None
        self.result_processor = None  

    def initialize_managers(self):
        if not self.stream_manager or not self.inference_manager:
            self.result_processor = ResultProcessor(
                self.config.weights_paths,
                self.config.images_dir,
                self.config.img_url_path)
            self.stream_manager = VideoStreamer(
                self.config.stream_configs,
                len(self.config.weights_paths)
            )
            self.inference_manager = YOLOPredictor(
                self.config.weights_paths,
                self.stream_manager.frame_queues,
                self.result_processor)

    def start(self):
        self.initialize_managers()
        #必须先启动推理，再启动视频流,防止出现队列变满
        self.inference_manager.start_inference()
        self.stream_manager.start_streams()
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
    def get_exam_score(self):
        return self.result_processor.exam_score

    def init_exam_variables(self):
        self.result_processor.init_exam_variables()
    def init_reset_variables(self):
        self.result_processor.init_reset_variables()
