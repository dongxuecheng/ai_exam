from shared.schemas import StreamConfig, ServerConfig
from pathlib import Path
import os

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "basket_k2"
IMAGES_DIR = BASE_DIR / 'images'/ "basket_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)


STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.237/cam/realmonitor?channel=1&subtype=0",
        target_models={0}  #检查悬挂机构，用pose或者seg
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.230/cam/realmonitor?channel=1&subtype=0",
        target_models={1}  #正面视角，检查警戒区
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.242/cam/realmonitor?channel=1&subtype=0",
        target_models={2,3,4}  # 顶部视角，用pose或者seg检查人，目标检测（警戒区，刷子，安全带）,seg来判断吊篮区域
    )
]

BASKET_K2_CONFIG= ServerConfig(
    server_ip='172.16.22.90',
    server_port=5005,
    weights_paths=[
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11x-pose1.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yz_oil_tank.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11x-pose2.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'basket_seg.pt'),       
        os.path.join(WEIGHTS_BASE_DIR, 'yz_grounding_wire.pt')
    ],
    images_dir=IMAGES_DIR,
    static_mount_path='/basket_k2',#url中的路径
    img_url_path=f'http://172.16.22.90:5005/basket_k2',
    stream_configs=STREAM_CONFIGS
)