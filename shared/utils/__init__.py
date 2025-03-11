"""
工具函数模块初始化文件
提供各种通用工具函数，包括几何计算、图像处理和验证函数
"""

from .geometry import (
    is_boxes_intersect,
    is_point_in_polygon,
    calculate_mask_rect_iou,
    is_point_in_rect,
    calculate_rect_polygon_iou
)

# 导出所有公共接口
__all__ = [
    # 几何函数
    'is_boxes_intersect',
    'is_point_in_polygon',
    'calculate_mask_rect_iou'
    'is_point_in_rect',
    'calculate_rect_polygon_iou'
]
