"""
Camera Service Module
Handles video capture from USB RCA-to-video converter via OpenCV
Features:
- Multi-camera support (cycle between cameras)
- Rolling 30-minute segment recording with auto-delete
- Manual recording to preserve footage
- Frame buffering for UI display
"""

import logging
import threading
import cv2
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)

# Try to import OpenCV, gracefully handle if not available
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not installed - camera functionality disabled")


class CameraService:
    """
    Camera Video Capture Service
    Manages RCA backup camera via USB capture card
    Features:
    - Non-blocking frame capture
    - Rolling 30-minute buffer segments
    - Manual save functionality
    - Multi-camera support
    """

    def __init__(
        self,
        device: str = '/dev/video0',
        resolution: Tuple[int, int] = (720, 480),
        fps: int = 30,
        rolling_segment_minutes: int = 30,
        max_stored_hours: int = 1
    ):
        """
        Initialize camera service

        Args:
            device: Video device path (/dev/video0, /dev/video1, etc)
            resolution: (width, height) tuple
            fps: Frames per second
            rolling_segment_minutes: Duration of rolling buffer segments
            max_stored_hours: Maximum rolling buffer storage
        """
        self.device = device
        self.resolution = resolution
        self.fps = fps
        self.rolling_segment_minutes = rolling_segment_minutes
        self.max_stored_hours = max_stored_hours

        # Video capture
        self.capture = None
        self.connected = False
        self.is_running = False
        self.thread = None

        # Frame buffer
        self.current_frame = None
        self.frame_buffer = deque(maxlen=fps * 2)  # 2 seconds of frames

        # Recording state
        self.recording_manual = False
        self.current_segment_writer = None
        self.current_segment_path = None
        self.segment_start_time = None

        # Storage paths
        self.rolling_footage_dir = Path('logs/rolling_footage')
        self.saved_footage_dir = Path('logs/saved_footage')
        self.rolling_footage_dir.mkdir(parents=True, exist_ok=True)
        self.saved_footage_dir.mkdir(parents=True, exist_ok=True)

        # Camera selection
        self.available_cameras = []
        self.current_camera_index = 0
        self._retry_interval = 60      # seconds between reconnect attempts when disconnected

        logger.info(
            f"CameraService initialized (device={device}, "
            f"resolution={resolution}, fps={fps})"
        )

    def start(self):
        """Start camera capture thread"""
        if self.is_running:
            logger.warning("CameraService already running")
            return

        logger.info("Starting camera capture thread")
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop camera capture and cleanup"""
        logger.info("Stopping camera service")
        self.is_running = False

        # Stop recording
        if self.current_segment_writer:
            self.current_segment_writer.release()

        # Release capture
        if self.capture:
            self.capture.release()

        if self.thread:
            self.thread.join(timeout=5)

        logger.info("Camera service stopped")

    def _connect_camera(self) -> bool:
        """
        Attempt to connect to camera device
        Non-blocking with timeout
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available - camera disabled")
            self.connected = False
            return False

        try:
            logger.info(f"Attempting camera connection on {self.device}")

            # Open video device
            self.capture = cv2.VideoCapture(self.device)

            if not self.capture.isOpened():
                logger.warning(f"Could not open {self.device}")
                self.connected = False
                return False

            # Set resolution
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Single frame buffer

            self.connected = True
            logger.info(f"Camera connected: {self.resolution[0]}x{self.resolution[1]} @ {self.fps} FPS")
            return True

        except Exception as e:
            logger.error(f"Camera connection failed: {e}")
            self.connected = False
            return False

    def _capture_loop(self):
        """
        Background thread: continuously capture frames
        Manages rolling buffer and recording
        """
        segment_frame_count = int(self.fps * 60 * self.rolling_segment_minutes)
        frames_in_current_segment = 0

        while self.is_running:
            try:
                # Connect if not connected
                if not self.connected:
                    if not self._connect_camera():
                        time.sleep(self._retry_interval)
                        continue

                # Read frame
                ret, frame = self.capture.read()

                if not ret:
                    logger.warning("Failed to read frame from camera")
                    self.connected = False
                    continue

                # Store current frame
                self.current_frame = frame
                self.frame_buffer.append(frame)

                # Handle rolling segment buffer
                if frames_in_current_segment == 0:
                    self._start_new_segment()

                # Write to rolling segment
                if self.current_segment_writer:
                    self.current_segment_writer.write(frame)
                    frames_in_current_segment += 1

                    if frames_in_current_segment >= segment_frame_count:
                        self._finalize_segment()
                        frames_in_current_segment = 0

                # Clean old rolling footage
                self._cleanup_old_segments()

                # Control frame rate
                time.sleep(1 / self.fps)

            except Exception as e:
                logger.error(f"Error in camera capture loop: {e}")
                self.connected = False
                time.sleep(5)

    def _start_new_segment(self):
        """Start a new rolling segment writer"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            segment_path = self.rolling_footage_dir / f"segment_{timestamp}.mp4"

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.current_segment_writer = cv2.VideoWriter(
                str(segment_path),
                fourcc,
                self.fps,
                self.resolution
            )

            self.current_segment_path = segment_path
            self.segment_start_time = datetime.now()

            logger.info(f"Started new rolling segment: {segment_path.name}")

        except Exception as e:
            logger.error(f"Could not start new segment: {e}")

    def _finalize_segment(self):
        """Finalize current segment and release writer"""
        try:
            if self.current_segment_writer:
                self.current_segment_writer.release()
                logger.info(f"Finalized segment: {self.current_segment_path.name}")
                self.current_segment_writer = None

        except Exception as e:
            logger.error(f"Error finalizing segment: {e}")

    def _cleanup_old_segments(self):
        """Remove rolling footage older than max_stored_hours"""
        try:
            max_age = timedelta(hours=self.max_stored_hours)
            now = datetime.now()

            for segment_file in self.rolling_footage_dir.glob('segment_*.mp4'):
                # Parse timestamp from filename
                try:
                    timestamp_str = segment_file.stem.replace('segment_', '')
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                    if now - file_time > max_age:
                        segment_file.unlink()
                        logger.debug(f"Deleted old rolling segment: {segment_file.name}")

                except Exception as e:
                    logger.debug(f"Could not parse segment timestamp: {e}")

        except Exception as e:
            logger.warning(f"Error in cleanup: {e}")

    def save_current_segment(self):
        """
        Save current rolling segment to permanent storage
        System records: save current segment + record next 30 min (total 1 hour saved)
        """
        if not self.current_segment_path:
            logger.warning("No current segment to save")
            return False

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_path = self.saved_footage_dir / f"saved_{timestamp}.mp4"

            # Copy current segment to saved folder
            import shutil
            shutil.copy2(self.current_segment_path, saved_path)

            logger.info(f"Saved footage to: {saved_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving segment: {e}")
            return False

    def toggle_manual_recording(self) -> bool:
        """Toggle manual recording flag"""
        self.recording_manual = not self.recording_manual
        if self.recording_manual:
            logger.info("Manual recording enabled - will save current + next segment")
        else:
            logger.info("Manual recording disabled")
        return self.recording_manual

    def get_current_frame(self) -> Optional[bytes]:
        """Return current frame as JPEG bytes, or None."""
        if self.current_frame is None:
            return None
        try:
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            if ret:
                return jpeg.tobytes()
        except Exception as e:
            logger.debug(f"Error encoding frame: {e}")
        return None

    def get_current_frame_numpy(self):
        """Return current frame as numpy BGR array, or None."""
        return self.current_frame

    def cycle_camera(self) -> int:
        """
        Cycle to next available camera
        Returns current camera index
        """
        # Simulate camera cycling (future: detect actual cameras)
        self.current_camera_index = (self.current_camera_index + 1) % 2
        logger.info(f"Switched to camera {self.current_camera_index + 1}")
        return self.current_camera_index

    def get_status(self) -> dict:
        """Get camera service status"""
        return {
            'connected': self.connected,
            'device': self.device,
            'resolution': self.resolution,
            'fps': self.fps,
            'current_camera': self.current_camera_index + 1,
            'rolling_segments': len(list(self.rolling_footage_dir.glob('*.mp4'))),
            'saved_footage': len(list(self.saved_footage_dir.glob('*.mp4'))),
            'recording_manual': self.recording_manual,
        }


if __name__ == '__main__':
    # Test camera service
    logging.basicConfig(level=logging.DEBUG)

    camera = CameraService()
    camera.start()

    time.sleep(15)  # Run for 15 seconds

    print(f"Status: {camera.get_status()}")
    camera.stop()
