from fastapi import APIRouter, HTTPException, Depends
from ..services import DetectionManager
from functools import lru_cache
from typing import Annotated
from ..core import WELDING1_K2_CONFIG, logger
from shared.schemas import StatusResponse, ResetStatusResponse, ExamStatusResponse
import re


router = APIRouter()

@lru_cache()#单例模型
def get_service() -> DetectionManager:
    return DetectionManager(WELDING1_K2_CONFIG)

#依赖注入
DetectionManagerDep=Annotated[DetectionManager,Depends(get_service)]


@router.get("/start_detection",response_model=StatusResponse)
async def start_detection(service: DetectionManagerDep) -> StatusResponse:
    """Start welding detection service"""
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
    """Stop welding detection service"""
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

@router.get("/reset_status",response_model=ResetStatusResponse)
async def reset_status(service: DetectionManagerDep) -> ResetStatusResponse:
    """Reset system status"""
    try:
        logger.info("Reset status")
        #TODO ERROR:    Reset failed: 'NoneType' object is not iterable
        #TODO 这里需要加not
        reset_flags = service.get_reset_flag()  # 获取复位标志
        #logger.info(f"reset_flags: {reset_flags}")
        if not any(reset_flags):  # 表明不需要复位,如果 welding_reset_flag 列表中的所有元素都为 False，则 any(welding_reset_flag) 返回 False，not any(welding_reset_flag) 返回 True。
            logger.info('reset_all!')
            return ResetStatusResponse(status="RESET_ALL")
        
        logger.info('reset_all is false')
        reset_steps = [
            {"resetStep": re.search(r'reset_step_(\d+)', key).group(1), "image": value}
            for key, value in service.get_reset_imgs().items()
        ]
        #logger.info(reset_steps)
        service.init_reset_variables()#初始化复位变量
        return ResetStatusResponse(status="NOT_RESET_ALL", data=reset_steps)
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/start_exam", response_model=StatusResponse)
async def start_exam(service: DetectionManagerDep) -> StatusResponse:
    """Start welding examination"""
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
            logger.info('welding_exam_order is none')
            return ExamStatusResponse(status="NONE")
        
        exam_steps = [
            {"step": re.search(r'welding_exam_(\d+)', value).group(1), "image": service.get_exam_imgs().get(value),"score":service.get_exam_score().get(value)}
            for value in service.get_exam_order()
        ]
        return ExamStatusResponse(status="SUCCESS", data=exam_steps)
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stop_exam",response_model=StatusResponse)
async def stop_exam(service: DetectionManagerDep) -> StatusResponse:
    """Stop welding examination"""
    try:
        logger.info("Stopping exam")
        if service.get_exam_status():
            service.set_exam_status(False)
            service.init_reset_variables()
            return StatusResponse(status="SUCCESS")
        
        logger.info("No exam running")
        return StatusResponse(status="NO_EXAM_RUNNING")

    except Exception as e:
        logger.error(f"Exam stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))