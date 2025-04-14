from pydantic import BaseModel
from typing import Optional

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
    score: Optional[int] = None

class WearingResponse(BaseModel):
    """穿戴响应模型"""
    name: str
    number: int

class ResetStatusResponse(StatusResponse):
    """复位状态响应模型"""
    data: Optional[list[ResetStepResponse]] = None

class ExamStatusResponse(StatusResponse):
    """考试状态响应模型"""
    data: Optional[list[ExamStepResponse]] = None

class WearingStatusResponse(StatusResponse):
    """考试状态响应模型"""
    data: list[WearingResponse]
    image: str
