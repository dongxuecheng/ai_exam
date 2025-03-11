"""Core package for basket K2 detection service."""

from .config import BASKET_K2_CONFIG
from .logging import logger

__all__ = [
    "BASKET_K2_CONFIG",
    "logger"
]