from fastapi import APIRouter, HTTPException, Depends
from ..services import DetectionManager
from functools import lru_cache
from typing import Annotated
from ..core import BASKET_K2_CONFIG, logger
from shared.schemas import StatusResponse, ExamStatusResponse
import re

router = APIRouter()

@lru_cache()#单例模型
def get_service() -> DetectionManager:
    return DetectionManager(BASKET_K2_CONFIG)

#依赖注入
DetectionManagerDep=Annotated[DetectionManager,Depends(get_service)]



@router.get("/start_detection",response_model=StatusResponse)
async def start_detection(service: DetectionManagerDep) -> StatusResponse:
    """Start basket detection service"""
    try:
        if service.is_running:
            logger.info("Detection already running")
            return StatusResponse(status="ALREADY_RUNNING")
        
        logger.info("Starting detection service")
        service.start()
        return StatusResponse(status="SUCCESS")
    except Exception as e:
        logger.error(f"Detection start failed: {e}")
        service.stop()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop_detection",response_model=StatusResponse)
async def stop_detection(service: DetectionManagerDep) -> StatusResponse:
    """Stop basket detection service"""
    try:
        if not service.is_running:
            logger.info("No detection running")
            return StatusResponse(status="NO_DETECTION_RUNNING")
        
        logger.info("Stopping detection service")
        service.stop()
        return StatusResponse(status="SUCCESS")
    except Exception as e:
        logger.error(f"Detection stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/start_exam", response_model=StatusResponse)
async def start_exam(service: DetectionManagerDep) -> StatusResponse:
    """Start basket examination"""
    try:
        logger.info("Starting exam")
        if not service.get_exam_status():  # 防止重复开启检测服务
            service.set_exam_status(True)
            service.init_exam_variables()
            return StatusResponse(status="SUCCESS")
        else:
            logger.info("start_exam is already running")
            return StatusResponse(status="ALREADY_RUNNING")

    except Exception as e:
        logger.error(f"Exam start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exam_status",response_model=ExamStatusResponse)
async def exam_status(service: DetectionManagerDep) -> ExamStatusResponse:
    """Get examination status"""
    try:
        logger.info("Checking exam status")
        if not service.get_exam_order():#使用not来判断列表是否为空
            logger.info('basket_exam_order is none')
            return ExamStatusResponse(status="NONE")
        
        exam_steps = [
            {"step": re.search(r'basket_(\d+)', value).group(1), "image": service.get_exam_imgs().get(value)}
            for value in service.get_exam_order()
        ]
        return ExamStatusResponse(status="SUCCESS", data=exam_steps)
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop_exam",response_model=StatusResponse)
async def stop_exam(service: DetectionManagerDep) -> StatusResponse:
    """Stop basket examination"""
    try:
        logger.info("Stopping exam")
        if service.get_exam_status():
            service.set_exam_status(False)
            #service.reset_exam_variables()
            return StatusResponse(status="SUCCESS")
        
        logger.info("No exam running")
        return StatusResponse(status="NO_EXAM_RUNNING")

    except Exception as e:
        logger.error(f"Exam stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))