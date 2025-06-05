#from typing import Optional, Type, Any
import logging
from ..schemas import ServerConfig
from .streamer import BaseVideoStreamer
from .predictor import BaseYOLOPredictor
from .processor import BaseResultProcessor

class BaseDetectionManager:
    """
    检测管理器基类，提供通用的检测服务管理功能
    """
    
    def __init__(self, 
                 config: ServerConfig, 
                 processor_class: BaseResultProcessor,
                 logger: logging.Logger = None):
        """
        初始化检测管理器
        
        Args:
            config: 服务器配置
            processor_class: 结果处理器类，必须是BaseResultProcessor的子类
            logger: 日志记录器，如不提供则创建默认logger
        """
        self.config = config
        self.is_running = False
        self.stream_manager = None
        self.inference_manager = None
        self.result_processor = None

        self.processor_class = processor_class
        self.logger = logger or logging.getLogger(__name__)
    
    def initialize_managers(self):
        """初始化所有管理器组件"""
        if not self.stream_manager or not self.inference_manager:
            # 创建结果处理器,利用传递过来的子类ResultProcessor实现多态
            self.result_processor = self.processor_class(            
            self.config.weights_paths,
            self.config.images_dir,
            self.config.img_url_path
            )
            
            # 创建视频流管理器
            self.stream_manager = BaseVideoStreamer(
                self.config.stream_configs,
                len(self.config.weights_paths),
                custom_logger=self.logger
            )
            
            # 创建推理管理器
            self.inference_manager = BaseYOLOPredictor(
                self.config.weights_paths,
                self.stream_manager.frame_queues,
                self.result_processor,
                custom_logger=self.logger,
                gpu_device=self.config.gpu_device
            )
    

    def start(self):
        """启动检测服务"""
        self.initialize_managers()
        # 必须先启动推理，再启动视频流，防止出现队列变满
        self.inference_manager.start_inference()
        self.stream_manager.start_streams()
        self.is_running = True
        self.logger.info("Detection service started")

    def stop(self):
        """停止检测服务"""
        if self.stream_manager and self.inference_manager:
            # 必须先停止视频流，再停止推理
            self.stream_manager.stop_streams()
            self.inference_manager.stop_inference()
            self.stream_manager = None
            self.inference_manager = None
            self.result_processor = None 
        self.is_running = False
        self.logger.info("Detection service stopped")
    
    def set_exam_status(self, status):
        """设置考试状态"""
        if self.result_processor and hasattr(self.result_processor, 'exam_status'):
            self.result_processor.exam_status.value = status
    
    def get_exam_status(self):
        """获取考试状态"""
        if self.result_processor and hasattr(self.result_processor, 'exam_status'):
            return self.result_processor.exam_status.value
        return None
    
    def get_exam_order(self):
        """获取考试顺序"""
        if self.result_processor and hasattr(self.result_processor, 'exam_order'):
            return self.result_processor.exam_order
        return None

    def get_exam_imgs(self):
        """获取考试图像"""
        if self.result_processor and hasattr(self.result_processor, 'exam_imgs'):
            return self.result_processor.exam_imgs
        return None

    def init_exam_variables(self):
        """初始化考试变量"""
        if self.result_processor and hasattr(self.result_processor, 'init_exam_variables'):
            self.result_processor.init_exam_variables()
