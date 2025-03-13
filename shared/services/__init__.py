"""共享服务模块"""

from .streamer import BaseVideoStreamer
from .predictor import BaseYOLOPredictor
from .processor import BaseResultProcessor
from .manager import BaseDetectionManager

__all__ = [
    "BaseVideoStreamer",
    "BaseYOLOPredictor",
    "BaseResultProcessor",
    "BaseDetectionManager"
]
