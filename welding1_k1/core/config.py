from shared.utils.config import create_server_config
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "welding1_k1"
IMAGES_DIR = BASE_DIR / 'images'/ "welding1_k1"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 使用环境变量配置创建服务器配置
WELDING1_K1_CONFIG = create_server_config(
    service_prefix='WELDING1_K1',
    weights_keys=['POSE', 'WEARING'],
    stream_count=1
)