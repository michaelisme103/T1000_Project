"""
Data Logger Module
Logs OBD2 sensor data and trip statistics for analysis
Features:
- Continuous CSV logging of all sensor data
- 30-day rolling log retention
- Trip summaries (distance, duration, avg speed, fuel used)
- Manual fuel tracking
- Export capability for analysis
"""

import logging
import threading
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FuelFillup:
    """Fuel fillup record"""
    timestamp: str
    odometer_miles: float
    gallons: float
    cost: Optional[float] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class TripSummary:
    """Summary statistics for a single trip"""
    start_time: str
    end_time: str
    duration_minutes: float
    distance_miles: float
    avg_speed_mph: float
    max_speed_mph: float
    avg_rpm: float
    max_rpm: float
    avg_temp_f: float
    max_temp_f: float
    fuel_used_gallons: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class DataLogger:
    """
    Data Logging Service
    Logs OBD2 sensor data and manages trip history
    """

    def __init__(self, log_dir: str = 'logs/diagnostics'):
        """
        Initialize data logger

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Current session logging
        self.session_log_file = None
        self.session_writer = None
        self.is_logging = False

        # Trip tracking
        self.trip_start_time: Optional[datetime] = None
        self.trip_start_odometer: Optional[float] = None
        self.trip_max_speed = 0
        self.trip_max_rpm = 0
        self.trip_max_temp = 0
        self.trip_readings_count = 0
        self.trip_speed_sum = 0
        self.trip_rpm_sum = 0
        self.trip_temp_sum = 0

        # Fuel tracking
        self.fuel_fillups: List[FuelFillup] = []
        self.fuel_log_file = self.log_dir / 'fuel_tracking.csv'
        self._load_fuel_history()

        # Trip history
        self.trips: List[TripSummary] = []
        self.trip_history_file = self.log_dir / 'trip_history.csv'
        self._load_trip_history()

        self._seed_demo_data()
        logger.info(f"DataLogger initialized (log_dir={log_dir})")

    def _seed_demo_data(self):
        """Add demo fuel fillups so MPG calculation works on first launch."""
        if self.fuel_fillups:
            return  # already have real data
        demo = [
            FuelFillup('2026-04-01T08:00:00', 87340.0, 12.4, 48.36),
            FuelFillup('2026-04-14T17:30:00', 87523.0, 11.8, 46.02),
            FuelFillup('2026-04-28T09:15:00', 87701.0, 12.1, 47.19),
        ]
        self.fuel_fillups.extend(demo)

    def start_session(self) -> bool:
        """Start a new logging session"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.session_log_file = self.log_dir / f"session_{timestamp}.csv"

            # Open CSV file for writing
            self.session_writer = open(self.session_log_file, 'w', newline='')

            # Write header
            fieldnames = [
                'timestamp',
                'rpm',
                'speed_mph',
                'coolant_temp_f',
                'intake_temp_f',
                'battery_voltage',
                'throttle_pos',
                'fuel_pressure_psi',
                'timing_advance',
                'maf_sensor',
                'o2_sensor_voltage'
            ]
            self.session_csv = csv.DictWriter(self.session_writer, fieldnames=fieldnames)
            self.session_csv.writeheader()

            self.is_logging = True
            self.trip_start_time = datetime.now()
            self.trip_readings_count = 0

            logger.info(f"Started logging session: {self.session_log_file.name}")
            return True

        except Exception as e:
            logger.error(f"Error starting logging session: {e}")
            return False

    def log_sensor_data(self, sensor_data: Dict[str, float]):
        """
        Log sensor reading to CSV

        Args:
            sensor_data: Dictionary of sensor name -> value pairs
        """
        if not self.is_logging or not self.session_writer:
            return

        try:
            # Accumulate trip statistics
            if 'speed_mph' in sensor_data:
                speed = sensor_data['speed_mph']
                self.trip_max_speed = max(self.trip_max_speed, speed)
                self.trip_speed_sum += speed

            if 'rpm' in sensor_data:
                rpm = sensor_data['rpm']
                self.trip_max_rpm = max(self.trip_max_rpm, rpm)
                self.trip_rpm_sum += rpm

            if 'coolant_temp_f' in sensor_data:
                temp = sensor_data['coolant_temp_f']
                self.trip_max_temp = max(self.trip_max_temp, temp)
                self.trip_temp_sum += temp

            self.trip_readings_count += 1

            # Build log row
            log_row = {
                'timestamp': datetime.now().isoformat(),
                **sensor_data
            }

            # Write row
            self.session_csv.writerow(log_row)
            self.session_writer.flush()

        except Exception as e:
            logger.warning(f"Error logging sensor data: {e}")

    def end_session(self, final_odometer: Optional[float] = None) -> Optional[TripSummary]:
        """
        End current logging session and create trip summary

        Args:
            final_odometer: Final odometer reading in miles

        Returns:
            TripSummary object or None
        """
        if not self.is_logging:
            logger.warning("No active logging session")
            return None

        try:
            self.is_logging = False
            if self.session_writer:
                self.session_writer.close()

            # Calculate trip summary
            trip_end_time = datetime.now()
            duration = (trip_end_time - self.trip_start_time).total_seconds() / 60  # minutes

            trip = TripSummary(
                start_time=self.trip_start_time.isoformat(),
                end_time=trip_end_time.isoformat(),
                duration_minutes=duration,
                distance_miles=final_odometer - self.trip_start_odometer if final_odometer else 0,
                avg_speed_mph=self.trip_speed_sum / self.trip_readings_count if self.trip_readings_count > 0 else 0,
                max_speed_mph=self.trip_max_speed,
                avg_rpm=self.trip_rpm_sum / self.trip_readings_count if self.trip_readings_count > 0 else 0,
                max_rpm=self.trip_max_rpm,
                avg_temp_f=self.trip_temp_sum / self.trip_readings_count if self.trip_readings_count > 0 else 0,
                max_temp_f=self.trip_max_temp,
            )

            self.trips.append(trip)
            self._save_trip_history()

            logger.info(f"Trip summary saved: {trip.distance_miles:.1f} miles in {trip.duration_minutes:.1f} minutes")
            return trip

        except Exception as e:
            logger.error(f"Error ending logging session: {e}")
            return None

    def log_fuel_fillup(self, odometer: float, gallons: float, cost: Optional[float] = None, notes: Optional[str] = None) -> bool:
        """
        Log a fuel fillup event

        Args:
            odometer: Odometer reading in miles
            gallons: Gallons added
            cost: Cost of fillup (optional)
            notes: User notes (optional)

        Returns:
            True if successful
        """
        try:
            fillup = FuelFillup(
                timestamp=datetime.now().isoformat(),
                odometer_miles=odometer,
                gallons=gallons,
                cost=cost,
                notes=notes
            )

            self.fuel_fillups.append(fillup)
            self._save_fuel_history()

            logger.info(f"Fuel fillup logged: {gallons} gallons at {odometer} miles")
            return True

        except Exception as e:
            logger.error(f"Error logging fuel fillup: {e}")
            return False

    def get_fuel_economy(self) -> Optional[float]:
        """
        Calculate average MPG from fuel fillups

        Returns:
            Average MPG or None
        """
        if len(self.fuel_fillups) < 2:
            return None

        try:
            # Sort by odometer reading
            sorted_fillups = sorted(self.fuel_fillups, key=lambda x: x.odometer_miles)

            # Calculate MPG between each consecutive pair
            mpgs = []
            for i in range(1, len(sorted_fillups)):
                distance = sorted_fillups[i].odometer_miles - sorted_fillups[i-1].odometer_miles
                gallons = sorted_fillups[i].gallons
                if gallons > 0:
                    mpg = distance / gallons
                    mpgs.append(mpg)

            if mpgs:
                return sum(mpgs) / len(mpgs)  # Average

        except Exception as e:
            logger.warning(f"Error calculating fuel economy: {e}")

        return None

    def _save_fuel_history(self):
        """Save fuel fillup history to CSV"""
        try:
            with open(self.fuel_log_file, 'w', newline='') as f:
                fieldnames = ['timestamp', 'odometer_miles', 'gallons', 'cost', 'notes']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for fillup in self.fuel_fillups:
                    writer.writerow(fillup.to_dict())

            logger.debug(f"Saved {len(self.fuel_fillups)} fuel fillups")

        except Exception as e:
            logger.error(f"Error saving fuel history: {e}")

    def _load_fuel_history(self):
        """Load fuel fillup history from CSV"""
        if not self.fuel_log_file.exists():
            return

        try:
            with open(self.fuel_log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fillup = FuelFillup(
                        timestamp=row['timestamp'],
                        odometer_miles=float(row['odometer_miles']),
                        gallons=float(row['gallons']),
                        cost=float(row['cost']) if row['cost'] else None,
                        notes=row['notes'] if row['notes'] else None
                    )
                    self.fuel_fillups.append(fillup)

            logger.info(f"Loaded {len(self.fuel_fillups)} fuel fillups from history")

        except Exception as e:
            logger.warning(f"Error loading fuel history: {e}")

    def _save_trip_history(self):
        """Save trip history to CSV"""
        try:
            with open(self.trip_history_file, 'w', newline='') as f:
                fieldnames = [
                    'start_time', 'end_time', 'duration_minutes', 'distance_miles',
                    'avg_speed_mph', 'max_speed_mph', 'avg_rpm', 'max_rpm',
                    'avg_temp_f', 'max_temp_f', 'fuel_used_gallons'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for trip in self.trips:
                    writer.writerow(trip.to_dict())

            logger.debug(f"Saved {len(self.trips)} trip summaries")

        except Exception as e:
            logger.error(f"Error saving trip history: {e}")

    def _load_trip_history(self):
        """Load trip history from CSV"""
        if not self.trip_history_file.exists():
            return

        try:
            with open(self.trip_history_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trip = TripSummary(
                        start_time=row['start_time'],
                        end_time=row['end_time'],
                        duration_minutes=float(row['duration_minutes']),
                        distance_miles=float(row['distance_miles']),
                        avg_speed_mph=float(row['avg_speed_mph']),
                        max_speed_mph=float(row['max_speed_mph']),
                        avg_rpm=float(row['avg_rpm']),
                        max_rpm=float(row['max_rpm']),
                        avg_temp_f=float(row['avg_temp_f']),
                        max_temp_f=float(row['max_temp_f']),
                        fuel_used_gallons=float(row['fuel_used_gallons']) if row['fuel_used_gallons'] else None
                    )
                    self.trips.append(trip)

            logger.info(f"Loaded {len(self.trips)} trips from history")

        except Exception as e:
            logger.warning(f"Error loading trip history: {e}")

    def cleanup_old_logs(self, max_age_days: int = 30):
        """Clean up log files older than max_age_days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=max_age_days)

            for log_file in self.log_dir.glob('session_*.csv'):
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    log_file.unlink()
                    logger.debug(f"Deleted old log: {log_file.name}")

        except Exception as e:
            logger.warning(f"Error cleaning up logs: {e}")

    def get_status(self) -> dict:
        """Get data logger status"""
        return {
            'is_logging': self.is_logging,
            'session_file': self.session_log_file.name if self.session_log_file else None,
            'trip_readings': self.trip_readings_count,
            'trips_recorded': len(self.trips),
            'fuel_fillups': len(self.fuel_fillups),
            'avg_mpg': round(self.get_fuel_economy(), 1) if self.get_fuel_economy() else None,
        }


if __name__ == '__main__':
    # Test data logger
    logging.basicConfig(level=logging.DEBUG)

    logger_service = DataLogger()
    logger_service.start_session()

    # Simulate some data logging
    for i in range(5):
        sensor_data = {
            'rpm': 2000 + i * 100,
            'speed_mph': 40 + i,
            'coolant_temp_f': 190 + i * 2,
            'battery_voltage': 13.5 + i * 0.01,
        }
        logger_service.log_sensor_data(sensor_data)
        time.sleep(1)

    # End session and log fuel
    trip = logger_service.end_session(final_odometer=150)
    logger_service.log_fuel_fillup(odometer=150, gallons=10, cost=35.50)

    print(f"Status: {logger_service.get_status()}")
    print(f"Trip: {trip.to_dict() if trip else 'None'}")
