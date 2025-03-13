from shared.schemas import ServerConfig
from shared.services import BaseDetectionManager
from .processor import ResultProcessor
from ..core import logger


class DetectionManager(BaseDetectionManager):
    """焊接检测管理器，提供焊接考核特定功能"""
    
    def __init__(self, config: ServerConfig):
        """
        初始化焊接检测管理器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config, ResultProcessor, logger)

    # 焊接考核独有的方法
    def init_reset_variables(self):
        """初始化重置变量"""
        if self.result_processor and hasattr(self.result_processor, 'init_reset_variables'):
            self.result_processor.init_reset_variables()
            
    def get_exam_score(self):
        """获取考试得分"""
        if self.result_processor and hasattr(self.result_processor, 'exam_score'):
            return self.result_processor.exam_score
        return None

    def get_rest_flag(self):
        """获取重置标志"""
        if self.result_processor and hasattr(self.result_processor, 'reset_flag'):
            return self.result_processor.reset_flag
        return None

    def get_rest_imgs(self):
        """获取重置图像"""
        if self.result_processor and hasattr(self.result_processor, 'reset_imgs'):
            return self.result_processor.reset_imgs
        return None
