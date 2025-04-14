"""Core package for Welding K1 detection service."""

from .config import WELDING_K1_CONFIG
from .logging import logger

__all__ = [
    "WELDING_K1_CONFIG",
    "logger"
]