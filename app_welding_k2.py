from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import logging
from pathlib import Path
import re
from config import StreamConfig, DetectionSettings
from detection_service import DetectionService

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
    img_url_path=f'http://172.16.20.163:5002/images/welding_k2',
    stream_configs=STREAM_CONFIGS
)

# FastAPI app
app = FastAPI(
    title="Welding K2 API",
    description="API for welding examination control system",
    version="1.0.0"
)

# Static files
app.mount("/images/welding_k2", StaticFiles(directory=SETTINGS.images_dir))

detection_service = DetectionService(SETTINGS)

@app.get("/start_detection")
async def start_detection() -> dict[str, str]:
    """Start welding detection service"""
    try:
        if detection_service.is_running:
            logger.info("Detection already running")
            return {"status": "ALREADY_RUNNING"}
        
        logger.info("Starting detection service")
        detection_service.start()
        return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Detection start failed: {e}")
        detection_service.stop()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_detection")
async def stop_detection() -> dict[str, str]:
    """Stop welding detection service"""
    try:
        if not detection_service.is_running:
            logger.info("No detection running")
            return {"status": "NO_DETECTION_RUNNING"}
        
        logger.info("Stopping detection service")
        detection_service.stop()
        return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Detection stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reset_status")
async def reset_status():
    """Reset system status"""
    try:
        logger.info("Reset status")

        if not any(detection_service.get_rest_flag()):  # 表明不需要复位,如果 welding_reset_flag 列表中的所有元素都为 False，则 any(welding_reset_flag) 返回 False，not any(welding_reset_flag) 返回 True。
            logger.info('reset_all!')
            return {"status": "RESET_ALL"}
        else:
            logger.info('reset_all is false')
            json_array = [
                {"resetStep": re.search(r'reset_step_(\d+)', key).group(1), "image": value}
                for key, value in detection_service.get_rest_imgs().items()
            ]
            detection_service.init_reset_variables()#初始化复位变量
            return {"status": "NOT_RESET_ALL", "data": json_array}
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/start_exam")
async def start_exam() -> dict[str, str]:
    """Start welding examination"""
    try:
        logger.info("Starting exam")
        if not detection_service.get_exam_status():  # 防止重复开启检测服务
            detection_service.set_exam_status(True)
            detection_service.init_exam_variables()
            logging.info('start_exam')
            return {"status": "SUCCESS"}
        else:
            logging.info("start_exam is already running")
            return {"status": "ALREADY_RUNNING"}

    except Exception as e:
        logger.error(f"Exam start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exam_status")
async def exam_status():#TODO 返回的数据格式还没确定
    """Get examination status"""
    try:
        logger.info("Checking exam status")
        if not detection_service.get_exam_order():#使用not来判断列表是否为空
            logging.info('welding_exam_order is none')
            return {"status": "NONE"}
        else:
            json_array = [
                {"step": re.search(r'welding_exam_(\d+)', value).group(1), "image": detection_service.get_exam_imgs().get(value)}
                for value in detection_service.get_exam_order()
            ]
            return {"status": "SUCCESS", "data": json_array}
        #return {"status": "SUCCESS"}
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stop_exam")
async def stop_exam() -> dict[str, str]:
    """Stop welding examination"""
    try:
        logger.info("Stopping exam")
        if detection_service.get_exam_status():
            detection_service.set_exam_status(False)
            #detection_service.reset_exam_variables()
            return {"status": "SUCCESS"}
        else:
            logger.info("No exam running")
            return {"status": "NO_EXAM_RUNNING"}

    except Exception as e:
        logger.error(f"Exam stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=SETTINGS.server_ip,
        port=SETTINGS.server_port,
        log_level="info"
    )
