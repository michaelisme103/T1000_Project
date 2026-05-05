"""
Mileage Tracker Service — T1000 Infotainment System
Tracks work vs personal trips using GPS distance accumulation.
Auto-saves when engine turns off (OBD RPM drops below threshold).
Logs to logs/work_miles/ and logs/personal_miles/ as monthly CSVs.
"""

import csv
import logging
import math
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MileageTrip:
    trip_id: str
    trip_type: str          # 'work' or 'personal'
    start_time: str
    end_time: str
    distance_miles: float
    duration_minutes: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    notes: str = ''

    def to_dict(self):
        return asdict(self)


class MileageTracker:
    """
    GPS-based mileage tracker.
    - Accumulates haversine distance between GPS samples every 2 s
    - Detects engine-off via OBD RPM < ENGINE_OFF_RPM and auto-saves
    - Monthly CSV files per trip type, easy to import into Excel / Google Sheets
    """

    POLL_INTERVAL   = 2.0   # seconds between GPS samples
    ENGINE_OFF_RPM  = 200   # below this → engine considered off
    MAX_JUMP_MILES  = 0.3   # ignore GPS jumps larger than this per sample

    def __init__(self, gps_service=None, obd_service=None):
        self.gps = gps_service
        self.obd = obd_service

        self.work_dir     = Path('logs/work_miles')
        self.personal_dir = Path('logs/personal_miles')
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.personal_dir.mkdir(parents=True, exist_ok=True)

        self._tracking    = False
        self._trip_type: Optional[str] = None
        self._start_time: Optional[datetime] = None
        self._distance_acc = 0.0
        self._last_lat: Optional[float] = None
        self._last_lon: Optional[float] = None
        self._start_lat: float = 0.0
        self._start_lon: float = 0.0

        self.current_trip: Optional[MileageTrip] = None
        self.completed_trips: list = []

        self.is_running = False
        self.thread: Optional[threading.Thread] = None

        logger.info("MileageTracker initialized")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("MileageTracker thread started")

    def stop(self):
        if self._tracking:
            self.end_trip(notes='app shutdown')
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("MileageTracker stopped")

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def _loop(self):
        while self.is_running:
            try:
                if self._tracking:
                    self._accumulate_distance()
                    self._check_engine_off()
                time.sleep(self.POLL_INTERVAL)
            except Exception as e:
                logger.error(f"MileageTracker loop error: {e}")
                time.sleep(self.POLL_INTERVAL)

    def _accumulate_distance(self):
        if not self.gps:
            return
        fix = self.gps.get_fix()
        if not fix or fix.fix_quality < 1:
            return
        lat, lon = fix.latitude, fix.longitude
        if self._last_lat is not None:
            d = self._haversine(self._last_lat, self._last_lon, lat, lon)
            if d < self.MAX_JUMP_MILES:
                self._distance_acc += d
        self._last_lat = lat
        self._last_lon = lon

    def _check_engine_off(self):
        if not self.obd:
            return
        rpm_r = self.obd.get_reading('RPM')
        if rpm_r is not None and rpm_r.value < self.ENGINE_OFF_RPM:
            logger.info("Engine off detected — auto-saving mileage trip")
            self.end_trip(notes='auto-saved: engine off')

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2) -> float:
        R = 3958.8
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_trip(self, trip_type: str) -> bool:
        """Begin tracking a work or personal trip."""
        if trip_type not in ('work', 'personal'):
            return False
        if self._tracking:
            self.end_trip(notes='replaced by new trip')

        self._trip_type    = trip_type
        self._start_time   = datetime.now()
        self._distance_acc = 0.0
        self._tracking     = True

        fix = self.gps.get_fix() if self.gps else None
        self._start_lat  = fix.latitude  if fix else 0.0
        self._start_lon  = fix.longitude if fix else 0.0
        self._last_lat   = self._start_lat or None
        self._last_lon   = self._start_lon or None

        trip_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_trip = MileageTrip(
            trip_id=trip_id, trip_type=trip_type,
            start_time=self._start_time.isoformat(), end_time='',
            distance_miles=0.0, duration_minutes=0.0,
            start_lat=self._start_lat, start_lon=self._start_lon,
            end_lat=0.0, end_lon=0.0,
        )
        logger.info(f"Trip started: {trip_type} ({trip_id})")
        return True

    def end_trip(self, notes: str = '') -> Optional[MileageTrip]:
        """Finalize and save the current trip. Returns the saved trip or None."""
        if not self._tracking or not self.current_trip:
            return None

        self._tracking = False
        end_time = datetime.now()
        duration = (end_time - self._start_time).total_seconds() / 60

        fix = self.gps.get_fix() if self.gps else None
        self.current_trip.end_time       = end_time.isoformat()
        self.current_trip.distance_miles = round(self._distance_acc, 2)
        self.current_trip.duration_minutes = round(duration, 1)
        self.current_trip.end_lat = fix.latitude  if fix else 0.0
        self.current_trip.end_lon = fix.longitude if fix else 0.0
        self.current_trip.notes   = notes

        self._save_trip(self.current_trip)
        self.completed_trips.append(self.current_trip)
        saved = self.current_trip
        self.current_trip = None
        logger.info(f"Trip saved: {saved.trip_type} — {saved.distance_miles:.2f} mi "
                    f"in {saved.duration_minutes:.1f} min")
        return saved

    def _save_trip(self, trip: MileageTrip):
        folder = self.work_dir if trip.trip_type == 'work' else self.personal_dir
        month  = datetime.now().strftime('%Y_%m')
        csv_path = folder / f"{trip.trip_type}_{month}.csv"
        write_header = not csv_path.exists()
        try:
            with open(csv_path, 'a', newline='') as f:
                w = csv.DictWriter(f, fieldnames=trip.to_dict().keys())
                if write_header:
                    w.writeheader()
                w.writerow(trip.to_dict())
            logger.info(f"Trip written to {csv_path.name}")
        except Exception as e:
            logger.error(f"Failed to write trip CSV: {e}")

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_tracking(self) -> bool:
        return self._tracking

    def get_trip_type(self) -> Optional[str]:
        return self._trip_type if self._tracking else None

    def get_current_distance(self) -> float:
        return round(self._distance_acc, 2)

    def get_elapsed(self) -> str:
        if not self._tracking or not self._start_time:
            return '--:--'
        secs = int((datetime.now() - self._start_time).total_seconds())
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def get_monthly_totals(self) -> dict:
        """Return {'work': miles, 'personal': miles} for the current calendar month."""
        month_str = datetime.now().strftime('%Y_%m')
        totals = {'work': 0.0, 'personal': 0.0}
        for t, folder in (('work', self.work_dir), ('personal', self.personal_dir)):
            f = folder / f"{t}_{month_str}.csv"
            if f.exists():
                try:
                    with open(f) as csvf:
                        for row in csv.DictReader(csvf):
                            totals[t] += float(row.get('distance_miles', 0))
                except Exception:
                    pass
        # Add currently running trip to totals
        if self._tracking:
            totals[self._trip_type] = totals.get(self._trip_type, 0) + self._distance_acc
        return {k: round(v, 1) for k, v in totals.items()}

    def get_recent_trips(self, n: int = 8) -> list:
        """Return the n most recent saved trips across both folders."""
        rows = []
        for folder in (self.work_dir, self.personal_dir):
            for f in sorted(folder.glob('*.csv'), reverse=True)[:3]:
                try:
                    with open(f) as csvf:
                        rows.extend(list(csv.DictReader(csvf)))
                except Exception:
                    pass
        rows.sort(key=lambda r: r.get('start_time', ''), reverse=True)
        return rows[:n]

    def get_status(self) -> dict:
        return {
            'tracking':     self._tracking,
            'trip_type':    self._trip_type,
            'distance_mi':  self.get_current_distance(),
            'elapsed':      self.get_elapsed(),
            'monthly':      self.get_monthly_totals(),
        }
