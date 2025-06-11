from multiprocessing import Queue, Event, Process
#from ultralytics import YOLO
import logging
from typing import Union, List
from .processor import BaseResultProcessor
from queue import Empty

from .onnx.classify import Classify
from .onnx.detect import Detect
from .onnx.segment import Segment
from .onnx.pose import Pose

# Use basic logging if specific logger not provided
logger = logging.getLogger("shared_services")


class BaseYOLOPredictor:
    def __init__(self, weights_paths: List[str], frame_queues: List[Queue], 
                 result_processor: BaseResultProcessor, custom_logger=None, gpu_device: Union[int, str] = 0):
        """
        Initialize YOLO predictor
        :param weights_paths: List of model weight paths
        :param frame_queues: List of frame queues for each model
        :param result_processor: Processor for model results
        :param custom_logger: Optional custom logger
        :param gpu_device: GPU device ID (int) or 'cpu' for CPU mode
        """
        self.weights_paths = weights_paths
        self.frame_queues = frame_queues
        self.result_processor = result_processor
        self.logger = custom_logger or logger
        self.gpu_device = gpu_device
        
        self.processes: List[Process] = []
        self.start_events = [Event() for _ in range(len(self.weights_paths))]
        self.stop_events = [Event() for _ in range(len(self.weights_paths))]

    def start_inference(self):
        for i, (weights_path, frame_queue) in enumerate(zip(self.weights_paths, self.frame_queues)):
            process = Process(
                target=self._inference_worker,
                args=(weights_path, frame_queue, 
                      self.start_events[i], self.stop_events[i], self.gpu_device)
            )
            process.start()
            self.processes.append(process)

        for event in self.start_events:
            event.wait()
    
    def stop_inference(self):
        for stop_event in self.stop_events:
            stop_event.set()
            
        for process in self.processes:
            try:
                process.join(timeout=1)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                    if process.is_alive():
                        self.logger.error(f"Model Force killing process {process.pid}")
                        process.kill()                    
            except Exception as e:
                self.logger.error(f"Failed to stop inference process {process.pid}: {e}")

        self.processes.clear()
        self.logger.info("All inference processes stopped")

    def _inference_worker(self, weights_path: str, frame_queue: Queue,
                         start_event: Event, stop_event: Event, gpu_device: Union[int, str]):
        try:
            model = self._load_model(weights_path, gpu_device)
            if not start_event.is_set():
                start_event.set()
                self.logger.info(f"{weights_path} inference is running on device {gpu_device}")

            while not stop_event.is_set():
                try:
                # if frame_queue.empty():
                #     continue
                    frame = frame_queue.get(timeout=1)

                    self._run_inference(model, frame, weights_path)
                except Empty:
                    continue
        except Exception as e:
            self.logger.error(f"Inference error for {weights_path}: {e}")
        finally:
            self.logger.info(f"Inference stopped for {weights_path}")

    def _load_model(self, weights_path: str, gpu_device: Union[int, str] = 0):
        try:
            # Load model without immediately setting device
            #model = YOLO(weights_path)
            if 'detect' in weights_path:
                onnx_model = Detect(weights_path, device=gpu_device, input_size=(1280,1280))
            elif 'classify' in weights_path:
                onnx_model = Classify(weights_path, device=gpu_device)
            elif 'segment' in weights_path:
                onnx_model = Segment(weights_path, device=gpu_device, input_size=(1280,1280))
            elif 'pose' in weights_path:
                onnx_model = Pose(weights_path, device=gpu_device, input_size=(1280,1280))
            else:
                raise ValueError(f"Unknown model type for path: {weights_path}")
            return onnx_model
        except Exception as e:
            self.logger.error(f"Failed to load model {weights_path}: {e}")
            raise

    def _run_inference(self, model, frame, weights_path):
        try:

            
            # Determine if this is a segmentation model and adjust parameters accordingly
            # Projects can override this method for custom inference logic
            # if 'yolo11l-seg' in weights_path.lower():
            #     results = model.predict(frame, verbose=False, conf=0.6, classes=[0], device=device)[0]
            #         # Additional parameters for segmentation models if needed
            # elif 'welding_wearing' in weights_path.lower():
            #     results = model.predict(frame, verbose=False, conf=0.6, classes=[0,3,10], device=device)[0]
            # else:
            #     results = model.predict(frame, verbose=False, conf=0.6, device=device)[0]

            results=model.predict(frame)
            self.result_processor.process_result(results, weights_path)
        except Exception as e:
            self.logger.error(f"Inference failed: {e}")
