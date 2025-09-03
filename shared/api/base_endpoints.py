"""
通用API端点模板，减少重复代码
"""
from fastapi import APIRouter, HTTPException, Depends
from functools import lru_cache
from typing import Any
from shared.schemas import StatusResponse, ResetStatusResponse, ExamStatusResponse, WearingStatusResponse
import re
import time


def create_detection_router(
    service_class,
    config: Any,
    logger: Any,
    service_name: str = "detection",
    include_reset: bool = True,
    include_exam: bool = True,
    include_wearing: bool = False
) -> APIRouter:
    """
    创建标准的检测服务路由器
    
    Args:
        service_class: 服务管理器类
        config: 服务配置对象
        logger: 日志记录器
        service_name: 服务名称（用于日志）
        include_reset: 是否包含reset相关端点
        include_exam: 是否包含exam相关端点
        include_wearing: 是否包含wearing相关端点
    """
    router = APIRouter()
    
    @lru_cache()  # 单例模式
    def get_service():
        return service_class(config)
    
    @router.get("/start_detection", response_model=StatusResponse)
    async def start_detection(service=Depends(get_service)) -> StatusResponse:
        """Start detection service"""
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

    @router.get("/stop_detection", response_model=StatusResponse)
    async def stop_detection(service=Depends(get_service)) -> StatusResponse:
        """Stop detection service"""
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

    if include_reset:
        @router.get("/reset_status", response_model=ResetStatusResponse)
        async def reset_status(service=Depends(get_service)) -> ResetStatusResponse:
            """Reset system status"""
            try:
                logger.info("Reset status")
                reset_flags = service.get_reset_flag()  # 获取复位标志
                if not any(reset_flags):  # 表明不需要复位
                    logger.info('reset_all!')
                    return ResetStatusResponse(status="RESET_ALL")
                
                logger.info('reset_all is false')
                reset_steps = [
                    {"resetStep": re.search(r'reset_step_(\d+)', key).group(1), "image": value}
                    for key, value in service.get_reset_imgs().items()
                ]
                service.init_reset_variables()  # 初始化复位变量
                return ResetStatusResponse(status="NOT_RESET_ALL", data=reset_steps)
            except Exception as e:
                logger.error(f"Reset failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    if include_exam:
        @router.get("/start_exam", response_model=StatusResponse)
        async def start_exam(service=Depends(get_service)) -> StatusResponse:
            """Start examination"""
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

        @router.get("/stop_exam", response_model=StatusResponse)
        async def stop_exam(service=Depends(get_service)) -> StatusResponse:
            """Stop examination"""
            try:
                logger.info("Stopping exam")
                if service.get_exam_status():
                    service.set_exam_status(False)
                    # 对于焊接服务，停止考试时需要初始化复位变量
                    if hasattr(service, 'init_reset_variables') and 'welding' in service_name:
                        service.init_reset_variables()
                    return StatusResponse(status="SUCCESS")
                
                logger.info("No exam running")
                return StatusResponse(status="NO_EXAM_RUNNING")
            except Exception as e:
                logger.error(f"Exam stop failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/exam_status", response_model=ExamStatusResponse)
        async def get_exam_status(service=Depends(get_service)) -> ExamStatusResponse:
            """Get examination status"""
            try:
                logger.info("Checking exam status")
                exam_order = service.get_exam_order()
                if not exam_order:  # 使用not来判断列表是否为空
                    logger.info('exam_order is none')
                    return ExamStatusResponse(status="NONE")
                
                # 检查是否是 basket 还是 welding 类型
                if any('basket' in value for value in exam_order):
                    # basket 类型 - 只包含 step 和 image 字段
                    exam_steps = []
                    for value in exam_order:
                        match = re.search(r'basket_step_(\d+)', value)
                        if match:
                            exam_steps.append({
                                "step": match.group(1), 
                                "image": service.get_exam_imgs().get(value)
                            })
                        else:
                            logger.warning(f"Failed to parse basket step from: {value}")
                else:
                    # welding 类型 - 包含 step, image 和 score 字段
                    exam_steps = []
                    for value in exam_order:
                        match = re.search(r'welding_exam_(\d+)', value)
                        if match:
                            exam_steps.append({
                                "step": match.group(1), 
                                "image": service.get_exam_imgs().get(value),
                                "score": service.get_exam_score().get(value)
                            })
                        else:
                            logger.warning(f"Failed to parse welding step from: {value}")
                
                return ExamStatusResponse(status="SUCCESS", data=exam_steps)
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    if include_wearing:
        @router.get("/wearing_detection", response_model=StatusResponse)
        async def wearing_detection(service=Depends(get_service)) -> StatusResponse:
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

        @router.get("/end_wearing_exam", response_model=StatusResponse)
        async def end_wearing_exam(service=Depends(get_service)) -> StatusResponse:
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
        async def human_postion_status(service=Depends(get_service)) -> StatusResponse:
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

        @router.get("/wearing_status", response_model=WearingStatusResponse)
        async def wearing_status(service=Depends(get_service)) -> WearingStatusResponse:
            """Get examination status"""
            try:
                service.set_save_img_flag(True)
                time.sleep(1)  # TODO 寻找更好方法实现
                
                wearing_items = service.get_wearing_items()
                image = service.get_wearing_img()
                if wearing_items is None or image is None:
                    logger.info("No wearing items or image found")
                    return StatusResponse(status="NONE")
                
                json_array = []
                for key, value in wearing_items.items():
                    json_array.append({"name": key, "number": value})

                service.init_variables()
                return WearingStatusResponse(status="SUCCESS", data=json_array, image=image['welding_wearing'])
                
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    return router


def create_base_router(service_class, config: Any, logger: Any, **kwargs) -> APIRouter:
    """
    创建基础路由器的便捷函数
    这是 create_detection_router 的别名，保持向后兼容
    """
    return create_detection_router(service_class, config, logger, **kwargs)