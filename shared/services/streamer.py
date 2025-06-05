from multiprocessing import Queue, Event, Process
import cv2
from contextlib import contextmanager
import logging
import time
from queue import Full, Empty
from typing import List, Optional

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
        
        # Create frame queues for each model using unified queue_size
        # All queues use the same size from config (assuming all configs have same queue_size)
        queue_size = stream_configs[0].queue_size if stream_configs else 100
        self.frame_queues = [Queue(maxsize=queue_size) for _ in range(self.num_models)]
        
        # Process and event management
        self.processes: List[Process] = []
        self.start_events = [Event() for _ in range(len(stream_configs))]
        self.stop_events = [Event() for _ in range(len(stream_configs))]
        self.reconnect_delays = [1.0] * len(stream_configs)  # Exponential backoff delays

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
        """Stop all video streams and cleanup resources"""
        # Stop all processes
        for stop_event in self.stop_events:
            stop_event.set()
            
        for process in self.processes:
            try:
                process.join(timeout=5)  # Increased timeout
                if process.is_alive():
                    self.logger.warning(f"Terminating process {process.pid}")
                    process.terminate()
                    process.join(timeout=2)
                    if process.is_alive():
                        self.logger.error(f"Force killing process {process.pid}")
                        process.kill()
            except Exception as e:
                self.logger.error(f"Failed to stop inference process {process.pid}: {e}")
        
        # Clear queues to prevent memory leaks
        self._clear_queues()
        
        self.processes.clear()
        self.logger.info("All streams stopped")
    
    def _clear_queues(self):
        """Clear all frame queues to prevent memory leaks"""
        for queue in self.frame_queues:
            try:
                while True:
                    queue.get_nowait()
            except Empty:
                pass  # Queue is empty
            except Exception as e:
                self.logger.warning(f"Error clearing queue: {e}")

    def _fetch_video_stream(self, config, index: int, start_event, stop_event):
        """
        Fetch video stream and distribute to model queues with reconnection logic
        """
        stream_started = False
        reconnect_delay = 1.0
        max_reconnect_delay = 60.0
        frame_count = 0
        
        while not stop_event.is_set():
            try:
                with self._video_capture(config.rtsp_url) as cap:
                    if not stream_started:
                        start_event.set()
                        stream_started = True
                        self.logger.info(f"Started stream: {config.rtsp_url}")
                        reconnect_delay = 1.0  # Reset delay on successful connection
                    
                    while not stop_event.is_set():
                        # Grab frame from buffer without decoding (fast operation)
                        ret = cap.grab()
                        if not ret:
                            self.logger.warning(f"Failed to grab frame from {config.rtsp_url}")
                            break
                        
                        frame_count += 1
                        
                        # Apply frame skip logic - only retrieve and decode needed frames
                        if frame_count % config.frame_skip != 0:
                            continue  # Skip frame without expensive decoding
                        
                        # Retrieve and decode the current frame (only for frames we need)
                        ret, frame = cap.retrieve()
                        if not ret:
                            self.logger.warning(f"Failed to retrieve frame from {config.rtsp_url}")
                            continue

                        # Distribute frame to all target model queues for this stream
                        self._distribute_frame_safely(frame, config.target_models, config.rtsp_url)
                        
            except ConnectionError as e:
                self.logger.error(f"Connection error for {config.rtsp_url}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error in stream {config.rtsp_url}: {e}")
            
            if not stop_event.is_set():
                self.logger.info(f"Reconnecting to {config.rtsp_url} in {reconnect_delay:.1f}s")
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                
        self.logger.info(f"Stopped stream: {config.rtsp_url}")
    
    def _distribute_frame_safely(self, frame, target_models, rtsp_url: str):
        """Safely distribute frame to target model queues"""
        for model_idx in sorted(target_models):  # Sort for consistent ordering
            if model_idx >= len(self.frame_queues):
                self.logger.error(f"Invalid model index {model_idx} for stream {rtsp_url}")
                continue
                
            try:
                self.frame_queues[model_idx].put_nowait(frame)
            except Full:
                # Queue is full, remove oldest frame and add new one
                try:
                    self.frame_queues[model_idx].get_nowait()
                    self.frame_queues[model_idx].put_nowait(frame)
                    self.logger.debug(f"Dropped frame for model {model_idx} (queue full)")
                except (Full, Empty):
                    self.logger.warning(f"Failed to add frame to queue for model {model_idx}")
            except Exception as e:
                self.logger.error(f"Error distributing frame to model {model_idx}: {e}")

    @contextmanager
    def _video_capture(self, rtsp_url: str):
        """Video capture context manager with better error handling"""
        cap = None
        try:
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                raise ConnectionError(f"Failed to open stream: {rtsp_url}")
            
            # Set capture properties for better performance
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize latency
            cap.set(cv2.CAP_PROP_FPS, 30)  # Set desired FPS
            
            # Try to enable hardware acceleration if available
            try:
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            except:
                pass  # Hardware acceleration not available
            
            yield cap
            
        except Exception as e:
            if cap:
                cap.release()
            raise ConnectionError(f"Video capture error for {rtsp_url}: {e}")
        finally:
            if cap:
                cap.release()
    
    def get_queue_status(self) -> dict:
        """Get status information about all queues"""
        status = {}
        for i, queue in enumerate(self.frame_queues):
            status[f"model_{i}"] = {
                "size": queue.qsize(),
                "maxsize": queue._maxsize if hasattr(queue, '_maxsize') else 'unknown'
            }
        return status
    
    def get_stream_status(self) -> dict:
        """Get status of all streams"""
        status = {}
        for i, (config, process) in enumerate(zip(self.stream_configs, self.processes)):
            status[f"stream_{i}"] = {
                "url": config.rtsp_url,
                "alive": process.is_alive() if process else False,
                "pid": process.pid if process and process.is_alive() else None
            }
        return status
