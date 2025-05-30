"""
统一的日志配置管理器
"""
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class LoggerManager:
    """统一的日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, service_name: str, project_root: Optional[Path] = None) -> logging.Logger:
        """
        获取或创建指定服务的logger
        
        Args:
            service_name: 服务名称
            project_root: 项目根目录，如果不提供则自动推断
            
        Returns:
            配置好的logger实例
        """
        if service_name in cls._loggers:
            return cls._loggers[service_name]
        
        logger = cls._create_logger(service_name, project_root)
        cls._loggers[service_name] = logger
        return logger
    
    @classmethod
    def _create_logger(cls, service_name: str, project_root: Optional[Path] = None) -> logging.Logger:
        """创建新的logger"""
        # 获取项目根目录
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        # 创建日志目录
        log_dir = project_root / "logs" / service_name
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建时间戳文件名
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        log_filename = f"{service_name}_{timestamp}.log"
        
        # 获取或创建logger
        logger = logging.getLogger(service_name)
        logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_dir / log_filename,
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 设置格式化器
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
