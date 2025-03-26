from shared.schemas import StreamConfig, ServerConfig
from pathlib import Path
import os

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "welding_k2"
IMAGES_DIR = BASE_DIR / 'images'/ "welding_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)


# STREAM_CONFIGS = [
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya123456@192.168.0.108/cam/realmonitor?channel=1&subtype=0",
#         target_models={0}  #油桶/扫把视角视频流 需要在顶部，目标检测（油桶，扫把）
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya123456@192.168.0.104/cam/realmonitor?channel=1&subtype=0",
#         target_models={1}  #垂直向下，检测焊机二次线的视角，分割（人体）来判断二次线的交集的大小
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya123456@192.168.0.107/cam/realmonitor?channel=1&subtype=0",
#         target_models={2}  # 拍摄开关灯视角，焊枪，搭铁线视频流（目标检测上述物体）
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya123456@192.168.0.2/cam/realmonitor?channel=1&subtype=0",
#         target_models={3,4}  # 焊台视角，搭铁线视频流，目标检测焊件，搭铁线，刷子，铁锤，图像分类焊接过程
#     ),
#     StreamConfig(
#         rtsp_url="rtsp://admin:ya123456@192.168.0.106/cam/realmonitor?channel=1&subtype=0",
#         target_models={5}  # 焊机开关视频流,目标检测（开关），分割（人体）来判断一次线
#     )
# ]

STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.230/cam/realmonitor?channel=1&subtype=0",
        target_models={0}  #油桶/扫把视角视频流 需要在顶部，目标检测（油桶，扫把）
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.231/cam/realmonitor?channel=1&subtype=0",
        target_models={1}  #垂直向下，检测焊机二次线的视角，分割（人体）来判断二次线的交集的大小
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.247/cam/realmonitor?channel=1&subtype=0",
        target_models={2}  # 拍摄开关灯视角，焊枪，搭铁线视频流（目标检测上述物体）
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.232/cam/realmonitor?channel=1&subtype=0",
        target_models={3,4}  # 焊台视角，搭铁线视频流，目标检测焊件，搭铁线，刷子，铁锤，图像分类焊接过程
    ),
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.238/cam/realmonitor?channel=1&subtype=0",
        target_models={5}  # 焊机开关视频流,目标检测（开关），分割（人体）来判断一次线
    )
]

WELDING_K2_CONFIG= ServerConfig(
    server_ip='172.16.22.55',
    server_port=5002,
    weights_paths=[
        os.path.join(WEIGHTS_BASE_DIR, 'yz_oil_tank.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11l-seg.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yz319_light_view.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yz_welding_station.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yz_welding_cls.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'yz_welding_switches.pt')
    ],
    images_dir=IMAGES_DIR,
    static_mount_path='/welding_k2',#url中的路径
    img_url_path=f'http://172.16.22.55:5002/welding_k2',
    stream_configs=STREAM_CONFIGS
)