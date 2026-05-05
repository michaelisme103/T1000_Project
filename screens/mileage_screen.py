"""
Mileage Screen — T1000 Infotainment System
Work vs personal trip logging with live GPS distance tracking.
"""

import logging
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

logger = logging.getLogger(__name__)

_WORK_CLR     = (0.10, 0.45, 0.80, 1)
_PERSONAL_CLR = (0.15, 0.60, 0.30, 1)
_IDLE_CLR     = (0.22, 0.22, 0.22, 1)
_LOG_CLR      = (0.55, 0.13, 0.13, 1)
_LOG_ACTIVE   = (0.80, 0.18, 0.18, 1)


class _RoundBtn(Button):
    def __init__(self, bg_color, **kwargs):
        super().__init__(**kwargs)
        self._bg = bg_color
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def set_color(self, color):
        self._bg = color
        self._draw()


class MileageScreen(Screen):
    """Work / Personal mileage tracker screen."""

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'mileage'
        self.services = services or {}
        self.tracker  = services.get('mileage') if services else None
        self._update_event = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=14, spacing=10)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back = Button(text='← Home', size_hint_x=None, width=90,
                      background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back)
        title_bar.add_widget(Label(text='Mileage Tracker', font_size='20sp',
                                   bold=True, color=(0.1, 0.7, 1.0, 1)))
        self.status_pill = Label(text='● Idle', font_size='13sp',
                                 color=(0.5, 0.5, 0.5, 1),
                                 size_hint_x=None, width=100)
        title_bar.add_widget(self.status_pill)
        root.add_widget(title_bar)

        # ── Live trip display ──────────────────────────────────────────
        live = BoxLayout(orientation='vertical', size_hint_y=0.28, spacing=2)

        self.type_lbl = Label(text='NO ACTIVE TRIP', font_size='26sp',
                              bold=True, color=(0.35, 0.35, 0.35, 1))
        self.dist_lbl = Label(text='0.00 mi', font_size='42sp',
                              bold=True, color=(1, 1, 1, 1))
        self.time_lbl = Label(text='--:--', font_size='18sp',
                              color=(0.65, 0.65, 0.65, 1))

        live.add_widget(self.type_lbl)
        live.add_widget(self.dist_lbl)
        live.add_widget(self.time_lbl)
        root.add_widget(live)

        # ── Start buttons ──────────────────────────────────────────────
        btn_row = BoxLayout(size_hint_y=None, height=68, spacing=12)

        self.work_btn = _RoundBtn(bg_color=_WORK_CLR,
                                  text='🏢  Work Trip',
                                  font_size='17sp', bold=True)
        self.work_btn.bind(on_press=lambda x: self._start('work'))

        self.personal_btn = _RoundBtn(bg_color=_PERSONAL_CLR,
                                      text='🏠  Personal Trip',
                                      font_size='17sp', bold=True)
        self.personal_btn.bind(on_press=lambda x: self._start('personal'))

        btn_row.add_widget(self.work_btn)
        btn_row.add_widget(self.personal_btn)
        root.add_widget(btn_row)

        # ── Log Trip button ────────────────────────────────────────────
        self.log_btn = _RoundBtn(bg_color=_LOG_CLR,
                                 text='✓  Log Trip',
                                 font_size='18sp', bold=True,
                                 size_hint_y=None, height=60)
        self.log_btn.bind(on_press=lambda x: self._log_trip())
        root.add_widget(self.log_btn)

        # ── Monthly totals strip ───────────────────────────────────────
        totals = BoxLayout(size_hint_y=None, height=40, spacing=16)
        self.work_total   = Label(text='Work this month: -- mi',
                                  font_size='13sp', bold=True,
                                  color=(0.4, 0.7, 1.0, 1))
        self.pers_total   = Label(text='Personal this month: -- mi',
                                  font_size='13sp', bold=True,
                                  color=(0.3, 1.0, 0.55, 1))
        totals.add_widget(self.work_total)
        totals.add_widget(self.pers_total)
        root.add_widget(totals)

        # ── Recent trips list ──────────────────────────────────────────
        root.add_widget(Label(
            text='Recent Trips', font_size='12sp',
            color=(0.45, 0.45, 0.45, 1),
            size_hint_y=None, height=20, halign='left'
        ))

        sv = ScrollView()
        self.trips_grid = GridLayout(cols=1, spacing=2,
                                     size_hint_y=None, padding=[0, 2])
        self.trips_grid.bind(minimum_height=self.trips_grid.setter('height'))
        sv.add_widget(self.trips_grid)
        root.add_widget(sv)

        # ── Feedback strip ─────────────────────────────────────────────
        self.feedback = Label(text='', font_size='12sp',
                              color=(0.3, 1.0, 0.3, 1),
                              size_hint_y=None, height=22)
        root.add_widget(self.feedback)

        self.add_widget(root)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        logger.info("Mileage screen displayed")
        self._update_event = Clock.schedule_interval(self._refresh, 1.0)
        self._refresh(0)

    def on_leave(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def _refresh(self, dt):
        try:
            if not self.tracker:
                self.type_lbl.text = '✕ Mileage service unavailable'
                self.type_lbl.color = (1.0, 0.3, 0.3, 1)
                return

            if self.tracker.is_tracking():
                ttype = self.tracker.get_trip_type()
                if ttype == 'work':
                    self.type_lbl.text  = '🏢  WORK TRIP'
                    self.type_lbl.color = (0.4, 0.75, 1.0, 1)
                    self.status_pill.text  = '● Work'
                    self.status_pill.color = (0.4, 0.75, 1.0, 1)
                    self.work_btn.set_color((0.08, 0.35, 0.65, 1))   # dimmed
                    self.personal_btn.set_color(_PERSONAL_CLR)
                else:
                    self.type_lbl.text  = '🏠  PERSONAL TRIP'
                    self.type_lbl.color = (0.3, 1.0, 0.55, 1)
                    self.status_pill.text  = '● Personal'
                    self.status_pill.color = (0.3, 1.0, 0.55, 1)
                    self.personal_btn.set_color((0.10, 0.45, 0.22, 1))
                    self.work_btn.set_color(_WORK_CLR)

                self.dist_lbl.text = f"{self.tracker.get_current_distance():.2f} mi"
                self.time_lbl.text = self.tracker.get_elapsed()
                self.log_btn.set_color(_LOG_ACTIVE)
            else:
                self.type_lbl.text  = 'NO ACTIVE TRIP'
                self.type_lbl.color = (0.35, 0.35, 0.35, 1)
                self.dist_lbl.text  = '0.00 mi'
                self.time_lbl.text  = '--:--'
                self.status_pill.text  = '● Idle'
                self.status_pill.color = (0.5, 0.5, 0.5, 1)
                self.work_btn.set_color(_WORK_CLR)
                self.personal_btn.set_color(_PERSONAL_CLR)
                self.log_btn.set_color(_LOG_CLR)

            t = self.tracker.get_monthly_totals()
            self.work_total.text = f"Work this month: {t['work']:.1f} mi"
            self.pers_total.text = f"Personal this month: {t['personal']:.1f} mi"

            self._refresh_trips()

        except Exception as e:
            logger.error(f"Mileage screen refresh error: {e}")

    def _refresh_trips(self):
        self.trips_grid.clear_widgets()
        trips = self.tracker.get_recent_trips(8) if self.tracker else []
        if not trips:
            self.trips_grid.add_widget(Label(
                text='No trips saved yet — start a trip above',
                font_size='12sp', color=(0.4, 0.4, 0.4, 1),
                size_hint_y=None, height=28
            ))
            return
        for t in trips:
            ttype = t.get('trip_type', '?')
            dist  = float(t.get('distance_miles', 0))
            dur   = float(t.get('duration_minutes', 0))
            dt_s  = t.get('start_time', '')[:16].replace('T', ' ')
            color = (0.4, 0.75, 1.0, 1) if ttype == 'work' else (0.3, 1.0, 0.55, 1)
            icon  = '🏢' if ttype == 'work' else '🏠'
            lbl = Label(
                text=f"{icon} {ttype.capitalize():10s}  {dist:6.2f} mi   "
                     f"{int(dur):3d} min   {dt_s}",
                font_size='12sp', color=color,
                size_hint_y=None, height=28, halign='left'
            )
            lbl.bind(size=lbl.setter('text_size'))
            self.trips_grid.add_widget(lbl)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start(self, trip_type: str):
        if not self.tracker:
            return
        self.tracker.start_trip(trip_type)
        label = 'Work' if trip_type == 'work' else 'Personal'
        self.feedback.text  = f"{label} trip started — drive safely!"
        self.feedback.color = (0.3, 1.0, 0.3, 1)

    def _log_trip(self):
        if not self.tracker:
            return
        if not self.tracker.is_tracking():
            self.feedback.text  = 'No active trip — press Work or Personal to start'
            self.feedback.color = (1.0, 0.6, 0.2, 1)
            return
        trip = self.tracker.end_trip()
        if trip:
            self.feedback.text = (
                f"✔  {trip.trip_type.capitalize()} trip saved — "
                f"{trip.distance_miles:.2f} mi in {trip.duration_minutes:.0f} min"
            )
            self.feedback.color = (0.3, 1.0, 0.3, 1)
        else:
            self.feedback.text  = '✘ Could not save trip'
            self.feedback.color = (1.0, 0.3, 0.3, 1)

    def handle_key(self, key, codepoint):
        return False
