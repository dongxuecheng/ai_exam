from pydantic import BaseModel, field_validator
from pathlib import Path
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

    @field_validator('images_dir')
    def validate_images_dir(cls, v):
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v
