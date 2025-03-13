from shared.schemas import ServerConfig
from shared.services import BaseDetectionManager
from .processor import ResultProcessor
from ..core import logger


class DetectionManager(BaseDetectionManager):
    """吊具检测管理器，提供吊具考核特定功能"""
    
    def __init__(self, config: ServerConfig):
        """
        初始化吊具检测管理器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config, ResultProcessor, logger)

