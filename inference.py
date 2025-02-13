from multiprocessing import Queue, Event, Process
from ultralytics import YOLO
import logging
from detection import DetectionResultProcessor

logger = logging.getLogger("uvicorn")

class YOLOInferenceManager:
    def __init__(self, weights_paths: list[str], frame_queues: list[Queue],result_processor: DetectionResultProcessor):
        self.weights_paths = weights_paths
        self.frame_queues = frame_queues
        self.processes: list[Process] = []
        self.start_events = [Event() for _ in range(len(self.weights_paths))]
        self.stop_events = [Event() for _ in range(len(self.weights_paths))]
        self.result_processor = result_processor


    def start_inference(self):
        for i, (weights_path, frame_queue) in enumerate(zip(self.weights_paths, self.frame_queues)):
            process = Process(
                target=self._inference_worker,
                args=(weights_path, frame_queue, 
                      self.start_events[i], self.stop_events[i])
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

            except Exception as e:
                logger.error(f"Failed to stop inference process {process.pid}: {e}")

        self.processes.clear()
        logger.info("All inference processes stopped")
    


    def _inference_worker(self, weights_path: str, frame_queue: Queue,
                         start_event: Event, stop_event: Event):
        try:
            model = self._load_model(weights_path)
            if not start_event.is_set():
                start_event.set()
                logger.info(f"{weights_path} infer_yolo is running")
            #logger.info(f"Started inference with model: {weights_path}")

            while not stop_event.is_set():
                if frame_queue.empty():
                    continue
                frame = frame_queue.get()

                self._run_inference(model, frame, weights_path)

        except Exception as e:
            logger.error(f"Inference error for {weights_path}: {e}")
        finally:
            logger.info(f"Inference stopped for {weights_path}")



    def _load_model(self, weights_path: str):
        try:
            model = YOLO(weights_path)
            return model
        except Exception as e:
            logger.error(f"Failed to load model {weights_path}: {e}")
            raise

    def _run_inference(self, model, frame, weights_path):
        try:
            results = model.predict(frame,verbose=False,device=1,conf=0.6)

            self.result_processor.main_fun(results[0], weights_path)
        except Exception as e:
            logger.error(f"Inference failed: {e}")