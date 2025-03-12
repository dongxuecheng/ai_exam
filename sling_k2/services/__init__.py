"""Service implementations for sling K2 detection service."""

from .manager import DetectionManager
from .processor import ResultProcessor

__all__ = [
    "DetectionManager",
    "ResultProcessor"
]