"""
Audio Service Module
Handles music playback control and volume management
Primary: Spotify via iPad (pass-through volume control)
Fallback: MPD-based local music player
"""

import logging
import subprocess
import threading
import time
from typing import Optional, Dict
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import MPD client
try:
    import mpd
    MPD_AVAILABLE = True
except ImportError:
    MPD_AVAILABLE = False
    logger.warning("python-mpd2 not installed - local MPD fallback disabled")


class PlaybackMode(Enum):
    """Audio playback modes"""
    SPOTIFY_IPAD = "spotify_ipad"  # Primary: audio via aux cable from iPad
    MPD_LOCAL = "mpd_local"  # Fallback: local music on Pi


class AudioService:
    """
    Audio Control Service
    Manages volume, playback control, and music source selection
    Supports Spotify via iPad and MPD fallback
    """

    def __init__(self, use_mpd: bool = False, mpd_host: str = 'localhost', mpd_port: int = 6600):
        """
        Initialize audio service

        Args:
            use_mpd: Enable MPD fallback for local music
            mpd_host: MPD server hostname
            mpd_port: MPD server port
        """
        self.use_mpd = use_mpd and MPD_AVAILABLE
        self.mpd_host = mpd_host
        self.mpd_port = mpd_port

        # Audio state
        self.current_mode = PlaybackMode.SPOTIFY_IPAD
        self.volume = 50  # 0-100
        self.is_playing = False

        # MPD connection
        self.mpd_client = None
        self.mpd_connected = False

        # Current track info
        self.current_track = None
        self.current_artist = None
        self.current_album = None

        if self.use_mpd:
            self._connect_mpd()

        logger.info(f"AudioService initialized (use_mpd={self.use_mpd})")

    def _connect_mpd(self) -> bool:
        """Connect to MPD server"""
        if not self.use_mpd or not MPD_AVAILABLE:
            logger.warning("MPD not available - fallback disabled")
            self.mpd_connected = False
            return False

        try:
            self.mpd_client = mpd.MPDClient()
            self.mpd_client.timeout = 5
            self.mpd_client.idletimeout = None
            self.mpd_client.connect(self.mpd_host, self.mpd_port)

            logger.info(f"Connected to MPD at {self.mpd_host}:{self.mpd_port}")
            self.mpd_connected = True
            self._update_track_info()
            return True

        except Exception as e:
            logger.warning(f"MPD connection failed: {e}")
            self.mpd_connected = False
            return False

    def _update_track_info(self):
        """Update current track information from MPD"""
        if not self.mpd_connected:
            return

        try:
            current_song = self.mpd_client.currentsong()
            if current_song:
                self.current_track = current_song.get('title', 'Unknown')
                self.current_artist = current_song.get('artist', 'Unknown')
                self.current_album = current_song.get('album', 'Unknown')
                logger.debug(f"Now playing: {self.current_artist} - {self.current_track}")
        except Exception as e:
            logger.warning(f"Could not get current song: {e}")

    def set_volume(self, level: int) -> bool:
        """
        Set master volume level

        Args:
            level: Volume 0-100

        Returns:
            True if successful
        """
        level = max(0, min(100, level))

        # For Spotify via iPad: control Pi audio output to amplifier
        if self.current_mode == PlaybackMode.SPOTIFY_IPAD:
            try:
                # Use alsamixer to set volume (ALSA audio system)
                # This controls the audio going TO the TPA3116 amplifier
                result = subprocess.run(
                    ['amixer', 'sset', 'PCM', f'{level}%'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    self.volume = level
                    logger.debug(f"Volume set to {level}%")
                    return True
                else:
                    logger.warning(f"amixer error: {result.stderr}")
                    return False

            except FileNotFoundError:
                logger.warning("amixer not found - volume control unavailable")
                self.volume = level
                return True  # Still update internal state

            except Exception as e:
                logger.error(f"Volume control error: {e}")
                return False

        # For MPD: control via MPD volume
        elif self.current_mode == PlaybackMode.MPD_LOCAL and self.mpd_connected:
            try:
                self.mpd_client.setvol(level)
                self.volume = level
                logger.debug(f"MPD volume set to {level}%")
                return True
            except Exception as e:
                logger.warning(f"MPD volume control failed: {e}")
                return False

        return False

    def get_volume(self) -> int:
        """Get current volume level"""
        return self.volume

    def play(self) -> bool:
        """Start playback"""
        if not self.mpd_connected and self.current_mode == PlaybackMode.MPD_LOCAL:
            logger.warning("MPD not connected - cannot play")
            return False

        try:
            if self.current_mode == PlaybackMode.MPD_LOCAL:
                self.mpd_client.play()
                self.is_playing = True
                logger.info("MPD playback started")
                return True
            else:
                # Spotify via iPad - user controls playback on iPad
                logger.info("Spotify playback controlled via iPad")
                self.is_playing = True
                return True

        except Exception as e:
            logger.error(f"Play error: {e}")
            return False

    def pause(self) -> bool:
        """Pause playback"""
        if not self.mpd_connected and self.current_mode == PlaybackMode.MPD_LOCAL:
            return False

        try:
            if self.current_mode == PlaybackMode.MPD_LOCAL:
                self.mpd_client.pause()
                self.is_playing = False
                logger.info("MPD playback paused")
                return True
            else:
                self.is_playing = False
                return True

        except Exception as e:
            logger.error(f"Pause error: {e}")
            return False

    def toggle_play(self) -> bool:
        """Toggle play/pause"""
        if self.is_playing:
            return self.pause()
        else:
            return self.play()

    def next(self) -> bool:
        """Skip to next track"""
        if not self.mpd_connected and self.current_mode == PlaybackMode.MPD_LOCAL:
            return False

        try:
            if self.current_mode == PlaybackMode.MPD_LOCAL:
                self.mpd_client.next()
                self._update_track_info()
                logger.info("Skipped to next track")
                return True
            else:
                logger.info("Next track - controlled via iPad Spotify app")
                return True

        except Exception as e:
            logger.error(f"Next track error: {e}")
            return False

    def previous(self) -> bool:
        """Go to previous track"""
        if not self.mpd_connected and self.current_mode == PlaybackMode.MPD_LOCAL:
            return False

        try:
            if self.current_mode == PlaybackMode.MPD_LOCAL:
                self.mpd_client.previous()
                self._update_track_info()
                logger.info("Skipped to previous track")
                return True
            else:
                logger.info("Previous track - controlled via iPad Spotify app")
                return True

        except Exception as e:
            logger.error(f"Previous track error: {e}")
            return False

    def set_mode(self, mode: PlaybackMode) -> bool:
        """
        Switch audio source mode

        Args:
            mode: PlaybackMode to switch to

        Returns:
            True if successful
        """
        if mode == PlaybackMode.MPD_LOCAL and not self.mpd_connected:
            logger.warning("MPD not available - cannot switch to MPD mode")
            return False

        self.current_mode = mode
        logger.info(f"Audio mode switched to {mode.value}")

        if mode == PlaybackMode.MPD_LOCAL:
            self._update_track_info()

        return True

    def get_current_track_info(self) -> Dict[str, Optional[str]]:
        """Get current track information"""
        if self.current_mode == PlaybackMode.SPOTIFY_IPAD:
            return {
                'track': 'Spotify on iPad',
                'artist': '(controlled via iPad)',
                'album': self.current_album or 'N/A',
                'mode': 'iPad (Aux)',
            }
        else:
            return {
                'track': self.current_track or 'No track',
                'artist': self.current_artist or 'Unknown',
                'album': self.current_album or 'Unknown',
                'mode': 'Local (MPD)',
            }

    def get_status(self) -> Dict:
        """Get audio service status"""
        return {
            'current_mode': self.current_mode.value,
            'volume': self.volume,
            'is_playing': self.is_playing,
            'mpd_connected': self.mpd_connected,
            'track': self.current_track or 'N/A',
            'artist': self.current_artist or 'N/A',
        }

    def stop(self):
        """Stop audio service and cleanup"""
        try:
            if self.mpd_connected:
                self.mpd_client.close()
                logger.info("MPD connection closed")
        except Exception as e:
            logger.warning(f"Error closing MPD: {e}")


if __name__ == '__main__':
    # Test audio service
    logging.basicConfig(level=logging.DEBUG)

    audio = AudioService(use_mpd=False)
    print(f"Status: {audio.get_status()}")

    # Test volume
    audio.set_volume(75)
    print(f"Volume: {audio.get_volume()}%")

    # Test mode switching
    audio.set_mode(PlaybackMode.SPOTIFY_IPAD)
    print(f"Current track: {audio.get_current_track_info()}")

    audio.stop()
