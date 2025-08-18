import numpy as np
import cv2

def is_boxes_intersect(box1: tuple[int, int, int, int], 
                    box2: tuple[int, int, int, int]) -> bool:
    """
    判断两个矩形框是否相交
    
    参数:
        box1: 第一个矩形框，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
        box2: 第二个矩形框，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
        
    返回:
        bool: 如果两个矩形框相交则返回True，否则返回False
    """
    
    box1_x1, box1_y1, box1_x2, box1_y2 = box1
    box2_x1, box2_y1, box2_x2, box2_y2 = box2
    
    # 检查一个框是否在另一个框的左侧
    if box1_x2 < box2_x1 or box2_x2 < box1_x1:
        return False
        
    # 检查一个框是否在另一个框的上方
    if box1_y2 < box2_y1 or box2_y2 < box1_y1:
        return False
    
    return True


def is_point_in_polygon(point: tuple[int, int], polygon: list[tuple[int, int]]) -> bool:
    """
    判断一个点是否在多边形内部或边界上
    
    参数:
        point: 需要检测的点坐标，格式为(x, y)
        polygon: 多边形的顶点坐标列表，每个顶点格式为(x, y)
        
    返回:
        bool: 如果点在多边形内部或边界上则返回True，否则返回False
    """

    # 将点转换为float32类型
    point = np.float32(point)
    
    # 将多边形顶点转换为cv2.pointPolygonTest所需的格式
    contour = np.array(polygon, dtype=np.float32)
    
    # 重塑轮廓为所需格式 (n,1,2)
    contour = contour.reshape((-1, 1, 2))
    
    # 使用pointPolygonTest检查点是否在多边形内部
    # 返回值 > 0 表示点在内部
    # 返回值 = 0 表示点在边界上
    # 返回值 < 0 表示点在外部
    result = cv2.pointPolygonTest(contour, tuple(point), False)
    
    return result >= 0

def calculate_mask_rect_iou(mask: np.ndarray, rect: tuple[int, int, int, int]) -> float:
    """
    计算掩码与矩形区域的交并比(IoU)
    
    参数:
        mask: 掩码点的坐标数组，形状为(n,2)，每行是一个(x,y)点坐标
        rect: 矩形区域，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
        
    返回:
        float: IoU值，范围从0到1
    """
    if len(mask) == 0:
        return 0.0
    
    # 创建掩码的二值图像
    x1_rect, y1_rect, x2_rect, y2_rect = rect
    width = max(x2_rect, np.max(mask[:, 0]).astype(int)) + 1
    height = max(y2_rect, np.max(mask[:, 1]).astype(int)) + 1
    
    # 创建掩码图像
    mask_img = np.zeros((height, width), dtype=np.uint8)
    mask_points = np.array(mask, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask_img, [mask_points], 1)
    
    # 创建矩形图像
    rect_img = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(rect_img, (x1_rect, y1_rect), (x2_rect, y2_rect), 1, -1)
    
    # 计算交集和并集
    intersection = np.logical_and(mask_img, rect_img).sum()
    union = np.logical_or(mask_img, rect_img).sum()
    
    # 计算IoU
    if union == 0:
        return 0.0
    iou = intersection / union
    
    return iou

def calculate_rect_polygon_iou(rect: tuple[int, int, int, int], polygon: list[tuple[int, int]]) -> float:
    """
    计算矩形和多边形的交并比(IoU)
    
    参数:
        rect: 矩形区域，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
        polygon: 多边形的顶点坐标列表，每个顶点格式为(x, y)
        
    返回:
        float: IoU值，范围从0到1
    """
    if len(polygon) == 0:
        return 0.0
    
    # 提取矩形坐标
    x1_rect, y1_rect, x2_rect, y2_rect = rect
    
    # 确定画布大小
    polygon_array = np.array(polygon)
    width = max(x2_rect, np.max(polygon_array[:, 0]).astype(int)) + 1
    height = max(y2_rect, np.max(polygon_array[:, 1]).astype(int)) + 1
    
    # 创建矩形掩码
    rect_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(rect_mask, (x1_rect, y1_rect), (x2_rect, y2_rect), 1, -1)
    
    # 创建多边形掩码
    poly_mask = np.zeros((height, width), dtype=np.uint8)
    poly_points = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(poly_mask, [poly_points], 1)
    
    # 计算交集和并集
    intersection = np.logical_and(rect_mask, poly_mask).sum()
    union = np.logical_or(rect_mask, poly_mask).sum()
    
    # 计算IoU
    if union == 0:
        return 0.0
    
    return float(intersection) / union

def is_point_in_rect(point: tuple[int, int], rect: tuple[int, int, int, int]) -> bool:
    """
    判断一个点是否在矩形区域内部或边界上
    
    参数:
        point: 需要检测的点坐标，格式为(x, y)
        rect: 矩形区域，格式为(x1, y1, x2, y2)，表示左上角和右下角坐标
        
    返回:
        bool: 如果点在矩形内部或边界上则返回True，否则返回False
    """
    x, y = point
    x1, y1, x2, y2 = rect
    
    # 检查点的x坐标是否在矩形的x范围内
    # 检查点的y坐标是否在矩形的y范围内
    return (x1 <= x <= x2) and (y1 <= y <= y2)