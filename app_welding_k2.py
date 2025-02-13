from fastapi import FastAPI, HTTPException,Depends
from functools import lru_cache
from typing import Annotated
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
import re
from schemas import StreamConfig, DetectionSettings, StatusResponse,  ResetStatusResponse, ExamStatusResponse
from service import DetectionService

# Logger setup
logger = logging.getLogger("uvicorn")

STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.230/cam/realmonitor?channel=1&subtype=0",
        target_models={0}  #油桶/扫把视角视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.231/cam/realmonitor?channel=1&subtype=0",
        target_models={1,2}  # 焊台视角，搭铁线视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.247/cam/realmonitor?channel=1&subtype=0",
        target_models={3, 4}  # 开关灯视角，焊机，焊枪，搭铁线视频流
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.232/cam/realmonitor?channel=1&subtype=0",
        target_models={5}  # 焊机开关视频流
    )
]

SETTINGS= DetectionSettings(
    server_ip='172.16.20.163',
    server_port=5002,
    weights_paths=['./weights/welding_k2/yz_oil_tank.pt',
                 './weights/welding_k2/yz_grounding_wire.pt',
                 './weights/welding_k2/welding_desk_cls_1121.pt',
                 './weights/welding_k2/yz_switching_light_view.pt',
                 './weights/welding_k2/yolo11x-pose.pt',
                 './weights/welding_k2/yz_welding_switches.pt'],
    images_dir=Path("./images/welding_k2"),
    static_mount_path='/welding_k2',
    img_url_path=f'http://172.16.20.163:5002/welding_k2',
    stream_configs=STREAM_CONFIGS
)

# FastAPI app
app = FastAPI(
    title="Welding K2 API",
    description="API for welding examination control system",
    version="1.0.0"
)

# Static files
app.mount(SETTINGS.static_mount_path, StaticFiles(directory=SETTINGS.images_dir))


@lru_cache()#单例模型
def get_service() -> DetectionService:
    return DetectionService(SETTINGS)

#依赖注入
DetectionServiceDep=Annotated[DetectionService,Depends(get_service)]



@app.get("/start_detection",response_model=StatusResponse)
async def start_detection(service: DetectionServiceDep) -> StatusResponse:
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

@app.get("/stop_detection",response_model=StatusResponse)
async def stop_detection(service: DetectionServiceDep) -> StatusResponse:
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

@app.get("/reset_status",response_model=ResetStatusResponse)
async def reset_status(service: DetectionServiceDep) -> ResetStatusResponse:
    """Reset system status"""
    try:
        logger.info("Reset status")

        if not any(service.get_rest_flag()):  # 表明不需要复位,如果 welding_reset_flag 列表中的所有元素都为 False，则 any(welding_reset_flag) 返回 False，not any(welding_reset_flag) 返回 True。
            logger.info('reset_all!')
            return ResetStatusResponse(status="RESET_ALL")
        
        logger.info('reset_all is false')
        reset_steps = [
            {"resetStep": re.search(r'reset_step_(\d+)', key).group(1), "image": value}
            for key, value in service.get_rest_imgs().items()
        ]
        service.init_reset_variables()#初始化复位变量
        return ResetStatusResponse(status="NOT_RESET_ALL", data=reset_steps)
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_exam", response_model=StatusResponse)
async def start_exam(service: DetectionServiceDep) -> StatusResponse:
    """Start welding examination"""
    try:
        logger.info("Starting exam")
        if not service.get_exam_status():  # 防止重复开启检测服务
            service.set_exam_status(True)
            service.init_exam_variables()
            logging.info('start_exam')
            return StatusResponse(status="SUCCESS")
        else:
            logging.info("start_exam is already running")
            return StatusResponse(status="ALREADY_RUNNING")

    except Exception as e:
        logger.error(f"Exam start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exam_status",response_model=ExamStatusResponse)
async def exam_status(service: DetectionServiceDep) -> ExamStatusResponse:
    """Get examination status"""
    try:
        logger.info("Checking exam status")
        if not service.get_exam_order():#使用not来判断列表是否为空
            logging.info('welding_exam_order is none')
            return ExamStatusResponse(status="NONE")
        
        exam_steps = [
            {"step": re.search(r'welding_exam_(\d+)', value).group(1), "image": service.get_exam_imgs().get(value)}
            for value in service.get_exam_order()
        ]
        return ExamStatusResponse(status="SUCCESS", data=exam_steps)
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_exam",response_model=StatusResponse)
async def stop_exam(service: DetectionServiceDep) -> StatusResponse:
    """Stop welding examination"""
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

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app, 
#         host=SETTINGS.server_ip,
#         port=SETTINGS.server_port,
#         log_level="info"
#     )
