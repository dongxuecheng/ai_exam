"""Core package for sling K2 detection service."""

from .config import SLING_K2_CONFIG
from .logging import logger

__all__ = [
    "SLING_K2_CONFIG",
    "logger"
]