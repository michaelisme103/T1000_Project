#!/usr/bin/env python3
"""
T1000 Infotainment System — Main Application Entry Point
Raspberry Pi 4B | Kivy UI | 1997 Toyota T100

Architecture:
  1. Load configuration (config/settings.json)
  2. Initialize all services (OBD2, Camera, GPIO, Audio, DataLogger, GPS, Health)
  3. Build Kivy ScreenManager and inject services into every screen
  4. Bind GPIO reverse-signal → auto-switch to camera screen
  5. Route keyboard events to the active screen
  6. On exit, stop all services cleanly
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# ── Kivy environment setup (before any kivy imports) ─────────────────────────
os.environ.setdefault('KIVY_NO_ENV_CONFIG', '1')
os.environ.setdefault('DISPLAY', ':0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock

# ── Logging setup ─────────────────────────────────────────────────────────────
Path('logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/t1000.log'),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ── Service imports ───────────────────────────────────────────────────────────
from services.obd_service      import OBDService
from services.camera_service   import CameraService
from services.gpio_service     import GPIOService, GPIOPin
from services.audio_service    import AudioService
from services.data_logger      import DataLogger
from services.gps_service      import GPSService
from services.health_monitor   import HealthMonitor
from services.mileage_tracker  import MileageTracker

# ── Screen imports ────────────────────────────────────────────────────────────
from screens.home_screen        import HomeScreen
from screens.camera_screen      import CameraScreen
from screens.music_screen       import MusicScreen
from screens.diagnostics_screen import DiagnosticsScreen
from screens.navigation_screen  import NavigationScreen
from screens.settings_screen    import SettingsScreen
from screens.health_screen      import HealthScreen
from screens.mileage_screen     import MileageScreen


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "obd2": {
        "port": "/dev/ttyUSB0",
        "baudrate": 38400,
        "polling_interval_seconds": 5,
        "timeout_seconds": 2
    },
    "camera": {
        "device": "/dev/video0",
        "resolution": [720, 480],
        "fps": 30,
        "rolling_segment_minutes": 30,
        "max_storage_hours": 1,
        "video_storage_path": "video_storage"
    },
    "gpio": {
        "use_gpio": False,
        "reverse_signal_pin": 17,
        "polling_hz": 50,
        "debounce_ms": 50
    },
    "audio": {
        "use_mpd": False,
        "audio_mode": "SPOTIFY_IPAD",
        "mpd_host": "localhost",
        "mpd_port": 6600,
        "default_volume": 50
    },
    "data_logging": {
        "enabled": True,
        "csv_path": "data/trips.csv",
        "log_interval_seconds": 5,
        "retention_days": 30
    },
    "gps": {
        "gpsd_host": "localhost",
        "gpsd_port": 2947
    },
    "ui": {
        "debug_mode": False,
        "window_size": [1280, 800],
        "fullscreen": False
    }
}


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def load_config() -> dict:
    config_path = Path('config/settings.json')
    config = DEFAULT_CONFIG.copy()
    try:
        if config_path.exists():
            with open(config_path) as f:
                _deep_merge(config, json.load(f))
            logger.info("Configuration loaded from config/settings.json")
        else:
            logger.warning("config/settings.json not found — using defaults")
    except Exception as e:
        logger.warning(f"Config load error: {e} — using defaults")
    return config


# ─────────────────────────────────────────────────────────────────────────────
# Service factory
# ─────────────────────────────────────────────────────────────────────────────

def build_services(config: dict) -> dict:
    cam_cfg  = config.get('camera', {})
    obd_cfg  = config.get('obd2',   {})
    aud_cfg  = config.get('audio',  {})
    gpio_cfg = config.get('gpio',   {})
    gps_cfg  = config.get('gps',    {})

    obd = OBDService(
        port=obd_cfg.get('port', '/dev/ttyUSB0'),
        baudrate=obd_cfg.get('baudrate', 38400),
        polling_interval=obd_cfg.get('polling_interval_seconds', 5),
    )

    cam_res = cam_cfg.get('resolution', [720, 480])
    camera = CameraService(
        device=cam_cfg.get('device', '/dev/video0'),
        resolution=tuple(cam_res),
        fps=cam_cfg.get('fps', 30),
        rolling_segment_minutes=cam_cfg.get('rolling_segment_minutes', 30),
        max_stored_hours=cam_cfg.get('max_storage_hours', 1),
    )

    gpio = GPIOService(
        use_gpio=gpio_cfg.get('use_gpio', False),
        gpio_mode='BCM',
    )

    audio = AudioService(
        use_mpd=aud_cfg.get('use_mpd', False),
        mpd_host=aud_cfg.get('mpd_host', 'localhost'),
        mpd_port=aud_cfg.get('mpd_port', 6600),
    )
    audio.set_volume(aud_cfg.get('default_volume', 50))

    data_log = DataLogger(log_dir='logs/diagnostics')

    gps = GPSService(
        gpsd_host=gps_cfg.get('gpsd_host', 'localhost'),
        gpsd_port=gps_cfg.get('gpsd_port', 2947),
    )

    health = HealthMonitor(obd_service=obd, poll_interval=5.0)

    mileage = MileageTracker(gps_service=gps, obd_service=obd)

    return {
        'obd':     obd,
        'camera':  camera,
        'gpio':    gpio,
        'audio':   audio,
        'logger':  data_log,
        'gps':     gps,
        'health':  health,
        'mileage': mileage,
    }


def start_services(services: dict):
    for name, svc in services.items():
        if hasattr(svc, 'start'):
            try:
                svc.start()
                logger.info(f"Service '{name}' started")
            except Exception as e:
                logger.error(f"Failed to start '{name}': {e}")


def stop_services(services: dict):
    for name, svc in services.items():
        if hasattr(svc, 'stop'):
            try:
                svc.stop()
                logger.info(f"Service '{name}' stopped")
            except Exception as e:
                logger.warning(f"Error stopping '{name}': {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Kivy Application
# ─────────────────────────────────────────────────────────────────────────────

class T1000App(App):
    """
    T1000 Infotainment System Kivy application.
    Services are built once, injected into every screen, then started.
    """

    title = 'T1000 Infotainment System'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_data = load_config()
        self.services: dict = {}
        self.sm: ScreenManager = None

        ui = self.config_data.get('ui', {})
        Window.size = tuple(ui.get('window_size', [1280, 800]))
        if ui.get('fullscreen', False):
            Window.fullscreen = 'auto'

        logger.info("T1000App initializing")

    # ------------------------------------------------------------------
    def build(self):
        self.services = build_services(self.config_data)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))

        screens = [
            HomeScreen(services=self.services, name='home'),
            CameraScreen(services=self.services, name='camera'),
            MusicScreen(services=self.services, name='music'),
            DiagnosticsScreen(services=self.services, name='diagnostics'),
            NavigationScreen(services=self.services, name='navigation'),
            HealthScreen(services=self.services, name='health'),
            MileageScreen(services=self.services, name='mileage'),
            SettingsScreen(services=self.services,
                           config=self.config_data, name='settings'),
        ]
        for s in screens:
            self.sm.add_widget(s)

        self.sm.current = 'home'
        Window.bind(on_keyboard=self._on_keyboard)

        logger.info("All screens registered")
        return self.sm

    # ------------------------------------------------------------------
    def on_start(self):
        start_services(self.services)
        self._wire_gpio()
        data_log = self.services.get('logger')
        if data_log:
            data_log.start_session()
        logger.info("T1000 ready")

    def on_stop(self):
        logger.info("Shutting down...")
        data_log = self.services.get('logger')
        if data_log and data_log.is_logging:
            data_log.end_session()
        stop_services(self.services)
        logger.info("Shutdown complete")

    # ------------------------------------------------------------------
    def _wire_gpio(self):
        gpio = self.services.get('gpio')
        if not gpio:
            return

        def on_reverse(active: bool):
            target = 'camera' if active else 'home'
            Clock.schedule_once(lambda dt: setattr(self.sm, 'current', target))

        gpio.register_reverse_callback(on_reverse)
        gpio.register_callback(GPIOPin.HOME_BUTTON,
            lambda: Clock.schedule_once(lambda dt: setattr(self.sm, 'current', 'home')))
        gpio.register_callback(GPIOPin.PAUSE_PLAY,
            lambda: self._audio_action('play'))
        gpio.register_callback(GPIOPin.SKIP_FORWARD,
            lambda: self._audio_action('next'))
        gpio.register_callback(GPIOPin.SKIP_BACK,
            lambda: self._audio_action('prev'))
        gpio.register_callback(GPIOPin.VOLUME_UP,
            lambda: self._vol_change(+5))
        gpio.register_callback(GPIOPin.VOLUME_DOWN,
            lambda: self._vol_change(-5))
        gpio.register_callback(GPIOPin.CAMERA_SKIP,
            lambda: self.services.get('camera') and self.services['camera'].cycle_camera())
        gpio.register_callback(GPIOPin.RECORD,
            lambda: self.services.get('camera') and self.services['camera'].toggle_manual_recording())

        logger.info("GPIO callbacks registered")

    def _audio_action(self, action: str):
        a = self.services.get('audio')
        if not a: return
        {'play': a.toggle_play, 'next': a.next, 'prev': a.previous}[action]()

    def _vol_change(self, delta: int):
        a = self.services.get('audio')
        if a:
            a.set_volume(max(0, min(100, a.get_volume() + delta)))

    # ------------------------------------------------------------------
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """
        Global keyboard routing.

        Universal keys:
          h        → Home
          Esc      → Back to Home
          d        → Diagnostics
          m        → Music
          c        → Camera (+ forwarded)
          n        → Navigation
          g        → Health
          s        → Settings
          p        → Power placeholder
          b        → Brightness placeholder

        Screen-forwarded keys (delegated to active screen's handle_key):
          Space, Arrow keys, r, c
        """
        cp = codepoint or ''

        # Global navigation
        if cp == 'h':
            self.sm.current = 'home'; return True
        if key == 27:
            if self.sm.current != 'home':
                self.sm.current = 'home'
            return True

        screen_shortcuts = {
            'd': 'diagnostics', 'm': 'music',
            'n': 'navigation',  'g': 'health', 's': 'settings',
            'l': 'mileage',
        }
        if cp in screen_shortcuts:
            self.sm.current = screen_shortcuts[cp]; return True

        # Forward to active screen
        active = self.sm.current_screen
        if hasattr(active, 'handle_key') and active.handle_key(key, cp):
            return True

        # Remaining globals
        if cp == 'p':
            logger.info("Power key"); return True
        if cp == 'b':
            logger.info("Brightness key"); return True

        return False


# ─────────────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 62)
    logger.info("  T1000 Infotainment System  —  Starting")
    logger.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 62)
    try:
        T1000App().run()
    except KeyboardInterrupt:
        logger.info("Interrupted — exiting")
    except Exception as e:
        logger.critical(f"Fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
