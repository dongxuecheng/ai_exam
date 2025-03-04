from multiprocessing import Queue, Event, Process
from ..schemas import StreamConfig
import cv2
from ..core import logger
from contextlib import contextmanager



class VideoStreamer:
    def __init__(self, stream_configs: list[StreamConfig],num_models: int):
        """
        初始化视频流管理器
        :param stream_configs: 每个视频流的配置
        """
        self.stream_configs = stream_configs
        self.num_models = num_models  # 总模型数量
        
        # 为每个模型创建对应的帧队列
        self.frame_queues = [
            Queue(maxsize=100) for _ in range(self.num_models)
        ]
        
        # 进程和事件管理
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
                    logger.warning(f"Terminating process {process.pid}")
                    process.terminate()
            except Exception as e:
                logger.error(f"Failed to stop inference process {process.pid}: {e}")
        
        #self._reset_queues()
        self.processes.clear()

        logger.info("All streams stopped")

    def _fetch_video_stream(self, config: StreamConfig, 
                          index: int, start_event: Event, 
                          stop_event: Event):
        """
        获取视频流并分发到对应模型的队列
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
                    logger.info(f"Started stream: {config.rtsp_url}")

                # 将同一帧分发到该流对应的所有模型队列
                for model_idx in config.target_models:
                    self.frame_queues[model_idx].put_nowait(frame)
            logger.info(f"Stopped stream: {config.rtsp_url}")

    @contextmanager
    def _video_capture(self, rtsp_url: str):
        """视频捕获的上下文管理器"""
        cap = cv2.VideoCapture(rtsp_url)
        try:
            if not cap.isOpened():
                raise ConnectionError(f"Failed to open stream: {rtsp_url}")
            yield cap
        finally:
            cap.release()