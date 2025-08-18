from shared.api.base_endpoints import create_detection_router
from ..services import DetectionManager
from ..core import config, logger

# 创建穿戴检测路由器，包含特殊的穿戴检测端点
router = create_detection_router(
    service_class=DetectionManager,
    config=config,
    logger=logger,
    service_name="welding_wearing",
    include_reset=False,
    include_exam=False,
    include_wearing=True
)
