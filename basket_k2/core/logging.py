import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    # Get uvicorn logger
    logger = logging.getLogger("uvicorn")
    
    # Create logs directory if it doesn't exist
    # 使用相对于项目根目录的路径
    base_dir = Path(__file__).parent.parent.parent  # 导航到项目根目录
    log_dir = base_dir / "logs" / "basket_k2"
    log_dir.mkdir(parents=True, exist_ok=True)  # 使用parents=True确保创建完整路径
    
    # Create timestamp for log filename
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    log_filename = f"basket_k2_{timestamp}.log"
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_dir / log_filename,
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Create logger instance
logger = setup_logging()