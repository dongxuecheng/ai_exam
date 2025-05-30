from fastapi import APIRouter, HTTPException, Depends
from ..services import DetectionManager
from functools import lru_cache
from typing import Annotated
from ..core import WELDING1_K1_CONFIG,logger
from shared.schemas import StatusResponse,WearingStatusResponse
import time

router = APIRouter()

@lru_cache()#单例模型
def get_service() -> DetectionManager:
    return DetectionManager(WELDING1_K1_CONFIG)

#依赖注入
DetectionManagerDep=Annotated[DetectionManager,Depends(get_service)]



@router.get("/wearing_detection",response_model=StatusResponse)
async def wearing_detection(service: DetectionManagerDep) -> StatusResponse:
    """Start wearing detection service"""
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

@router.get("/end_wearing_exam",response_model=StatusResponse)
async def end_wearing_exam(service: DetectionManagerDep) -> StatusResponse:
    """Stop wearing detection service"""
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



@router.get("/human_postion_status", response_model=StatusResponse)
async def human_postion_status(service: DetectionManagerDep) -> StatusResponse:
    """Get human_postion_status"""
    try:
        if service.get_human_postion():
            logger.info("IN_POSTION")
            return StatusResponse(status="IN_POSTION")
        else:
            logger.info("NOT_IN_POSTION")
            return StatusResponse(status="NOT_IN_POSTION")
        
    except Exception as e:
        logger.error(f"Get human_postion_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/wearing_status",response_model=WearingStatusResponse)
async def wearing_status(service: DetectionManagerDep) -> WearingStatusResponse:
    """Get examination status"""
    try:
        service.set_save_img_flag(True)
        time.sleep(1)#TODO 寻找更好方法实现
        
        wearing_items=service.get_wearing_items()
        image=service.get_wearing_img()
        if wearing_items is None or image is None:
            logger.info("No wearing items or image found")
            return StatusResponse(status="NONE")
        

        json_array=[]
        for key, value in wearing_items.items():
            json_array.append({"name":key,"number":value})

        service.init_variables()
        return WearingStatusResponse(status="SUCCESS", data=json_array, image=image['welding_wearing'])
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

