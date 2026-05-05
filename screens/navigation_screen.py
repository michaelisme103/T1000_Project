"""
Navigation Screen — T1000 Infotainment System
Displays GPS position, speed, heading, and satellite fix quality.
Renders a simple compass rose and coordinate display.
Placeholder for future offline map tile integration.
"""

import logging
import math
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Ellipse, Line, Triangle,
                            PushMatrix, PopMatrix, Rotate, Translate)
from kivy.clock import Clock

logger = logging.getLogger(__name__)


class CompassWidget(Widget):
    """
    Simple compass rose widget drawn with Kivy graphics.
    Rotates the needle to show current heading.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._heading = 0.0
        self.bind(size=self._redraw, pos=self._redraw)

    def set_heading(self, heading: float):
        self._heading = heading
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - 8

        with self.canvas:
            # Outer ring
            Color(0.2, 0.3, 0.5, 1)
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(0.3, 0.6, 0.9, 1)
            Line(circle=(cx, cy, r), width=2)

            # Cardinal labels (drawn as tick marks)
            for deg, label_txt in [(0, 'N'), (90, 'E'), (180, 'S'), (270, 'W')]:
                rad = math.radians(deg - 90)
                x0 = cx + (r - 12) * math.cos(rad)
                y0 = cy + (r - 12) * math.sin(rad)
                x1 = cx + r * math.cos(rad)
                y1 = cy + r * math.sin(rad)
                Color(0.7, 0.8, 1.0, 1)
                Line(points=[x0, y0, x1, y1], width=2)

            # Heading needle (red = North, white = South)
            needle_rad = math.radians(-self._heading + 90)
            nlen = r - 14
            nx = cx + nlen * math.cos(needle_rad)
            ny = cy + nlen * math.sin(needle_rad)
            Color(1.0, 0.2, 0.2, 1)
            Line(points=[cx, cy, nx, ny], width=3)

            # South end of needle
            s_rad = math.radians(-self._heading + 90 + 180)
            sx = cx + (nlen * 0.5) * math.cos(s_rad)
            sy = cy + (nlen * 0.5) * math.sin(s_rad)
            Color(0.9, 0.9, 0.9, 1)
            Line(points=[cx, cy, sx, sy], width=2)

            # Center dot
            Color(1.0, 1.0, 1.0, 1)
            Ellipse(pos=(cx - 4, cy - 4), size=(8, 8))


class NavigationScreen(Screen):
    """
    GPS navigation display screen.
    Shows position, speed, heading, satellite count, and fix quality.
    """

    UPDATE_HZ = 1.0   # refresh every second

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'navigation'
        self.services = services or {}
        self.gps_service = services.get('gps') if services else None
        self._update_event = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)
        title_bar.add_widget(Label(text='Navigation / GPS', font_size='20sp',
                                   bold=True, color=(0.1, 0.7, 1.0, 1)))
        self.fix_label = Label(text='Searching...', font_size='12sp',
                               color=(1, 0.75, 0, 1), size_hint_x=None, width=120)
        title_bar.add_widget(self.fix_label)
        root.add_widget(title_bar)

        # ── Main content (compass + data) ─────────────────────────────
        content = BoxLayout(spacing=12)

        # Left — compass
        compass_box = BoxLayout(orientation='vertical', size_hint_x=0.4)
        self.compass = CompassWidget()
        compass_box.add_widget(self.compass)
        self.heading_label = Label(text='---°  ---', font_size='16sp', bold=True,
                                   color=(0.8, 0.9, 1.0, 1), size_hint_y=None, height=30)
        compass_box.add_widget(self.heading_label)
        content.add_widget(compass_box)

        # Right — data grid
        data_grid = GridLayout(cols=2, spacing=6, size_hint_x=0.6)

        info_fields = [
            ('Latitude',   'lat_label',   '---'),
            ('Longitude',  'lon_label',   '---'),
            ('Speed',      'spd_label',   '-- mph'),
            ('Altitude',   'alt_label',   '-- ft'),
            ('Satellites', 'sat_label',   '--'),
            ('Fix Quality','fixq_label',  'No Fix'),
            ('Updated',    'upd_label',   '--:--:--'),
            ('Source',     'src_label',   'Searching'),
        ]

        for disp, attr, default in info_fields:
            data_grid.add_widget(Label(text=disp + ':', font_size='13sp',
                                       color=(0.6, 0.6, 0.6, 1), halign='right'))
            lbl = Label(text=default, font_size='13sp', bold=True,
                        color=(1, 1, 1, 1), halign='left')
            setattr(self, attr, lbl)
            data_grid.add_widget(lbl)

        content.add_widget(data_grid)
        root.add_widget(content)

        # ── Status / note strip ───────────────────────────────────────
        note = Label(
            text='🗺  Offline map tiles — coming in Phase 2  |  '
                 'Connect USB GPS receiver for real position data',
            font_size='11sp', color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None, height=22
        )
        root.add_widget(note)

        # ── Track log ─────────────────────────────────────────────────
        self.track_label = Label(
            text='Track log inactive', font_size='11sp',
            color=(0.4, 0.6, 0.4, 1), size_hint_y=None, height=20
        )
        root.add_widget(self.track_label)

        self.add_widget(root)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        logger.info("Navigation screen displayed")
        self._update_event = Clock.schedule_interval(self._refresh, self.UPDATE_HZ)
        self._refresh(0)

    def on_leave(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _refresh(self, dt):
        if not self.gps_service:
            self.fix_label.text = 'GPS service unavailable'
            return

        fix = self.gps_service.get_fix()
        if not fix:
            self.fix_label.text = 'No GPS data yet'
            return

        # Fix quality indicator
        fq_text = {0: 'No Fix', 1: '2D Fix', 2: 'Diff GPS', 3: '3D Fix'}.get(fix.fix_quality, 'Unknown')
        self.fix_label.text = f"{'[SIM]' if fix.simulated else '[GPS]'}  {fq_text}"
        self.fix_label.color = (0.3, 1.0, 0.3, 1) if fix.fix_quality >= 1 else (1, 0.5, 0, 1)

        # Coordinate labels
        lat_dir = 'N' if fix.latitude >= 0 else 'S'
        lon_dir = 'E' if fix.longitude >= 0 else 'W'
        self.lat_label.text  = f"{abs(fix.latitude):.6f}° {lat_dir}"
        self.lon_label.text  = f"{abs(fix.longitude):.6f}° {lon_dir}"
        self.spd_label.text  = f"{fix.speed_mph:.1f} mph"
        self.alt_label.text  = f"{fix.altitude_ft:.0f} ft"
        self.sat_label.text  = str(fix.satellites)
        self.fixq_label.text = fq_text
        self.upd_label.text  = fix.timestamp.strftime('%H:%M:%S')
        self.src_label.text  = 'Simulated' if fix.simulated else 'USB GPS Receiver'

        # Compass
        self.compass.set_heading(fix.heading_deg)
        direction = self.gps_service.get_heading_text()
        self.heading_label.text = f"{fix.heading_deg:.0f}°  {direction}"

        # Track log message
        self.track_label.text = (
            f"Track log: {fix.latitude:.5f}, {fix.longitude:.5f}  "
            f"— Full map tiles in Phase 2"
        )

    def handle_key(self, key, codepoint):
        return False
