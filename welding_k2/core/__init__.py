"""Core package for welding K2 detection service."""

from .config import WELDING_K2_CONFIG
from .logging import logger

__all__ = [
    "WELDING_K2_CONFIG",
    "logger"
]