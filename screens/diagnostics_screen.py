"""
Diagnostics Screen — T1000 Infotainment System
Full OBD2 dashboard with live sensor data, DTC codes,
matplotlib charts (RPM / Temp / Battery), and fuel tracking.
"""

import logging
import io
import threading
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available — charts disabled")


# ─────────────────────────────────────────────────────────────────────────────
# Helper widgets
# ─────────────────────────────────────────────────────────────────────────────

class GaugeLabel(BoxLayout):
    """A sensor value display widget: Name | Value | Unit."""
    def __init__(self, sensor_name: str, display_name: str, unit: str,
                 warn_high: float = None, crit_high: float = None, **kwargs):
        super().__init__(orientation='horizontal', spacing=4,
                         size_hint_y=None, height=36, **kwargs)
        self.sensor_name = sensor_name
        self.warn_high = warn_high
        self.crit_high = crit_high

        self.name_lbl = Label(text=display_name, font_size='13sp',
                              color=(0.7, 0.7, 0.7, 1), size_hint_x=0.45,
                              halign='right', valign='middle')
        self.name_lbl.bind(size=self.name_lbl.setter('text_size'))

        self.val_lbl = Label(text='--', font_size='16sp', bold=True,
                             color=(1, 1, 1, 1), size_hint_x=0.35,
                             halign='center', valign='middle')
        self.val_lbl.bind(size=self.val_lbl.setter('text_size'))

        self.unit_lbl = Label(text=unit, font_size='11sp',
                              color=(0.5, 0.5, 0.5, 1), size_hint_x=0.2,
                              halign='left', valign='middle')
        self.unit_lbl.bind(size=self.unit_lbl.setter('text_size'))

        self.add_widget(self.name_lbl)
        self.add_widget(self.val_lbl)
        self.add_widget(self.unit_lbl)

    def update(self, value: float):
        self.val_lbl.text = str(value)
        if self.crit_high and value >= self.crit_high:
            self.val_lbl.color = (1.0, 0.15, 0.15, 1)   # red
        elif self.warn_high and value >= self.warn_high:
            self.val_lbl.color = (1.0, 0.75, 0.0, 1)    # amber
        else:
            self.val_lbl.color = (0.3, 1.0, 0.3, 1)     # green


# ─────────────────────────────────────────────────────────────────────────────

class DiagnosticsScreen(Screen):
    """
    OBD2 diagnostics dashboard.
    Tabs:  Live Data  |  Charts  |  DTCs  |  Fuel  |  Health
    """

    CHART_UPDATE_SECS = 15   # regenerate charts every N seconds
    DATA_UPDATE_SECS  = 3    # refresh live readings every N seconds

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'diagnostics'
        self.services  = services or {}
        self.obd       = services.get('obd')    if services else None
        self.data_log  = services.get('logger') if services else None
        self.health_mon= services.get('health') if services else None

        self._data_event  = None
        self._chart_event = None

        # Gauge widgets (built during UI construction)
        self._gauges: dict[str, GaugeLabel] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=8, spacing=6)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)
        title_bar.add_widget(Label(text='OBD2 Diagnostics', font_size='20sp',
                                   bold=True, color=(0.1, 0.7, 1.0, 1)))
        self.conn_label = Label(text='●  Connecting', font_size='12sp',
                                color=(1, 0.75, 0.0, 1), size_hint_x=None, width=120)
        title_bar.add_widget(self.conn_label)
        root.add_widget(title_bar)

        # ── Alert banner ──────────────────────────────────────────────
        self.alert_label = Label(
            text='', font_size='13sp', color=(1, 0.3, 0.3, 1),
            size_hint_y=None, height=26
        )
        root.add_widget(self.alert_label)

        # ── Tabbed panel ──────────────────────────────────────────────
        tp = TabbedPanel(do_default_tab=False)
        tp.tab_width = 110

        tp.add_widget(self._build_live_tab())
        tp.add_widget(self._build_charts_tab())
        tp.add_widget(self._build_dtc_tab())
        tp.add_widget(self._build_fuel_tab())
        tp.add_widget(self._build_health_tab())

        root.add_widget(tp)
        self.add_widget(root)
        self._tabs = tp

    # ── Live Data tab ─────────────────────────────────────────────────

    def _build_live_tab(self) -> TabbedPanelItem:
        tab = TabbedPanelItem(text='Live Data')
        sv = ScrollView()
        grid = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=4)
        grid.bind(minimum_height=grid.setter('height'))

        sensors = [
            ('RPM',             'Engine RPM',         'rpm',  3500, 5000),
            ('SPEED',           'Speed',               'mph',   75,  100),
            ('COOLANT_TEMP',    'Coolant Temp',        '°F',   210,  240),
            ('BATTERY_VOLTAGE', 'Battery',             'V',   None, None),
            ('INTAKE_TEMP',     'Intake Air Temp',     '°F',   110,  140),
            ('THROTTLE_POS',    'Throttle Position',   '%',   None, None),
            ('ENGINE_LOAD',     'Engine Load',         '%',     85,  100),
            ('FUEL_PRESSURE',   'Fuel Pressure',       'psi', None, None),
            ('STFT_B1',         'Short Fuel Trim B1',  '%',     12,   20),
            ('LTFT_B1',         'Long Fuel Trim B1',   '%',     12,   20),
            ('TIMING_ADVANCE',  'Timing Advance',      '°',  None, None),
            ('O2_B1S1',         'O2 Sensor B1S1',      'V',  None, None),
            ('O2_B1S2',         'O2 Sensor B1S2',      'V',  None, None),
            ('MAF',             'Mass Air Flow',       'g/s', None, None),
        ]

        for sensor_name, disp, unit, warn, crit in sensors:
            g = GaugeLabel(sensor_name, disp, unit, warn_high=warn, crit_high=crit)
            self._gauges[sensor_name] = g
            grid.add_widget(g)

        sv.add_widget(grid)
        tab.add_widget(sv)
        return tab

    # ── Charts tab ────────────────────────────────────────────────────

    def _build_charts_tab(self) -> TabbedPanelItem:
        tab = TabbedPanelItem(text='Charts')
        box = BoxLayout(orientation='vertical', spacing=4, padding=4)

        box.add_widget(Label(text='Live Sensor Charts (last 5 min)',
                             font_size='13sp', color=(0.7, 0.7, 0.7, 1),
                             size_hint_y=None, height=24))

        self.chart_image = KivyImage(allow_stretch=True, keep_ratio=True)
        box.add_widget(self.chart_image)

        refresh_btn = Button(text='↻ Refresh Charts', size_hint_y=None, height=40,
                             background_color=(0.2, 0.4, 0.6, 1), font_size='13sp')
        refresh_btn.bind(on_press=lambda x: self._generate_charts())
        box.add_widget(refresh_btn)

        tab.add_widget(box)
        return tab

    # ── DTC tab ───────────────────────────────────────────────────────

    def _build_dtc_tab(self) -> TabbedPanelItem:
        tab = TabbedPanelItem(text='DTCs')
        box = BoxLayout(orientation='vertical', spacing=6, padding=8)

        ctrl_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        ctrl_row.add_widget(Button(text='↻ Refresh', font_size='13sp',
                                   background_color=(0.2, 0.4, 0.6, 1),
                                   on_press=lambda x: self._refresh_dtcs()))
        ctrl_row.add_widget(Button(text='🗑 Clear DTCs', font_size='13sp',
                                   background_color=(0.6, 0.15, 0.15, 1),
                                   on_press=lambda x: self._clear_dtcs()))
        box.add_widget(ctrl_row)

        self.dtc_scroll = ScrollView()
        self.dtc_grid = GridLayout(cols=1, spacing=4, size_hint_y=None, padding=4)
        self.dtc_grid.bind(minimum_height=self.dtc_grid.setter('height'))
        self.dtc_scroll.add_widget(self.dtc_grid)
        box.add_widget(self.dtc_scroll)

        tab.add_widget(box)
        return tab

    # ── Fuel tab ──────────────────────────────────────────────────────

    def _build_fuel_tab(self) -> TabbedPanelItem:
        tab = TabbedPanelItem(text='Fuel')
        box = BoxLayout(orientation='vertical', spacing=8, padding=12)

        box.add_widget(Label(text='Fuel Economy Tracking', font_size='16sp',
                             bold=True, color=(1, 0.7, 0.1, 1),
                             size_hint_y=None, height=30))

        self.mpg_label = Label(text='Average MPG: calculating...', font_size='20sp',
                               color=(0.3, 1, 0.3, 1), size_hint_y=None, height=40)
        box.add_widget(self.mpg_label)

        self.fillup_label = Label(text='Fillup history will appear here',
                                  font_size='13sp', color=(0.7, 0.7, 0.7, 1))
        box.add_widget(self.fillup_label)

        # Fillup entry row
        box.add_widget(Label(text='Log Fillup:', font_size='14sp', bold=True,
                             color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=28))

        entry_row = BoxLayout(size_hint_y=None, height=44, spacing=8)

        from kivy.uix.textinput import TextInput
        self.odo_input = TextInput(hint_text='Odometer (mi)', multiline=False,
                                   input_filter='float', size_hint_x=0.35,
                                   font_size='14sp')
        self.gal_input = TextInput(hint_text='Gallons', multiline=False,
                                   input_filter='float', size_hint_x=0.25,
                                   font_size='14sp')
        log_btn = Button(text='Log Fillup', font_size='13sp',
                         background_color=(0.6, 0.4, 0.1, 1))
        log_btn.bind(on_press=self._log_fillup)

        entry_row.add_widget(self.odo_input)
        entry_row.add_widget(self.gal_input)
        entry_row.add_widget(log_btn)
        box.add_widget(entry_row)

        tab.add_widget(box)
        return tab

    # ── Health tab ────────────────────────────────────────────────────

    def _build_health_tab(self) -> TabbedPanelItem:
        tab = TabbedPanelItem(text='Health')
        box = BoxLayout(orientation='vertical', spacing=6, padding=10)

        self.health_score_label = Label(
            text='Health Score: --', font_size='22sp', bold=True,
            color=(0.3, 1.0, 0.3, 1), size_hint_y=None, height=42
        )
        box.add_widget(self.health_score_label)

        self.health_pi_label = Label(
            text='Pi CPU: --%   RAM: --%   Temp: --°C   Disk: --%',
            font_size='13sp', color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None, height=28
        )
        box.add_widget(self.health_pi_label)

        self.health_alerts_label = Label(
            text='No alerts', font_size='13sp', color=(0.7, 0.9, 0.7, 1)
        )
        box.add_widget(self.health_alerts_label)

        tab.add_widget(box)
        return tab

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        logger.info("Diagnostics screen displayed")
        self._data_event  = Clock.schedule_interval(self._refresh_live,   self.DATA_UPDATE_SECS)
        self._chart_event = Clock.schedule_interval(self._generate_charts, self.CHART_UPDATE_SECS)
        self._refresh_live(0)
        self._generate_charts(0)
        self._refresh_dtcs()
        self._refresh_fuel()
        self._refresh_health()

    def on_leave(self):
        if self._data_event:
            self._data_event.cancel()
            self._data_event = None
        if self._chart_event:
            self._chart_event.cancel()
            self._chart_event = None

    # ------------------------------------------------------------------
    # Live data refresh
    # ------------------------------------------------------------------

    def _refresh_live(self, dt):
        if not self.obd:
            return

        # Update connection indicator
        if self.obd.connected:
            self.conn_label.text = '●  Live'
            self.conn_label.color = (0.3, 1.0, 0.3, 1)
        else:
            self.conn_label.text = '●  Simulated'
            self.conn_label.color = (1.0, 0.75, 0.0, 1)

        # Update all gauge widgets
        readings = self.obd.get_all_readings()
        for sensor_name, gauge in self._gauges.items():
            r = readings.get(sensor_name)
            if r:
                gauge.update(r.value)

        # Alert banner — DTCs
        if self.obd.active_dtcs:
            codes = ', '.join(self.obd.active_dtcs)
            self.alert_label.text = f'⚠ Check Engine: {codes}'
        else:
            self.alert_label.text = ''

        self._refresh_health()

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def _generate_charts(self, dt=None):
        """Generate matplotlib charts in a background thread, then update UI."""
        if not MATPLOTLIB_AVAILABLE or not self.obd:
            return
        threading.Thread(target=self._chart_worker, daemon=True).start()

    def _chart_worker(self):
        try:
            fig, axes = plt.subplots(2, 2, figsize=(9, 4.5),
                                     facecolor='#1a1a2e', tight_layout=True)
            plt.rcParams.update({
                'axes.facecolor': '#16213e',
                'axes.labelcolor': '#cccccc',
                'xtick.color':    '#888888',
                'ytick.color':    '#888888',
                'grid.color':     '#333355',
            })

            chart_cfg = [
                ('RPM',            'Engine RPM',     '#00bfff', 'rpm',  (axes[0][0], 0,  5500)),
                ('SPEED',          'Speed',           '#00ff88', 'mph',  (axes[0][1], 0,  80)),
                ('COOLANT_TEMP',   'Coolant Temp',    '#ff6040', '°F',   (axes[1][0], 140, 240)),
                ('BATTERY_VOLTAGE','Battery Voltage', '#ffcc00', 'V',    (axes[1][1], 11.5, 15.5)),
            ]

            for sensor, title, color, unit, (ax, ymin, ymax) in chart_cfg:
                timestamps, values = self.obd.get_chart_data(sensor)

                ax.set_facecolor('#16213e')
                ax.set_title(title, color='#dddddd', fontsize=9, pad=3)
                ax.set_ylabel(unit, color='#888888', fontsize=8)
                ax.set_ylim(ymin, ymax)
                ax.grid(True, alpha=0.3)
                ax.spines['bottom'].set_color('#333355')
                ax.spines['left'].set_color('#333355')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.tick_params(labelsize=7)

                if values:
                    x = list(range(len(values)))
                    ax.plot(x, values, color=color, linewidth=1.5, solid_capstyle='round')
                    ax.fill_between(x, ymin, values, color=color, alpha=0.15)
                    # Current value annotation
                    ax.annotate(f'{values[-1]:.1f}', xy=(x[-1], values[-1]),
                                color=color, fontsize=9, fontweight='bold',
                                xytext=(-30, 6), textcoords='offset points')
                else:
                    ax.text(0.5, 0.5, 'Collecting data...', transform=ax.transAxes,
                            color='#666666', ha='center', va='center', fontsize=8)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=90, bbox_inches='tight',
                        facecolor='#1a1a2e')
            buf.seek(0)
            plt.close(fig)

            # Update texture on main thread
            Clock.schedule_once(lambda dt: self._set_chart_texture(buf))

        except Exception as e:
            logger.error(f"Chart generation error: {e}")

    def _set_chart_texture(self, buf):
        try:
            core_img = CoreImage(buf, ext='png')
            self.chart_image.texture = core_img.texture
        except Exception as e:
            logger.debug(f"Chart texture update error: {e}")

    # ------------------------------------------------------------------
    # DTC panel
    # ------------------------------------------------------------------

    def _refresh_dtcs(self, *_):
        self.dtc_grid.clear_widgets()
        if not self.obd:
            self.dtc_grid.add_widget(Label(
                text='OBD service not available', font_size='14sp',
                color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=30
            ))
            return

        dtcs = self.obd.get_dtcs()
        if not dtcs:
            self.dtc_grid.add_widget(Label(
                text='✔  No active trouble codes', font_size='15sp',
                color=(0.3, 1.0, 0.3, 1), size_hint_y=None, height=32
            ))
            return

        sev_colors = {'critical': (1, 0.2, 0.2, 1), 'warning': (1, 0.75, 0, 1), 'info': (0.5, 0.8, 1, 1)}

        for code, info in dtcs.items():
            color = sev_colors.get(info['severity'], (0.8, 0.8, 0.8, 1))
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=68,
                            padding=[6, 4])
            title = Label(text=f"[b]{code}[/b] — {info['title']}", markup=True,
                          font_size='13sp', color=color, halign='left',
                          size_hint_y=None, height=28)
            title.bind(size=title.setter('text_size'))
            desc = Label(text=info['description'], font_size='11sp',
                         color=(0.75, 0.75, 0.75, 1), halign='left',
                         size_hint_y=None, height=36)
            desc.bind(size=desc.setter('text_size'))
            box.add_widget(title)
            box.add_widget(desc)
            self.dtc_grid.add_widget(box)

    def _clear_dtcs(self, *_):
        if self.obd:
            self.obd.clear_dtcs()
            self._refresh_dtcs()

    # ------------------------------------------------------------------
    # Fuel panel
    # ------------------------------------------------------------------

    def _refresh_fuel(self, *_):
        if not self.data_log:
            self.mpg_label.text = 'Data logger not available'
            return

        mpg = self.data_log.get_fuel_economy()
        self.mpg_label.text = f"Average MPG: {mpg:.1f}" if mpg else "Average MPG: (need 2+ fillups)"

        fillups = self.data_log.fuel_fillups[-5:]  # last 5
        if fillups:
            lines = [f"{f.timestamp[:10]}  {f.gallons:.1f} gal @ {f.odometer_miles:.0f} mi"
                     for f in fillups]
            self.fillup_label.text = '\n'.join(reversed(lines))

    def _log_fillup(self, *_):
        if not self.data_log:
            return
        try:
            odo = float(self.odo_input.text)
            gal = float(self.gal_input.text)
            self.data_log.log_fuel_fillup(odometer=odo, gallons=gal)
            self.odo_input.text = ''
            self.gal_input.text = ''
            self._refresh_fuel()
        except ValueError:
            self.fillup_label.text = 'Enter valid odometer and gallons values'

    # ------------------------------------------------------------------
    # Health panel
    # ------------------------------------------------------------------

    def _refresh_health(self, *_):
        score_color = (0.3, 1.0, 0.3, 1)

        if self.health_mon:
            score = self.health_mon.get_overall_score()
            if score < 50:   score_color = (1.0, 0.2, 0.2, 1)
            elif score < 75: score_color = (1.0, 0.75, 0.0, 1)

            self.health_score_label.text = f'Overall Health Score: {score}/100'
            self.health_score_label.color = score_color

            s = self.health_mon.get_system_health()
            temp_str = f"{s.cpu_temp_c:.1f}°C" if s.cpu_temp_c else "N/A"
            self.health_pi_label.text = (
                f"CPU: {s.cpu_percent:.1f}%   RAM: {s.ram_percent:.1f}%   "
                f"Pi Temp: {temp_str}   Disk: {s.disk_percent:.1f}%"
            )

            alerts = self.health_mon.get_alerts()
            if alerts:
                self.health_alerts_label.text = '\n'.join(f'⚠ {a}' for a in alerts)
                self.health_alerts_label.color = (1.0, 0.5, 0.2, 1)
            else:
                self.health_alerts_label.text = '✔  All systems healthy'
                self.health_alerts_label.color = (0.3, 1.0, 0.3, 1)

        elif self.obd:
            h = self.obd.get_health_summary()
            score = h.get('score', 0)
            if score < 50:   score_color = (1.0, 0.2, 0.2, 1)
            elif score < 75: score_color = (1.0, 0.75, 0.0, 1)
            self.health_score_label.text = f'Engine Health Score: {score}/100'
            self.health_score_label.color = score_color
            issues = h.get('issues', [])
            self.health_alerts_label.text = '\n'.join(issues) if issues else '✔  No engine issues'

    # ------------------------------------------------------------------
    # Keyboard forwarding
    # ------------------------------------------------------------------

    def handle_key(self, key, codepoint):
        return False  # diagnostics screen consumes no special keys
