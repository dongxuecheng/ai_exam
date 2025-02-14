import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging():
    """Configure logging for the application"""
    # Get uvicorn logger
    logger = logging.getLogger("uvicorn")
    
    # Create logs directory if it doesn't exist
    log_dir = Path("/mnt/xcd/code/ai_exam/logs/welding_k2")
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamp for log filename
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    log_filename = f"welding_k2_{timestamp}.log"
    
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