from pydantic import BaseModel, field_validator
from pathlib import Path
from typing import Optional

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
    static_mount_path: str
    stream_configs: list[StreamConfig]

    @field_validator('images_dir')
    def validate_images_dir(cls, v):
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

class StatusResponse(BaseModel):
    """基础状态响应模型"""
    status: str

class ResetStepResponse(BaseModel):
    """复位步骤响应模型"""
    resetStep: str
    image: str

class ExamStepResponse(BaseModel):
    """考试步骤响应模型"""
    step: str
    image: str

class ResetStatusResponse(StatusResponse):
    """复位状态响应模型"""
    data: Optional[list[ResetStepResponse]] = None

class ExamStatusResponse(StatusResponse):
    """考试状态响应模型"""
    data: Optional[list[ExamStepResponse]] = None
