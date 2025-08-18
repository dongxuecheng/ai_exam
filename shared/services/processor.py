from abc import ABC, abstractmethod
from pathlib import Path

class BaseResultProcessor(ABC):
    """
    结果处理器基类，所有具体处理器应继承此类
    """
    def __init__(self, weights_paths: list[str], 
                 images_dir: Path, 
                 img_url_path: str):
        """
        初始化结果处理器
        
        Args:
            weights_paths: 模型权重文件路径列表
            images_dir: 图像保存目录
            img_url_path: 图像URL路径前缀
        """
        self.weights_paths = weights_paths
        self.images_dir = images_dir
        self.img_url_path = img_url_path
        
    @abstractmethod    
    def process_result(self, result, weights_path):
        """
        处理模型结果
        
        Args:
            result: 模型推理结果
            weights_path: 使用的模型权重路径
            
        Returns:
            处理后的结果
        """
        raise NotImplementedError("Subclasses must implement process_result method")