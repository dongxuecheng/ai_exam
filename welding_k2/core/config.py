from shared.utils.config import create_server_config
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights'/ "welding_k2"
IMAGES_DIR = BASE_DIR / 'images'/ "welding_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)

# 使用环境变量配置创建服务器配置
WELDING_K2_CONFIG = create_server_config(
    service_prefix='WELDING_K2',
    weights_keys=['OIL_TANK', 'SEG', 'LIGHT_VIEW', 'DESK', 'CLS', 'SWITCH'],
    stream_count=5
)