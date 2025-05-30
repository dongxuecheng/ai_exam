"""Core package for Welding1 K1 detection service."""

from .config import WELDING1_K1_CONFIG
from .logging import logger

__all__ = [
    "WELDING1_K1_CONFIG",
    "logger",
]