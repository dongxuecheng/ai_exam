from shared.schemas import ServerConfig
from shared.services import BaseDetectionManager
from .processor import ResultProcessor
from ..core import logger


class DetectionManager(BaseDetectionManager):
    """焊接穿戴检测管理器，提供穿戴考核特定功能"""
    
    def __init__(self, config: ServerConfig):
        """
        初始化吊具检测管理器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config, ResultProcessor, logger)

    #焊接穿戴考核独有的方法
    def init_variables(self):
        """初始化重置变量"""
        if self.result_processor and hasattr(self.result_processor, 'init_variables'):
            self.result_processor.init_variables()
            
    def get_human_postion(self):
        """获取考试得分"""
        if self.result_processor and hasattr(self.result_processor, 'human_postion'):
            return self.result_processor.human_postion.value
        return None
    
    def set_save_img_flag(self, flag):
        """设置保存图片标志"""
        if self.result_processor and hasattr(self.result_processor, 'save_img_flag'):
            self.result_processor.save_img_flag.value = flag

    def get_wearing_items(self):
        """获取穿戴物品"""
        if self.result_processor and hasattr(self.result_processor, 'wearing_items'):
            return self.result_processor.wearing_items
        return None
    def get_wearing_img(self):
        """获取穿戴图片"""
        if self.result_processor and hasattr(self.result_processor, 'img_rul'):
            return self.result_processor.img_rul
        return None


