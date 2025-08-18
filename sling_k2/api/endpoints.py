from ..services import DetectionManager
from ..core import config, logger
from shared.api.base_endpoints import create_detection_router

# 创建标准路由器，不包含reset功能
router = create_detection_router(
    service_class=DetectionManager,
    config=config,
    logger=logger,
    service_name="sling",
    include_reset=False,
    include_exam=True
)
