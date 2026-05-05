"""
Music Screen — T1000 Infotainment System
Controls Spotify (via iPad aux) or MPD local playback.
"""

import logging
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle

logger = logging.getLogger(__name__)


class MusicScreen(Screen):
    """Music player control screen."""

    def __init__(self, services: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.name = 'music'
        self.services = services or {}
        self.audio_service = services.get('audio') if services else None
        self._update_event = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=12, spacing=8)

        # ── Title bar ─────────────────────────────────────────────────
        title_bar = BoxLayout(size_hint_y=None, height=44, spacing=8)
        back_btn = Button(text='← Home', size_hint_x=None, width=90,
                          background_color=(0.3, 0.3, 0.3, 1), font_size='14sp')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        title_bar.add_widget(back_btn)
        title_bar.add_widget(Label(text='Music Player', font_size='20sp', bold=True,
                                   color=(0.1, 0.7, 1.0, 1)))
        self.mode_label = Label(text='Spotify/iPad', font_size='12sp',
                                color=(0.6, 0.9, 0.6, 1), size_hint_x=None, width=100)
        title_bar.add_widget(self.mode_label)
        root.add_widget(title_bar)

        # ── Now playing ───────────────────────────────────────────────
        now_playing = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=4,
                                padding=[16, 8])
        self.track_label = Label(
            text='[No track info]', font_size='18sp', bold=True,
            color=(1, 1, 1, 1), text_size=(None, None), halign='center'
        )
        self.artist_label = Label(
            text='Connect iPad via aux or enable MPD', font_size='14sp',
            color=(0.7, 0.7, 0.7, 1), halign='center'
        )
        self.album_label = Label(
            text='', font_size='12sp', color=(0.5, 0.5, 0.5, 1), halign='center'
        )
        now_playing.add_widget(self.track_label)
        now_playing.add_widget(self.artist_label)
        now_playing.add_widget(self.album_label)
        root.add_widget(now_playing)

        # ── Volume bar ────────────────────────────────────────────────
        vol_box = BoxLayout(size_hint_y=None, height=48, spacing=8)

        vol_dn = Button(text='🔉', size_hint_x=None, width=50,
                        background_color=(0.2, 0.2, 0.2, 1), font_size='18sp')
        vol_dn.bind(on_press=lambda x: self._change_volume(-5))
        vol_box.add_widget(vol_dn)

        self.volume_bar = ProgressBar(max=100, value=50)
        vol_box.add_widget(self.volume_bar)

        vol_up = Button(text='🔊', size_hint_x=None, width=50,
                        background_color=(0.2, 0.2, 0.2, 1), font_size='18sp')
        vol_up.bind(on_press=lambda x: self._change_volume(5))
        vol_box.add_widget(vol_up)

        self.volume_label = Label(text='50%', size_hint_x=None, width=50,
                                  font_size='14sp', color=(0.8, 0.8, 0.8, 1))
        vol_box.add_widget(self.volume_label)

        root.add_widget(vol_box)

        # ── Playback controls ─────────────────────────────────────────
        ctrl = BoxLayout(size_hint_y=None, height=64, spacing=10)

        self.prev_btn = Button(text='⏮ Prev\n[←]',
                               background_color=(0.15, 0.45, 0.75, 1), font_size='14sp')
        self.prev_btn.bind(on_press=lambda x: self._previous())
        ctrl.add_widget(self.prev_btn)

        self.play_btn = Button(text='▶ Play\n[Space]',
                               background_color=(0.15, 0.65, 0.25, 1), font_size='15sp')
        self.play_btn.bind(on_press=lambda x: self._toggle_play())
        ctrl.add_widget(self.play_btn)

        self.next_btn = Button(text='Next ⏭\n[→]',
                               background_color=(0.15, 0.45, 0.75, 1), font_size='14sp')
        self.next_btn.bind(on_press=lambda x: self._next())
        ctrl.add_widget(self.next_btn)

        root.add_widget(ctrl)

        # ── Source toggle ─────────────────────────────────────────────
        src_row = BoxLayout(size_hint_y=None, height=44, spacing=10)
        src_row.add_widget(Label(text='Source:', size_hint_x=None, width=70,
                                 font_size='13sp', color=(0.7, 0.7, 0.7, 1)))

        self.spotify_btn = Button(text='Spotify/iPad',
                                  background_color=(0.10, 0.55, 0.25, 1), font_size='13sp')
        self.spotify_btn.bind(on_press=lambda x: self._set_mode('spotify'))
        src_row.add_widget(self.spotify_btn)

        self.mpd_btn = Button(text='Local MPD',
                              background_color=(0.25, 0.25, 0.25, 1), font_size='13sp')
        self.mpd_btn.bind(on_press=lambda x: self._set_mode('mpd'))
        src_row.add_widget(self.mpd_btn)

        root.add_widget(src_row)

        # ── Status ────────────────────────────────────────────────────
        self.status_label = Label(
            text='Ready', font_size='11sp', color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None, height=22
        )
        root.add_widget(self.status_label)

        self.add_widget(root)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self):
        logger.info("Music screen displayed")
        self._update_event = Clock.schedule_interval(self._refresh_ui, 2.0)
        self._refresh_ui(0)

    def on_leave(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    # ------------------------------------------------------------------
    # UI refresh
    # ------------------------------------------------------------------

    def _refresh_ui(self, dt):
        if not self.audio_service:
            self.status_label.text = 'Audio service not available'
            return

        info = self.audio_service.get_current_track_info()
        status = self.audio_service.get_status()

        self.track_label.text  = info.get('track', '--') or '--'
        self.artist_label.text = info.get('artist', '') or ''
        self.album_label.text  = info.get('album', '') or ''
        self.mode_label.text   = info.get('mode', '')

        vol = self.audio_service.get_volume()
        self.volume_bar.value = vol
        self.volume_label.text = f"{vol}%"

        playing = status.get('is_playing', False)
        self.play_btn.text = '⏸ Pause\n[Space]' if playing else '▶ Play\n[Space]'
        self.play_btn.background_color = (0.75, 0.65, 0.10, 1) if playing else (0.15, 0.65, 0.25, 1)

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _toggle_play(self):
        if self.audio_service:
            self.audio_service.toggle_play()
        self._refresh_ui(0)

    def _next(self):
        if self.audio_service:
            self.audio_service.next()
        self.status_label.text = 'Next track →'
        self._refresh_ui(0)

    def _previous(self):
        if self.audio_service:
            self.audio_service.previous()
        self.status_label.text = '← Previous track'
        self._refresh_ui(0)

    def _change_volume(self, delta: int):
        if self.audio_service:
            new_vol = max(0, min(100, self.audio_service.get_volume() + delta))
            self.audio_service.set_volume(new_vol)
        self._refresh_ui(0)

    def _set_mode(self, mode: str):
        if not self.audio_service:
            return
        from services.audio_service import PlaybackMode
        if mode == 'spotify':
            self.audio_service.set_mode(PlaybackMode.SPOTIFY_IPAD)
            self.spotify_btn.background_color = (0.10, 0.55, 0.25, 1)
            self.mpd_btn.background_color = (0.25, 0.25, 0.25, 1)
            self.status_label.text = 'Switched to Spotify/iPad mode'
        else:
            ok = self.audio_service.set_mode(PlaybackMode.MPD_LOCAL)
            if ok:
                self.mpd_btn.background_color = (0.10, 0.45, 0.25, 1)
                self.spotify_btn.background_color = (0.25, 0.25, 0.25, 1)
                self.status_label.text = 'Switched to Local MPD'
            else:
                self.status_label.text = 'MPD not available — is it running?'

    # ------------------------------------------------------------------
    # Keyboard forwarding
    # ------------------------------------------------------------------

    def handle_key(self, key, codepoint):
        if codepoint == ' ':
            self._toggle_play(); return True
        if key == 275:   # right arrow
            self._next(); return True
        if key == 276:   # left arrow
            self._previous(); return True
        if key == 273:   # up arrow
            self._change_volume(5); return True
        if key == 274:   # down arrow
            self._change_volume(-5); return True
        return False
