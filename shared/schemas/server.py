from pydantic import BaseModel, field_validator
from pathlib import Path
from typing import Union
from .stream import StreamConfig

class ServerConfig(BaseModel):
    """检测服务配置"""
    server_ip: str
    server_port: int
    weights_paths: list[str]
    images_dir: Path
    img_url_path: str
    static_mount_path: str
    stream_configs: list[StreamConfig]
    gpu_device: Union[int, str] = 0  # GPU device ID or 'cpu' for CPU mode

    @field_validator('images_dir')
    def validate_images_dir(cls, v):
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator('gpu_device')
    def validate_gpu_device(cls, v):
        if isinstance(v, str) and v != 'cpu':
            raise ValueError("GPU device must be an integer (device ID) or 'cpu'")
        if isinstance(v, int) and v < 0:
            raise ValueError("GPU device ID must be non-negative")
        return v
