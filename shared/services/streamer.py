from multiprocessing import Queue, Event, Process
import cv2
from contextlib import contextmanager
import logging

# Use basic logging if specific logger not provided
logger = logging.getLogger("shared_services")

class BaseVideoStreamer:
    def __init__(self, stream_configs: list, num_models: int, custom_logger=None):
        """
        Initialize video stream manager
        :param stream_configs: Configuration for each video stream
        :param num_models: Total number of models
        :param custom_logger: Optional custom logger
        """
        self.stream_configs = stream_configs
        self.num_models = num_models
        self.logger = custom_logger or logger
        
        # Create frame queues for each model
        self.frame_queues = [
            Queue(maxsize=100) for _ in range(self.num_models)
        ]
        
        # Process and event management
        self.processes: list[Process] = []
        self.start_events = [Event() for _ in range(len(stream_configs))]
        self.stop_events = [Event() for _ in range(len(stream_configs))]

    def start_streams(self):
        for i, config in enumerate(self.stream_configs):
            process = Process(
                target=self._fetch_video_stream,
                args=(config, i, self.start_events[i], self.stop_events[i])
            )
            process.start()
            self.processes.append(process)
            
        # Wait for all processes to start
        for event in self.start_events:
            event.wait()
            
    def stop_streams(self):
        # Stop all processes
        for stop_event in self.stop_events:
            stop_event.set()
            
        for process in self.processes:
            try:
                process.join(timeout=1)
                if process.is_alive():
                    self.logger.warning(f"Terminating process {process.pid}")
                    process.terminate()
            except Exception as e:
                self.logger.error(f"Failed to stop inference process {process.pid}: {e}")
        
        self.processes.clear()
        self.logger.info("All streams stopped")

    def _fetch_video_stream(self, config, index: int, start_event: Event, stop_event: Event):
        """
        Fetch video stream and distribute to model queues
        """
        with self._video_capture(config.rtsp_url) as cap:
            
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if cap.get(cv2.CAP_PROP_POS_FRAMES) % config.frame_skip != 0:
                    continue

                if not start_event.is_set():
                    start_event.set()
                    self.logger.info(f"Started stream: {config.rtsp_url}")

                # Distribute frame to all target model queues for this stream
                for model_idx in config.target_models:
                    self.frame_queues[model_idx].put_nowait(frame)
            self.logger.info(f"Stopped stream: {config.rtsp_url}")

    @contextmanager
    def _video_capture(self, rtsp_url: str):
        """Video capture context manager"""
        cap = cv2.VideoCapture(rtsp_url)
        try:
            if not cap.isOpened():
                raise ConnectionError(f"Failed to open stream: {rtsp_url}")
            # Enable hardware acceleration
            #cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
            yield cap
        finally:
            cap.release()
