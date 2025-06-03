from shared.api.base_endpoints import create_detection_router
from ..services import DetectionManager
from ..core import config, logger

# 创建标准的检测路由器，包含reset和exam功能
router = create_detection_router(
    service_class=DetectionManager,
    config=config,
    logger=logger,
    service_name="welding3",
    include_reset=True,
    include_exam=True,
    include_wearing=False
)
