from pydantic import BaseModel
from pathlib import Path

class StreamConfig(BaseModel):
    """流配置"""
    rtsp_url: str
    queue_size: int = 100
    frame_skip: int = 5
    target_models: set[int]

class DetectionSettings(BaseModel):
    """检测服务配置"""
    server_ip: str
    server_port: int
    weights_paths: list[str]
    images_dir: Path
    img_url_path: str
    stream_configs: list[StreamConfig]

