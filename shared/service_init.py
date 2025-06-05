"""
统一的服务初始化模块，简化各服务的配置和日志设置
"""
from pathlib import Path
from shared.utils.config import get_service_config
from shared.logging_manager import get_logger
from shared.schemas import ServerConfig


class ServiceInitializer:
    """服务初始化器，统一管理配置和日志"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._config = None
        self._logger = None
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        # 获取项目根目录
        base_dir = Path(__file__).parent.parent.parent
        
        # 创建weights和images目录
        weights_dir = base_dir / 'weights' / self.service_name
        images_dir = base_dir / 'images' / self.service_name
        
        weights_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def config(self) -> ServerConfig:
        """获取服务配置"""
        if self._config is None:
            self._config = get_service_config(self.service_name)
        return self._config
    
    @property
    def logger(self):
        """获取服务日志器"""
        if self._logger is None:
            self._logger = get_logger(self.service_name)
        return self._logger


# 便捷函数
def init_service(service_name: str):
    """初始化服务的便捷函数"""
    return ServiceInitializer(service_name)
