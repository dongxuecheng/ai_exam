"""Core package for welding K2 detection service."""

from .config import config, logger, service_name

__all__ = [
    "config",
    "logger",
    "service_name"
]