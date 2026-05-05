"""
Home Screen — T1000 Infotainment System
Main menu hub with system status indicators.
"""

import logging
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

logger = logging.getLogger(__name__)


class NavButton(Button):
    """Styled navigation button with icon and label."""
    def __init__(self, icon: str, label: str, color: tuple, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{icon}\n{label}"
        self.font_size = '16sp'
        self.markup = True
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self._btn_color = color
        self._btn_label = label
        self.bind(size=self._draw_bg, pos=self._draw_bg)

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._btn_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])


class HomeScreen(Screen):
    """
    Main menu screen.
    Displays all available systems with status indicators.
    """

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'
        self.services = services or {}
        self._build_ui()
        Clock.schedule_interval(self._update_status, 2.0)

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=16, spacing=10)

        # ── Header ───────────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.title_label = Label(
            text='T1000 Infotainment',
            font_size='26sp', bold=True,
            color=(0.1, 0.7, 1.0, 1),
            size_hint_x=0.7
        )
        self.clock_label = Label(
            text='', font_size='16sp', color=(0.8, 0.8, 0.8, 1),
            size_hint_x=0.3, halign='right'
        )
        header.add_widget(self.title_label)
        header.add_widget(self.clock_label)
        root.add_widget(header)

        # ── Status bar ───────────────────────────────────────────────────
        self.status_bar = Label(
            text='Initializing systems...',
            font_size='11sp', color=(0.6, 0.9, 0.6, 1),
            size_hint_y=None, height=22
        )
        root.add_widget(self.status_bar)

        # ── Navigation grid ───────────────────────────────────────────────
        grid = GridLayout(cols=2, spacing=14)

        buttons = [
            ('📷', 'Camera',      'camera',      (0.10, 0.40, 0.70, 1)),
            ('🎵', 'Music',       'music',        (0.15, 0.55, 0.30, 1)),
            ('🔧', 'Diagnostics', 'diagnostics',  (0.60, 0.35, 0.05, 1)),
            ('🗺', 'Navigation',  'navigation',   (0.35, 0.15, 0.65, 1)),
            ('❤', 'Health',      'health',       (0.65, 0.15, 0.20, 1)),
            ('🚗', 'Mileage',     'mileage',      (0.50, 0.28, 0.08, 1)),
            ('⚙', 'Settings',    'settings',     (0.30, 0.30, 0.30, 1)),
        ]

        for icon, label, screen, color in buttons:
            btn = NavButton(icon=icon, label=label, color=color)
            btn.bind(on_press=lambda x, s=screen: self._navigate(s))
            grid.add_widget(btn)

        root.add_widget(grid)

        # ── Quick status strip ─────────────────────────────────────────
        self.quick_status = Label(
            text='OBD: -- | GPS: -- | Temp: -- | Battery: --',
            font_size='11sp', color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=22
        )
        root.add_widget(self.quick_status)

        self.add_widget(root)

    def _navigate(self, screen_name: str):
        logger.info(f"Navigating to {screen_name}")
        try:
            self.manager.current = screen_name
        except Exception as e:
            logger.warning(f"Screen '{screen_name}' not found: {e}")
            self.status_bar.text = f"Screen '{screen_name}' not available yet"

    def _update_status(self, dt):
        self.clock_label.text = datetime.now().strftime('%H:%M:%S\n%b %d')

        # Build quick status line from services
        parts = []

        obd = self.services.get('obd')
        if obd:
            r = obd.get_reading('COOLANT_TEMP')
            temp_str = f"{r.value:.0f}°F" if r else '--'
            v = obd.get_reading('BATTERY_VOLTAGE')
            volt_str = f"{v.value:.1f}V" if v else '--'
            parts.append(f"OBD: {'Live' if obd.connected else 'Sim'}")
            parts.append(f"Temp: {temp_str}")
            parts.append(f"Batt: {volt_str}")

        gps = self.services.get('gps')
        if gps:
            fix = gps.get_fix()
            if fix:
                gps_str = f"GPS: {'Fix' if fix.fix_quality > 0 else 'NoFix'}{'[SIM]' if fix.simulated else ''}"
            else:
                gps_str = "GPS: Searching"
            parts.append(gps_str)

        health = self.services.get('health')
        if health:
            parts.append(f"Pi: {health.get_overall_score()}%")

        self.quick_status.text = '  |  '.join(parts) if parts else 'Systems initializing...'

    def on_enter(self):
        logger.info("Home screen displayed")
        self._update_status(0)
