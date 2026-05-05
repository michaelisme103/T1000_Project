"""
Health Screen — T1000 Infotainment System
Dedicated system health dashboard combining Pi hardware metrics
and OBD2 engine vitals with live matplotlib charts.
"""

import logging
import io
import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class MeterWidget(BoxLayout):
    """Horizontal bar meter: label | progressbar | value."""
    def __init__(self, title: str, max_val: float, warn: float, crit: float, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=34, spacing=6, **kwargs)
        self.warn = warn
        self.crit = crit
        self.max_val = max_val

        self.add_widget(Label(text=title, font_size='12sp',
                              color=(0.7, 0.7, 0.7, 1), size_hint_x=0.28,
                              halign='right', valign='middle'))
        self.bar = ProgressBar(max=max_val, value=0, size_hint_x=0.52)
        self.add_widget(self.bar)
        self.val_lbl = Label(text='--', font_size='12sp', bold=True,
                             color=(0.3, 1, 0.3, 1), size_hint_x=0.20)
        self.add_widget(self.val_lbl)

    def update(self, value: float, suffix: str = ''):
        self.bar.value = min(value, self.max_val)
        self.val_lbl.text = f"{value:.1f}{suffix}"
        if value >= self.crit:
            self.val_lbl.color = (1.0, 0.2, 0.2, 1)
        elif value >= self.warn:
            self.val_lbl.color = (1.0, 0.75, 0.0, 1)
        else:
            self.val_lbl.color = (0.3, 1.0, 0.3, 1)


class HealthScreen(Screen):
    """Dedicated health monitoring screen."""

    CHART_INTERVAL = 20
    DATA_INTERVAL  = 3

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'health'
        self.services   = services or {}
        self.health_mon = services.get('health') if services else None
        self.obd        = services.get('obd')    if services else None

        self._data_event  = None
        self._chart_event = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=6)

        # ── Title ─────────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)
        title_bar.add_widget(Label(text='System Health', font_size='20sp',
                                   bold=True, color=(0.1, 0.7, 1.0, 1)))
        self.score_badge = Label(text='Score: --', font_size='14sp', bold=True,
                                 color=(0.3, 1.0, 0.3, 1), size_hint_x=None, width=100)
        title_bar.add_widget(self.score_badge)
        root.add_widget(title_bar)

        # ── Body split ────────────────────────────────────────────────
        body = BoxLayout(spacing=10)

        # Left column — meters
        left = BoxLayout(orientation='vertical', size_hint_x=0.38, spacing=4)
        left.add_widget(Label(text='[b]Pi Hardware[/b]', markup=True, font_size='13sp',
                              color=(0.4, 0.8, 1.0, 1), size_hint_y=None, height=24))

        self.cpu_meter  = MeterWidget('CPU',      100, 75, 90)
        self.ram_meter  = MeterWidget('RAM',      100, 75, 90)
        self.temp_meter = MeterWidget('Pi Temp°C', 100, 70, 80)
        self.disk_meter = MeterWidget('Disk',     100, 80, 95)

        for m in (self.cpu_meter, self.ram_meter, self.temp_meter, self.disk_meter):
            left.add_widget(m)

        left.add_widget(Label(text='[b]Engine[/b]', markup=True, font_size='13sp',
                              color=(0.4, 0.8, 1.0, 1), size_hint_y=None, height=24))

        self.eng_temp_meter = MeterWidget('Coolant °F', 260, 210, 230)
        self.volt_meter     = MeterWidget('Battery V',   16,  13.5, 15)
        self.rpm_meter      = MeterWidget('RPM×100',     60,  45,   55)

        for m in (self.eng_temp_meter, self.volt_meter, self.rpm_meter):
            left.add_widget(m)

        body.add_widget(left)

        # Right column — chart + alerts
        right = BoxLayout(orientation='vertical', size_hint_x=0.62, spacing=6)

        self.chart_image = KivyImage(allow_stretch=True, keep_ratio=True,
                                     size_hint_y=0.65)
        right.add_widget(self.chart_image)

        right.add_widget(Label(text='Alerts:', font_size='12sp',
                               color=(0.6, 0.6, 0.6, 1),
                               size_hint_y=None, height=20))
        sv = ScrollView(size_hint_y=0.35)
        self.alerts_label = Label(
            text='No alerts', font_size='12sp',
            color=(0.3, 1.0, 0.3, 1), halign='left', valign='top',
            size_hint_y=None
        )
        self.alerts_label.bind(texture_size=self.alerts_label.setter('size'))
        sv.add_widget(self.alerts_label)
        right.add_widget(sv)

        body.add_widget(right)
        root.add_widget(body)

        self.uptime_label = Label(
            text='Uptime: --', font_size='11sp', color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None, height=20
        )
        root.add_widget(self.uptime_label)

        self.add_widget(root)

    # ------------------------------------------------------------------
    def on_enter(self):
        logger.info("Health screen displayed")
        self._data_event  = Clock.schedule_interval(self._refresh, self.DATA_INTERVAL)
        self._chart_event = Clock.schedule_interval(self._gen_chart, self.CHART_INTERVAL)
        self._refresh(0)
        self._gen_chart(0)

    def on_leave(self):
        for ev in (self._data_event, self._chart_event):
            if ev:
                ev.cancel()
        self._data_event = self._chart_event = None

    # ------------------------------------------------------------------
    def _refresh(self, dt):
        # Pi metrics
        if self.health_mon:
            s = self.health_mon.get_system_health()
            self.cpu_meter.update(s.cpu_percent, '%')
            self.ram_meter.update(s.ram_percent, '%')
            self.temp_meter.update(s.cpu_temp_c or 0, '°C')
            self.disk_meter.update(s.disk_percent, '%')

            score = self.health_mon.get_overall_score()
            self.score_badge.text = f"Score: {score}"
            self.score_badge.color = (
                (1.0, 0.2, 0.2, 1) if score < 50 else
                (1.0, 0.75, 0.0, 1) if score < 75 else
                (0.3, 1.0, 0.3, 1)
            )

            alerts = self.health_mon.get_alerts()
            self.alerts_label.text = ('\n'.join(f'⚠ {a}' for a in alerts)
                                      if alerts else '✔  All healthy')
            self.alerts_label.color = (1.0, 0.5, 0.2, 1) if alerts else (0.3, 1.0, 0.3, 1)
            self.uptime_label.text = f"Uptime: {self.health_mon.get_uptime_str()}"

        # Engine metrics
        if self.obd:
            r = self.obd.get_reading('COOLANT_TEMP')
            if r: self.eng_temp_meter.update(r.value, '°F')
            v = self.obd.get_reading('BATTERY_VOLTAGE')
            if v: self.volt_meter.update(v.value, 'V')
            rpm = self.obd.get_reading('RPM')
            if rpm: self.rpm_meter.update(rpm.value / 100, 'x100')

    def _gen_chart(self, dt=None):
        if not MATPLOTLIB_AVAILABLE:
            return
        threading.Thread(target=self._chart_worker, daemon=True).start()

    def _chart_worker(self):
        try:
            fig, axes = plt.subplots(1, 3, figsize=(9, 2.8),
                                     facecolor='#1a1a2e', tight_layout=True)
            cfg = []

            if self.health_mon:
                ts, cpu  = self.health_mon.get_chart_data('cpu')
                ts, ram  = self.health_mon.get_chart_data('ram')
                ts, temp = self.health_mon.get_chart_data('temp')
                cfg = [
                    (axes[0], cpu,  'CPU %',     '#00bfff', 0, 100),
                    (axes[1], ram,  'RAM %',     '#00ff88', 0, 100),
                    (axes[2], temp, 'Pi Temp°C', '#ff6040', 30, 90),
                ]

            for ax, data, title, color, ymin, ymax in cfg:
                ax.set_facecolor('#16213e')
                ax.set_title(title, color='#dddddd', fontsize=9)
                ax.set_ylim(ymin, ymax)
                ax.grid(True, alpha=0.3, color='#334')
                ax.spines[:].set_visible(False)
                ax.tick_params(colors='#888', labelsize=7)
                if data:
                    x = list(range(len(data)))
                    ax.plot(x, data, color=color, lw=1.5)
                    ax.fill_between(x, ymin, data, color=color, alpha=0.18)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=90, facecolor='#1a1a2e',
                        bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            Clock.schedule_once(lambda dt: self._set_chart(buf))
        except Exception as e:
            logger.error(f"Health chart error: {e}")

    def _set_chart(self, buf):
        try:
            self.chart_image.texture = CoreImage(buf, ext='png').texture
        except Exception as e:
            logger.debug(f"Health chart texture error: {e}")

    def handle_key(self, key, codepoint):
        return False
