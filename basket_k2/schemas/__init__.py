"""Schema definitions for basket K2 detection service."""

from .response import (
    StatusResponse,
    ExamStatusResponse
)
from .stream import StreamConfig
from .server import ServerConfig

__all__ = [
    "StatusResponse",
    "ExamStatusResponse",
    "StreamConfig",
    "ServerConfig"
]