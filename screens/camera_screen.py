"""
Camera Screen — T1000 Infotainment System
Displays live backup camera feed with recording controls.
Uses Kivy Texture for live frame rendering.
Falls back to animated color-bar test pattern when no camera connected.
"""

import logging
import io
import threading
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class CameraScreen(Screen):
    """
    Backup camera display screen.
    Shows live OpenCV frames as Kivy textures.
    Generates an animated test pattern when no hardware present.
    """

    FRAME_UPDATE_HZ = 15   # UI refresh rate (not capture rate)

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'camera'
        self.services = services or {}
        self.camera_service = services.get('camera') if services else None

        self._frame_event = None
        self._sim_tick = 0
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)

        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)

        self.title_label = Label(text='Backup Camera', font_size='20sp', bold=True,
                                 color=(0.1, 0.7, 1.0, 1))
        title_bar.add_widget(self.title_label)

        self.rec_indicator = Label(text='', font_size='16sp', color=(1, 0.2, 0.2, 1),
                                   size_hint_x=None, width=80)
        title_bar.add_widget(self.rec_indicator)

        root.add_widget(title_bar)

        # ── Camera feed ───────────────────────────────────────────────
        self.feed_image = KivyImage(
            allow_stretch=True,
            keep_ratio=True,
        )
        root.add_widget(self.feed_image)

        # ── Info overlay ──────────────────────────────────────────────
        self.info_label = Label(
            text='Connecting to camera...', font_size='12sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None, height=22
        )
        root.add_widget(self.info_label)

        # ── Controls ──────────────────────────────────────────────────
        ctrl = BoxLayout(size_hint_y=None, height=52, spacing=10)

        self.cam_btn = Button(
            text='Camera 1  [C]',
            background_color=(0.1, 0.45, 0.75, 1), font_size='14sp'
        )
        self.cam_btn.bind(on_press=self._cycle_camera)
        ctrl.add_widget(self.cam_btn)

        self.rec_btn = Button(
            text='⏺ Record  [R]',
            background_color=(0.7, 0.15, 0.15, 1), font_size='14sp'
        )
        self.rec_btn.bind(on_press=self._toggle_record)
        ctrl.add_widget(self.rec_btn)

        save_btn = Button(
            text='💾 Save Clip',
            background_color=(0.25, 0.55, 0.25, 1), font_size='14sp'
        )
        save_btn.bind(on_press=self._save_clip)
        ctrl.add_widget(save_btn)

        root.add_widget(ctrl)
        self.add_widget(root)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        logger.info("Camera screen displayed")
        self._frame_event = Clock.schedule_interval(
            self._update_frame, 1.0 / self.FRAME_UPDATE_HZ
        )

    def on_leave(self):
        if self._frame_event:
            self._frame_event.cancel()
            self._frame_event = None

    # ------------------------------------------------------------------
    # Frame update
    # ------------------------------------------------------------------

    def _update_frame(self, dt):
        """Called on main thread at FRAME_UPDATE_HZ to refresh display."""
        frame = None

        if self.camera_service and self.camera_service.connected:
            frame = self.camera_service.get_current_frame_numpy()

        if frame is None:
            frame = self._generate_test_pattern()

        if frame is not None and NUMPY_AVAILABLE:
            self._blit_frame(frame)

        self._update_info()
        self._sim_tick += 1

    def _blit_frame(self, frame_bgr):
        """Convert a numpy BGR frame to a Kivy texture and display it."""
        if not NUMPY_AVAILABLE:
            return
        try:
            # BGR → RGB
            frame_rgb = frame_bgr[:, :, ::-1]
            h, w, _ = frame_rgb.shape
            tex = Texture.create(size=(w, h), colorfmt='rgb')
            # Kivy expects data bottom-up
            tex.blit_buffer(frame_rgb[::-1].tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.feed_image.texture = tex
        except Exception as e:
            logger.debug(f"Frame blit error: {e}")

    def _generate_test_pattern(self):
        """Generate an animated EIA color bar test pattern using numpy."""
        if not NUMPY_AVAILABLE:
            return None

        w, h = 720, 480
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        tick = self._sim_tick

        # 7-color SMPTE bars in top 75%
        bar_h = int(h * 0.75)
        colors = [
            (192, 192, 192),  # White
            (192, 192, 0),    # Yellow
            (0,   192, 192),  # Cyan
            (0,   192, 0),    # Green
            (192, 0,   192),  # Magenta
            (192, 0,   0),    # Red
            (0,   0,   192),  # Blue
        ]
        bar_w = w // len(colors)
        for i, color in enumerate(colors):
            x0 = i * bar_w
            x1 = x0 + bar_w
            frame[:bar_h, x0:x1] = color

        # Bottom strip: black / cyan / magenta / black / white / black
        bot_colors = [(0,0,0),(0,192,192),(192,0,192),(0,0,0),(255,255,255),(0,0,0),(192,192,192)]
        bot_w = w // len(bot_colors)
        for i, color in enumerate(bot_colors):
            x0 = i * bot_w
            x1 = x0 + bot_w
            frame[bar_h:, x0:x1] = color

        # Animated scan line
        if OPENCV_AVAILABLE:
            line_y = int((tick * 4) % bar_h)
            cv2.line(frame, (0, line_y), (w, line_y), (255, 255, 255), 1)

            ts = datetime.now().strftime('%H:%M:%S')
            cv2.putText(frame, 'NO CAMERA — DISCONNECTED', (10, 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.95, (60, 60, 255), 2)
            cv2.putText(frame, ts, (10, 62),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 1)
            cv2.putText(frame, 'Connect a USB camera / RCA capture card',
                        (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (180, 180, 180), 1)

        return frame

    def _update_info(self):
        try:
            if self.camera_service:
                status = self.camera_service.get_status()
                if status['connected']:
                    src = '● LIVE'
                    self.title_label.color = (0.3, 1.0, 0.3, 1)
                else:
                    src = '✕ DISCONNECTED'
                    self.title_label.color = (1.0, 0.3, 0.3, 1)
                cam = status['current_camera']
                segs = status['rolling_segments']
                self.info_label.text = (
                    f"{src} | Cam {cam} | Rolling segments: {segs} "
                    f"| Saved: {status['saved_footage']}"
                )
                if status['recording_manual']:
                    self.rec_indicator.text = '● REC'
                    self.rec_btn.background_color = (0.9, 0.1, 0.1, 1)
                else:
                    self.rec_indicator.text = ''
                    self.rec_btn.background_color = (0.7, 0.15, 0.15, 1)
            else:
                self.info_label.text = '✕ DISCONNECTED — Camera service unavailable'
                self.title_label.color = (1.0, 0.3, 0.3, 1)
        except Exception as e:
            self.info_label.text = f'Camera error: {e}'

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _cycle_camera(self, *_):
        if self.camera_service:
            idx = self.camera_service.cycle_camera()
            self.cam_btn.text = f'Camera {idx + 1}  [C]'
        logger.info("Camera cycled")

    def _toggle_record(self, *_):
        if self.camera_service:
            state = self.camera_service.toggle_manual_recording()
            self.rec_btn.text = '⏹ Stop REC  [R]' if state else '⏺ Record  [R]'
        logger.info("Record toggled")

    def _save_clip(self, *_):
        if self.camera_service:
            ok = self.camera_service.save_current_segment()
            self.info_label.text = "✔ Clip saved!" if ok else "✘ Save failed — no active segment"
        logger.info("Save clip requested")

    # ------------------------------------------------------------------
    # Keyboard forwarding (called from main app)
    # ------------------------------------------------------------------

    def handle_key(self, key, codepoint):
        if codepoint == 'c':
            self._cycle_camera()
            return True
        if codepoint == 'r':
            self._toggle_record()
            return True
        return False
