"""
Settings Screen — T1000 Infotainment System
Edit configuration values and view system information.
"""

import logging
import json
from pathlib import Path

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.clock import Clock

logger = logging.getLogger(__name__)

CONFIG_PATH = Path('config/settings.json')


class SettingsRow(BoxLayout):
    """Label + control widget row."""
    def __init__(self, label_text: str, control_widget, **kwargs):
        super().__init__(size_hint_y=None, height=42, spacing=10, **kwargs)
        lbl = Label(text=label_text, font_size='13sp',
                    color=(0.7, 0.7, 0.7, 1), size_hint_x=0.5,
                    halign='right', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)
        self.add_widget(control_widget)


class SettingsScreen(Screen):
    """System configuration screen."""

    def __init__(self, services: dict = None, config: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.services = services or {}
        self.config = config or {}
        self._inputs = {}
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)
        title_bar.add_widget(Label(text='Settings', font_size='20sp',
                                   bold=True, color=(0.1, 0.7, 1.0, 1)))
        save_btn = Button(text='💾 Save', size_hint_x=None, width=80,
                          background_color=(0.2, 0.5, 0.2, 1), font_size='14sp')
        save_btn.bind(on_press=self._save_config)
        title_bar.add_widget(save_btn)
        root.add_widget(title_bar)

        # ── Scrollable settings ───────────────────────────────────────
        sv = ScrollView()
        grid = GridLayout(cols=1, spacing=4, size_hint_y=None, padding=6)
        grid.bind(minimum_height=grid.setter('height'))

        self._add_section(grid, 'OBD2 Settings')
        self._add_text_row(grid, 'OBD Port',    'obd2.port',        '/dev/ttyUSB0')
        self._add_text_row(grid, 'Baud Rate',   'obd2.baudrate',    '38400')
        self._add_text_row(grid, 'Poll Interval (s)', 'obd2.polling_interval_seconds', '5')

        self._add_section(grid, 'Camera Settings')
        self._add_text_row(grid, 'Camera Device',  'camera.device',     '/dev/video0')
        self._add_text_row(grid, 'Resolution W',   'camera.resolution.0','720')
        self._add_text_row(grid, 'Resolution H',   'camera.resolution.1','480')
        self._add_text_row(grid, 'FPS',            'camera.fps',         '30')
        self._add_text_row(grid, 'Segment (min)',  'camera.rolling_segment_minutes', '30')
        self._add_text_row(grid, 'Max Store (h)',  'camera.max_storage_hours', '1')

        self._add_section(grid, 'Audio Settings')
        self._add_text_row(grid, 'MPD Host',    'audio.mpd_host', 'localhost')
        self._add_text_row(grid, 'MPD Port',    'audio.mpd_port', '6600')
        self._add_text_row(grid, 'Default Vol', 'audio.default_volume', '50')

        self._add_section(grid, 'GPIO Settings')
        self._add_text_row(grid, 'Reverse Pin', 'gpio.reverse_signal_pin', '17')

        self._add_section(grid, 'UI Settings')
        self._add_text_row(grid, 'Window W',   'ui.window_size.0', '1280')
        self._add_text_row(grid, 'Window H',   'ui.window_size.1', '800')

        sv.add_widget(grid)
        root.add_widget(sv)

        # ── System info strip ─────────────────────────────────────────
        self.sysinfo_label = Label(
            text='Loading system info...', font_size='11sp',
            color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=22
        )
        root.add_widget(self.sysinfo_label)

        # ── Status bar ────────────────────────────────────────────────
        self.status_label = Label(
            text='', font_size='12sp', color=(0.5, 0.9, 0.5, 1),
            size_hint_y=None, height=24
        )
        root.add_widget(self.status_label)

        self.add_widget(root)

    def _add_section(self, grid, title: str):
        lbl = Label(text=f'[b]{title}[/b]', markup=True, font_size='14sp',
                    color=(0.4, 0.8, 1.0, 1), halign='left',
                    size_hint_y=None, height=32)
        lbl.bind(size=lbl.setter('text_size'))
        grid.add_widget(lbl)

    def _add_text_row(self, grid, label: str, key: str, default: str):
        inp = TextInput(
            text=self._get_config_value(key, default),
            multiline=False, font_size='13sp',
            background_color=(0.12, 0.12, 0.18, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.1, 0.7, 1, 1),
        )
        self._inputs[key] = inp
        grid.add_widget(SettingsRow(label, inp))

    def _get_config_value(self, key_path: str, default: str) -> str:
        """Traverse dot-separated key path in config dict."""
        parts = key_path.split('.')
        val = self.config
        for part in parts:
            if isinstance(val, list):
                try:
                    val = val[int(part)]
                except (IndexError, ValueError):
                    return default
            elif isinstance(val, dict):
                val = val.get(part, {})
            else:
                return default
        return str(val) if val != {} else default

    def _set_config_value(self, key_path: str, value: str):
        """Write value back into nested config dict."""
        parts = key_path.split('.')
        target = self.config
        for part in parts[:-1]:
            if isinstance(target, list):
                target = target[int(part)]
            else:
                target = target.setdefault(part, {})

        last = parts[-1]
        # Try to convert to appropriate type
        try:
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            pass  # keep as string

        if isinstance(target, list):
            target[int(last)] = value
        else:
            target[last] = value

    def _save_config(self, *_):
        try:
            for key, inp in self._inputs.items():
                self._set_config_value(key, inp.text.strip())

            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)

            self.status_label.text = '✔ Settings saved — restart for some changes to take effect'
            self.status_label.color = (0.3, 1.0, 0.3, 1)
            logger.info("Settings saved to config/settings.json")

        except Exception as e:
            self.status_label.text = f'✘ Save failed: {e}'
            self.status_label.color = (1.0, 0.3, 0.3, 1)
            logger.error(f"Settings save error: {e}")

    def on_enter(self):
        logger.info("Settings screen displayed")
        self._refresh_inputs()
        Clock.schedule_once(self._update_sysinfo, 0.5)

    def _refresh_inputs(self):
        """Re-populate inputs from current config."""
        for key, inp in self._inputs.items():
            inp.text = self._get_config_value(key, inp.text)

    def _update_sysinfo(self, dt):
        health = self.services.get('health')
        if health:
            s = health.get_system_health()
            temp = f"{s.cpu_temp_c:.1f}°C" if s.cpu_temp_c else "N/A"
            self.sysinfo_label.text = (
                f"Pi: CPU {s.cpu_percent:.1f}%  RAM {s.ram_percent:.1f}%  "
                f"Temp {temp}  Disk {s.disk_percent:.1f}%  "
                f"Uptime {health.get_uptime_str()}"
            )
        else:
            self.sysinfo_label.text = 'Install psutil for system metrics'

    def handle_key(self, key, codepoint):
        return False
