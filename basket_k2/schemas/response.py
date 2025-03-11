from pydantic import BaseModel
from typing import Optional

class StatusResponse(BaseModel):
    """基础状态响应模型"""
    status: str

class ExamStepResponse(BaseModel):
    """考试步骤响应模型"""
    step: str
    image: str

class ExamStatusResponse(StatusResponse):
    """考试状态响应模型"""
    data: Optional[list[ExamStepResponse]] = None
