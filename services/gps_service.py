"""
GPS Service Module — T1000 Infotainment System
Reads position data from a USB GPS receiver via gpsd.
Falls back to realistic simulated coordinates when hardware is absent.
"""

import logging
import threading
import time
import math
import random
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass

# Try gpsd client library (pip install gps3 or gpsd-py3)
try:
    from gps3 import gps3 as gps3lib
    GPS3_AVAILABLE = True
except ImportError:
    GPS3_AVAILABLE = False

try:
    import gps as gpsd_gps
    GPSD_AVAILABLE = True
except ImportError:
    GPSD_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class GPSFix:
    """Current GPS position and status."""
    latitude: float       # decimal degrees
    longitude: float      # decimal degrees
    altitude_ft: float    # feet
    speed_mph: float      # miles per hour
    heading_deg: float    # degrees true (0=N, 90=E, 180=S, 270=W)
    fix_quality: int      # 0=no fix, 1=GPS fix, 2=DGPS fix
    satellites: int       # number of satellites in view
    timestamp: datetime
    simulated: bool       # True when using simulation


class GPSService:
    """
    GPS Position Service.
    Connects to gpsd daemon for USB GPS receiver data.
    Falls back to simulated driving route when no GPS hardware present.
    """

    # Simulated home base: Vicksburg, Mississippi area
    SIM_HOME_LAT = 32.3526
    SIM_HOME_LON = -90.8779
    SIM_HOME_ALT = 230.0  # ft

    def __init__(self, gpsd_host: str = 'localhost', gpsd_port: int = 2947):
        self.gpsd_host = gpsd_host
        self.gpsd_port = gpsd_port

        self.current_fix: Optional[GPSFix] = None
        self.is_running = False
        self.connected = False
        self.thread: Optional[threading.Thread] = None

        self._gpsd_failed = False      # True after 3 failed connects → pure sim
        self._connect_failures = 0

        # Simulation state
        self._sim_lat = self.SIM_HOME_LAT
        self._sim_lon = self.SIM_HOME_LON
        self._sim_heading = 45.0   # NE
        self._sim_speed = 0.0
        self._sim_tick = 0

        logger.info(f"GPSService initialized (gpsd at {gpsd_host}:{gpsd_port})")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self.is_running:
            return
        # Generate an initial fix immediately so screens have data on first paint
        self._generate_simulated_fix()
        self.is_running = True
        self.thread = threading.Thread(target=self._gps_loop, daemon=True)
        self.thread.start()
        logger.info("GPS service thread started")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("GPS service stopped")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _gps_loop(self):
        while self.is_running:
            try:
                if self._gpsd_failed:
                    self._generate_simulated_fix()
                    time.sleep(1.0)
                    continue

                if not self.connected:
                    if not self._connect_gpsd():
                        self._connect_failures += 1
                        self._generate_simulated_fix()
                        if self._connect_failures >= 3:
                            logger.info("gpsd unavailable — switching to simulation mode")
                            self._gpsd_failed = True
                        time.sleep(1.0)
                        continue

                self._connect_failures = 0
                self._read_gpsd()
                time.sleep(1.0)

            except Exception as e:
                logger.debug(f"GPS loop error: {e}")
                self.connected = False
                self._generate_simulated_fix()
                time.sleep(2.0)

    def _connect_gpsd(self) -> bool:
        """Attempt to connect to gpsd daemon."""
        if not (GPS3_AVAILABLE or GPSD_AVAILABLE):
            return False

        try:
            if GPS3_AVAILABLE:
                self._gps3_socket = gps3lib.GPSDSocket()
                self._gps3_data = gps3lib.DataStream()
                self._gps3_socket.connect(self.gpsd_host, self.gpsd_port)
                self._gps3_socket.watch()
                self.connected = True
                logger.info("Connected to gpsd via gps3")
                return True
        except Exception as e:
            logger.debug(f"gpsd connection failed: {e}")

        return False

    def _read_gpsd(self):
        """Read one fix from gpsd."""
        try:
            if GPS3_AVAILABLE and hasattr(self, '_gps3_socket'):
                for new_data in self._gps3_socket:
                    if new_data:
                        self._gps3_data.unpack(new_data)
                        lat = self._gps3_data.TPV.get('lat', 'n/a')
                        lon = self._gps3_data.TPV.get('lon', 'n/a')
                        alt = self._gps3_data.TPV.get('alt', 0)
                        spd = self._gps3_data.TPV.get('speed', 0)
                        trk = self._gps3_data.TPV.get('track', 0)
                        mode = self._gps3_data.TPV.get('mode', 0)

                        if lat != 'n/a' and lon != 'n/a':
                            self.current_fix = GPSFix(
                                latitude=float(lat),
                                longitude=float(lon),
                                altitude_ft=float(alt or 0) * 3.28084,
                                speed_mph=float(spd or 0) * 2.23694,
                                heading_deg=float(trk or 0),
                                fix_quality=int(mode or 0),
                                satellites=self._gps3_data.SKY.get('nSat', 0) or 0,
                                timestamp=datetime.now(),
                                simulated=False
                            )
                        break
        except Exception as e:
            logger.debug(f"gpsd read error: {e}")
            self.connected = False

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def _generate_simulated_fix(self):
        """
        Simulate a GPS fix with a vehicle slowly driving around
        the Vicksburg, Mississippi area.
        """
        self._sim_tick += 1
        t = self._sim_tick

        # Speed profile: accelerate, cruise, decelerate, stop
        phase = t % 120
        if phase < 20:
            self._sim_speed = phase * 2.0           # 0 → 40 mph
        elif phase < 80:
            self._sim_speed = 40.0 + random.gauss(0, 1)  # cruise ~40 mph
        elif phase < 110:
            self._sim_speed = max(0, 40 - (phase - 80) * 1.4)  # slow down
        else:
            self._sim_speed = 0.0                   # stopped

        # Gently drift heading
        self._sim_heading = (self._sim_heading + random.gauss(0, 1)) % 360

        # Move position based on speed and heading
        if self._sim_speed > 0:
            # Convert speed to degrees/second (roughly)
            dist_deg = (self._sim_speed * 0.44704) / 111_000  # meters per degree ≈ 111 km
            rad = math.radians(self._sim_heading)
            self._sim_lat += dist_deg * math.cos(rad)
            self._sim_lon += dist_deg * math.sin(rad) / math.cos(math.radians(self._sim_lat))

        # Keep within ~10 miles of home
        if self._distance_miles(self._sim_lat, self._sim_lon,
                                self.SIM_HOME_LAT, self.SIM_HOME_LON) > 10:
            # Turn back toward home
            bearing = self._bearing_to(self._sim_lat, self._sim_lon,
                                       self.SIM_HOME_LAT, self.SIM_HOME_LON)
            self._sim_heading = bearing + random.gauss(0, 10)

        alt = self.SIM_HOME_ALT + random.gauss(0, 5)
        sats = random.randint(6, 12)

        self.current_fix = GPSFix(
            latitude=self._sim_lat,
            longitude=self._sim_lon,
            altitude_ft=alt,
            speed_mph=max(0, self._sim_speed),
            heading_deg=self._sim_heading % 360,
            fix_quality=3,     # simulated 3D fix
            satellites=sats,
            timestamp=datetime.now(),
            simulated=True
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _distance_miles(lat1, lon1, lat2, lon2) -> float:
        R = 3958.8  # Earth radius in miles
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _bearing_to(lat1, lon1, lat2, lon2) -> float:
        d_lon = math.radians(lon2 - lon1)
        x = math.sin(d_lon) * math.cos(math.radians(lat2))
        y = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
             math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(d_lon))
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_fix(self) -> Optional[GPSFix]:
        """Return the most recent GPS fix."""
        return self.current_fix

    def get_coordinates(self) -> Optional[tuple]:
        """Return (lat, lon) tuple or None."""
        if self.current_fix:
            return (self.current_fix.latitude, self.current_fix.longitude)
        return None

    def get_speed_mph(self) -> float:
        return self.current_fix.speed_mph if self.current_fix else 0.0

    def get_heading_text(self) -> str:
        """Convert heading degrees to cardinal direction string."""
        if not self.current_fix:
            return "---"
        deg = self.current_fix.heading_deg
        dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = round(deg / 22.5) % 16
        return dirs[idx]

    def has_fix(self) -> bool:
        return (self.current_fix is not None and
                self.current_fix.fix_quality >= 1)

    def get_status(self) -> dict:
        fix = self.current_fix
        return {
            'connected': self.connected,
            'has_fix': self.has_fix(),
            'simulated': fix.simulated if fix else True,
            'satellites': fix.satellites if fix else 0,
            'fix_quality': fix.fix_quality if fix else 0,
            'latitude': fix.latitude if fix else None,
            'longitude': fix.longitude if fix else None,
            'speed_mph': fix.speed_mph if fix else 0.0,
            'heading': fix.heading_deg if fix else 0.0,
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    gps = GPSService()
    gps.start()
    for _ in range(5):
        time.sleep(2)
        fix = gps.get_fix()
        if fix:
            print(f"  {fix.latitude:.6f}, {fix.longitude:.6f} "
                  f"  {fix.speed_mph:.1f} mph  {gps.get_heading_text()}  "
                  f"{'[SIM]' if fix.simulated else '[GPS]'}")
    gps.stop()
