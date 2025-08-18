from shared.api.base_endpoints import create_detection_router
from ..services import DetectionManager
from ..core import config, logger

# 创建标准的检测路由器，包含exam功能但不包含reset功能
router = create_detection_router(
    service_class=DetectionManager,
    config=config,
    logger=logger,
    service_name="basket",
    include_reset=False,
    include_exam=True,
    include_wearing=False
)