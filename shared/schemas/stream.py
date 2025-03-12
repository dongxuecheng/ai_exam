from pydantic import BaseModel

class StreamConfig(BaseModel):
    """流配置"""
    rtsp_url: str
    queue_size: int = 100
    frame_skip: int = 5
    target_models: set[int]
