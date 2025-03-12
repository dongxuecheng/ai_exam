class BaseResultProcessor:
    """Base class for result processors"""
    def process_result(self, result, weights_path):
        """Process a model result - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_result method")