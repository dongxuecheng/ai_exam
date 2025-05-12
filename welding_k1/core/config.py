from shared.schemas import StreamConfig, ServerConfig
from pathlib import Path
import os

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "welding_k1"
IMAGES_DIR = BASE_DIR / 'images'/ "welding_k1"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

STREAM_CONFIGS = [
    StreamConfig(
        rtsp_url="rtsp://admin:yaoan1234@172.16.22.235/cam/realmonitor?channel=1&subtype=0",
        target_models={0,1}  #两个模型，一个检查人，一个检测穿戴
    )
]

WELDING_K1_CONFIG= ServerConfig(
    #TODO server_ip和port还没有被调用
    server_ip='127.0.0.1',
    server_port=5001,
    weights_paths=[
        os.path.join(WEIGHTS_BASE_DIR, 'yolo11n-pose.pt'),
        os.path.join(WEIGHTS_BASE_DIR, 'jidian/welding_wearing.pt')
    ],
    images_dir=IMAGES_DIR,
    static_mount_path='/welding_k1',#url中的路径
    img_url_path=f'http://127.0.0.1:5001/welding_k1',
    stream_configs=STREAM_CONFIGS
)