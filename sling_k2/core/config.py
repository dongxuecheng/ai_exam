from shared.utils.yaml_config import get_service_config
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
WEIGHTS_BASE_DIR = BASE_DIR / 'weights' / "sling_k2"
IMAGES_DIR = BASE_DIR / 'images' / "sling_k2"

# 确保必要的目录存在
WEIGHTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 使用YAML配置创建服务器配置
SLING_K2_CONFIG = get_service_config('sling_k2')