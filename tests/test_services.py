"""
Unit Tests for T1000 Services
Tests cover critical functionality of OBD, camera, GPIO, audio, and data logging services
Run with: python -m pytest tests/test_services.py -v
"""

import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import services
from services.obd_service import OBDService, SensorReading, DTC_DATABASE
from services.camera_service import CameraService
from services.gpio_service import GPIOService, GPIOPin
from services.audio_service import AudioService, PlaybackMode
from services.data_logger import DataLogger, FuelFillup, TripSummary
from services.gps_service import GPSService, GPSFix
from services.health_monitor import HealthMonitor, SystemHealth


class TestOBDService:
    """Tests for OBD2 service"""

    def test_init(self):
        """Test OBDService initialization"""
        obd = OBDService(port='/dev/ttyUSB0', baudrate=38400)
        assert obd.port == '/dev/ttyUSB0'
        assert obd.baudrate == 38400
        assert obd.connected is False
        assert obd.active_dtcs == []

    def test_get_reading_nonexistent(self):
        """Test getting non-existent sensor reading"""
        obd = OBDService()
        reading = obd.get_reading('NONEXISTENT')
        assert reading is None

    def test_add_and_get_reading(self):
        """Test storing and retrieving sensor readings"""
        from datetime import datetime
        obd = OBDService()

        # Manually add a reading
        reading = SensorReading(
            name='TEST_SENSOR',
            value=100.0,
            unit='units',
            timestamp=datetime.now(),
            priority=1
        )
        obd.latest_readings['TEST_SENSOR'] = reading

        # Retrieve it
        retrieved = obd.get_reading('TEST_SENSOR')
        assert retrieved is not None
        assert retrieved.value == 100.0
        assert retrieved.name == 'TEST_SENSOR'

    def test_get_readings_by_priority(self):
        """Test filtering readings by priority"""
        from datetime import datetime
        obd = OBDService()

        # Add readings with different priorities
        readings = [
            SensorReading('P1_SENSOR', 1, 'units', datetime.now(), 1),
            SensorReading('P2_SENSOR', 2, 'units', datetime.now(), 2),
            SensorReading('P3_SENSOR', 3, 'units', datetime.now(), 3),
        ]

        for reading in readings:
            obd.latest_readings[reading.name] = reading

        # Get priority 2 readings
        p2_readings = obd.get_all_readings(priority=2)
        assert len(p2_readings) == 1
        assert 'P2_SENSOR' in p2_readings

    def test_dtc_database_size(self):
        """DTC_DATABASE must have at least 250 entries."""
        assert len(DTC_DATABASE) >= 250

    def test_dtc_database_format(self):
        """Every DTC entry must be a 3-tuple (title, description, severity)."""
        for code, entry in DTC_DATABASE.items():
            assert isinstance(entry, tuple) and len(entry) == 3, \
                f"{code}: expected 3-tuple, got {entry!r}"
            assert entry[2] in ('info', 'warning', 'critical'), \
                f"{code}: unknown severity '{entry[2]}'"

    def test_get_dtcs_returns_full_info(self):
        """get_dtcs() now returns dicts with title/description/severity."""
        obd = OBDService()
        obd.active_dtcs = ['P0301', 'P0420']

        dtc_dict = obd.get_dtcs()
        assert len(dtc_dict) == 2
        for code, info in dtc_dict.items():
            assert 'title' in info
            assert 'description' in info
            assert 'severity' in info

    def test_get_dtc_title(self):
        """get_dtc_title returns short name for known codes."""
        obd = OBDService()
        title = obd.get_dtc_title('P0420')
        assert isinstance(title, str) and len(title) > 5
        assert obd.get_dtc_title('ZZZZZ') == 'Unknown Code'

    def test_get_dtc_severity(self):
        """get_dtc_severity returns a valid severity string."""
        obd = OBDService()
        sev = obd.get_dtc_severity('P0016')
        assert sev in ('info', 'warning', 'critical')
        assert obd.get_dtc_severity('ZZZZZ') == 'warning'

    def test_get_chart_data(self):
        """get_chart_data returns two equal-length lists."""
        obd = OBDService()
        ts, vals = obd.get_chart_data('RPM')
        assert isinstance(ts, list)
        assert isinstance(vals, list)
        assert len(ts) == len(vals)

    def test_get_health_summary_structure(self):
        """get_health_summary returns expected keys and sane score."""
        obd = OBDService()
        summary = obd.get_health_summary()
        assert 'score' in summary
        assert 'issues' in summary
        assert 'dtc_count' in summary
        assert 0 <= summary['score'] <= 100
        assert isinstance(summary['issues'], list)

    def test_get_health_summary_dtc_penalty(self):
        """Active DTCs should reduce the health score."""
        obd = OBDService()
        clean_score = obd.get_health_summary()['score']
        obd.active_dtcs = ['P0301', 'P0302', 'P0303']
        penalised_score = obd.get_health_summary()['score']
        assert penalised_score < clean_score

    def test_status(self):
        """Test OBD service status"""
        obd = OBDService()
        status = obd.get_status()

        assert 'connected' in status
        assert 'port' in status
        assert 'readings_count' in status
        assert status['connected'] is False


class TestCameraService:
    """Tests for camera service"""

    def test_init(self):
        """Test CameraService initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            camera = CameraService(
                device='/dev/video0',
                resolution=(720, 480),
                fps=30
            )
            assert camera.device == '/dev/video0'
            assert camera.resolution == (720, 480)
            assert camera.fps == 30
            assert camera.connected is False

    def test_rolling_footage_directory_creation(self):
        """Test that rolling footage directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            camera = CameraService()
            assert camera.rolling_footage_dir.exists()
            assert camera.saved_footage_dir.exists()

    def test_cycle_camera(self):
        """Test camera cycling"""
        camera = CameraService()
        assert camera.current_camera_index == 0

        idx = camera.cycle_camera()
        assert idx == 1

        idx = camera.cycle_camera()
        assert idx == 0

    def test_toggle_manual_recording(self):
        """Test manual recording toggle"""
        camera = CameraService()
        assert camera.recording_manual is False

        result = camera.toggle_manual_recording()
        assert result is True

        result = camera.toggle_manual_recording()
        assert result is False

    def test_status(self):
        """Test camera service status"""
        camera = CameraService()
        status = camera.get_status()

        assert 'connected' in status
        assert 'device' in status
        assert 'resolution' in status
        assert 'current_camera' in status


class TestGPIOService:
    """Tests for GPIO service"""

    def test_init_no_gpio(self):
        """Test GPIOService initialization without GPIO"""
        gpio = GPIOService(use_gpio=False)
        assert gpio.use_gpio is False
        assert gpio.button_states == {}

    def test_register_button_callback(self):
        """Test button callback registration"""
        gpio = GPIOService(use_gpio=False)
        callback = Mock()

        gpio.register_callback(GPIOPin.PAUSE_PLAY, callback)
        assert GPIOPin.PAUSE_PLAY in gpio.button_callbacks
        assert callback in gpio.button_callbacks[GPIOPin.PAUSE_PLAY]

    def test_register_reverse_callback(self):
        """Test reverse signal callback registration"""
        gpio = GPIOService(use_gpio=False)
        callback = Mock()

        gpio.register_reverse_callback(callback)
        assert gpio.reverse_callback == callback

    def test_simulate_button_press(self):
        """Test simulated button press"""
        gpio = GPIOService(use_gpio=False)
        callback = Mock()

        gpio.register_callback(GPIOPin.PAUSE_PLAY, callback)
        gpio.simulate_button_press(GPIOPin.PAUSE_PLAY)

        callback.assert_called_once()

    def test_simulate_reverse_signal(self):
        """Test simulated reverse signal"""
        gpio = GPIOService(use_gpio=False)
        callback = Mock()

        gpio.register_reverse_callback(callback)
        gpio.simulate_reverse_signal(True)

        callback.assert_called_once_with(True)
        assert gpio.reverse_active is True

    def test_status(self):
        """Test GPIO service status"""
        gpio = GPIOService(use_gpio=False)
        status = gpio.get_status()

        assert 'gpio_enabled' in status
        assert 'polling_active' in status
        assert status['gpio_enabled'] is False


class TestAudioService:
    """Tests for audio service"""

    def test_init(self):
        """Test AudioService initialization"""
        audio = AudioService(use_mpd=False)
        assert audio.use_mpd is False
        assert audio.current_mode == PlaybackMode.SPOTIFY_IPAD
        assert audio.volume == 50

    def test_set_volume(self):
        """Test volume control"""
        audio = AudioService(use_mpd=False)

        # Set valid volume
        audio.set_volume(75)
        assert audio.get_volume() == 75

        # Test bounds
        audio.set_volume(150)  # Should be clamped
        assert audio.get_volume() == 100

        audio.set_volume(-10)  # Should be clamped
        assert audio.get_volume() == 0

    def test_toggle_play(self):
        """Test play/pause toggle"""
        audio = AudioService(use_mpd=False)
        assert audio.is_playing is False

        audio.toggle_play()
        assert audio.is_playing is True

        audio.toggle_play()
        assert audio.is_playing is False

    def test_switch_mode(self):
        """Test switching audio mode"""
        audio = AudioService(use_mpd=False)

        # Try to switch to MPD (should fail since not available)
        result = audio.set_mode(PlaybackMode.MPD_LOCAL)
        assert result is False  # MPD not connected

        # Spotify mode should work
        result = audio.set_mode(PlaybackMode.SPOTIFY_IPAD)
        assert result is True

    def test_get_track_info(self):
        """Test getting track information"""
        audio = AudioService(use_mpd=False)
        info = audio.get_current_track_info()

        assert 'track' in info
        assert 'artist' in info
        assert 'album' in info
        assert 'mode' in info

    def test_status(self):
        """Test audio service status"""
        audio = AudioService(use_mpd=False)
        status = audio.get_status()

        assert 'current_mode' in status
        assert 'volume' in status
        assert 'is_playing' in status


class TestDataLogger:
    """Tests for data logger service"""

    def test_init(self):
        """Test DataLogger initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)
            assert logger.log_dir == Path(tmpdir)
            assert logger.is_logging is False

    def test_start_session(self):
        """Test starting a logging session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)
            result = logger.start_session()

            assert result is True
            assert logger.is_logging is True
            assert logger.session_log_file is not None

    def test_log_sensor_data(self):
        """Test logging sensor data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)
            logger.start_session()

            sensor_data = {
                'rpm': 2000,
                'speed_mph': 45,
                'coolant_temp_f': 190,
            }
            logger.log_sensor_data(sensor_data)

            assert logger.trip_readings_count == 1
            assert logger.trip_speed_sum == 45
            assert logger.trip_rpm_sum == 2000

    def test_fuel_fillup_logging(self):
        """Test fuel fillup logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)

            result = logger.log_fuel_fillup(
                odometer=100,
                gallons=10,
                cost=35.50
            )

            assert result is True
            assert len(logger.fuel_fillups) == 1
            fillup = logger.fuel_fillups[0]
            assert fillup.odometer_miles == 100
            assert fillup.gallons == 10

    def test_calculate_fuel_economy(self):
        """Test fuel economy calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)

            # Add two fillups
            logger.log_fuel_fillup(odometer=100, gallons=10)
            logger.log_fuel_fillup(odometer=250, gallons=10)

            mpg = logger.get_fuel_economy()
            assert mpg is not None
            assert mpg == 15.0  # (250-100) / 10 = 15 MPG

    def test_end_session(self):
        """Test ending a logging session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)
            logger.start_session()

            # Log some data
            logger.log_sensor_data({'rpm': 2000, 'speed_mph': 50})
            time.sleep(0.1)

            trip = logger.end_session(final_odometer=150)

            assert trip is not None
            assert logger.is_logging is False
            assert len(logger.trips) == 1

    def test_status(self):
        """Test data logger status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = DataLogger(log_dir=tmpdir)
            status = logger.get_status()

            assert 'is_logging' in status
            assert 'trip_readings' in status
            assert 'fuel_fillups' in status


class TestGPSService:
    """Tests for GPS service (simulation mode — no hardware required)."""

    def test_init(self):
        gps = GPSService()
        assert gps.gpsd_host == 'localhost'
        assert gps.gpsd_port == 2947
        assert gps.connected is False
        assert gps.current_fix is None

    def test_simulated_fix_after_tick(self):
        """_generate_simulated_fix() must populate current_fix."""
        gps = GPSService()
        gps._generate_simulated_fix()
        fix = gps.get_fix()
        assert fix is not None
        assert fix.simulated is True
        assert fix.fix_quality == 3

    def test_simulated_fix_coordinates_near_home(self):
        """Simulated fix should start at (or very near) the home base."""
        gps = GPSService()
        gps._generate_simulated_fix()
        fix = gps.get_fix()
        dist = GPSService._distance_miles(
            fix.latitude, fix.longitude,
            GPSService.SIM_HOME_LAT, GPSService.SIM_HOME_LON
        )
        assert dist < 15  # should be within 15 miles of home

    def test_simulated_fix_stays_within_radius(self):
        """After 200 ticks, fix should remain within 12 miles of home."""
        gps = GPSService()
        for _ in range(200):
            gps._generate_simulated_fix()
        fix = gps.get_fix()
        dist = GPSService._distance_miles(
            fix.latitude, fix.longitude,
            GPSService.SIM_HOME_LAT, GPSService.SIM_HOME_LON
        )
        assert dist < 12

    def test_get_coordinates_returns_tuple(self):
        gps = GPSService()
        assert gps.get_coordinates() is None     # no fix yet
        gps._generate_simulated_fix()
        coords = gps.get_coordinates()
        assert isinstance(coords, tuple) and len(coords) == 2

    def test_has_fix_false_initially(self):
        gps = GPSService()
        assert gps.has_fix() is False

    def test_has_fix_true_after_simulation(self):
        gps = GPSService()
        gps._generate_simulated_fix()
        assert gps.has_fix() is True

    def test_get_heading_text_no_fix(self):
        gps = GPSService()
        assert gps.get_heading_text() == '---'

    def test_get_heading_text_with_fix(self):
        gps = GPSService()
        gps._generate_simulated_fix()
        heading = gps.get_heading_text()
        valid = {'N','NNE','NE','ENE','E','ESE','SE','SSE',
                 'S','SSW','SW','WSW','W','WNW','NW','NNW'}
        assert heading in valid

    def test_get_speed_mph_before_fix(self):
        gps = GPSService()
        assert gps.get_speed_mph() == 0.0

    def test_get_status_keys(self):
        gps = GPSService()
        status = gps.get_status()
        for key in ('connected', 'has_fix', 'simulated', 'satellites',
                    'fix_quality', 'latitude', 'longitude', 'speed_mph', 'heading'):
            assert key in status

    def test_distance_miles_same_point(self):
        dist = GPSService._distance_miles(32.0, -90.0, 32.0, -90.0)
        assert dist < 0.001

    def test_bearing_to_east(self):
        """Bearing from (0, 0) to (0, 1) should be ~90° (East)."""
        bearing = GPSService._bearing_to(0, 0, 0, 1)
        assert abs(bearing - 90) < 2


class TestHealthMonitor:
    """Tests for system health monitor (psutil optional)."""

    def test_init(self):
        monitor = HealthMonitor()
        assert monitor.is_running is False
        assert monitor.obd_service is None
        assert isinstance(monitor.alerts, list)

    def test_initial_health_object(self):
        monitor = HealthMonitor()
        h = monitor.get_system_health()
        assert isinstance(h, SystemHealth)
        assert h.cpu_percent >= 0

    def test_collect_fills_current(self):
        """_collect_system_metrics must populate the current SystemHealth."""
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        h = monitor.current
        assert h.cpu_percent >= 0
        assert h.ram_percent >= 0
        assert h.disk_percent >= 0

    def test_history_appended(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        assert len(monitor.cpu_history) == 1
        assert len(monitor.ram_history) == 1
        assert len(monitor.timestamps) == 1

    def test_get_chart_data_returns_equal_lists(self):
        monitor = HealthMonitor()
        for _ in range(3):
            monitor._collect_system_metrics()
        for metric in ('cpu', 'ram', 'temp'):
            ts, vals = monitor.get_chart_data(metric)
            assert len(ts) == len(vals) == 3

    def test_get_overall_score_range(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        score = monitor.get_overall_score()
        assert 0 <= score <= 100

    def test_score_integrates_obd(self):
        """With a healthy OBD service, score stays sensible."""
        obd = OBDService()
        monitor = HealthMonitor(obd_service=obd)
        monitor._collect_system_metrics()
        score = monitor.get_overall_score()
        assert 0 <= score <= 100

    def test_alerts_list(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        monitor._update_alerts()
        assert isinstance(monitor.get_alerts(), list)

    def test_high_temp_triggers_alert(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        monitor.current.cpu_temp_c = 85.0  # above critical threshold
        monitor._update_alerts()
        alerts = monitor.get_alerts()
        assert any('CRITICAL' in a or 'Hot' in a for a in alerts)

    def test_high_cpu_triggers_alert(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        monitor.current.cpu_percent = 95.0
        monitor._update_alerts()
        assert any('CPU' in a for a in monitor.get_alerts())

    def test_high_ram_triggers_alert(self):
        monitor = HealthMonitor()
        monitor._collect_system_metrics()
        monitor.current.ram_percent = 92.0
        monitor._update_alerts()
        assert any('RAM' in a for a in monitor.get_alerts())

    def test_uptime_str_format(self):
        monitor = HealthMonitor()
        monitor.current.uptime_seconds = 3723  # 1h 2m 3s
        result = monitor.get_uptime_str()
        assert '01h' in result
        assert '02m' in result
        assert '03s' in result

    def test_get_status_keys(self):
        monitor = HealthMonitor()
        status = monitor.get_status()
        for key in ('is_running', 'overall_score', 'alerts', 'system'):
            assert key in status


class TestIntegration:
    """Integration tests for multiple services"""

    def test_multiple_services_initialization(self):
        """Test that all services can be initialized simultaneously"""
        with tempfile.TemporaryDirectory() as tmpdir:
            obd = OBDService()
            camera = CameraService()
            gpio = GPIOService(use_gpio=False)
            audio = AudioService(use_mpd=False)
            logger = DataLogger(log_dir=tmpdir)

            # All should be initialized
            assert obd is not None
            assert camera is not None
            assert gpio is not None
            assert audio is not None
            assert logger is not None

    def test_gpio_triggers_ui_event(self):
        """Test GPIO button press triggers callback"""
        callback = Mock()
        gpio = GPIOService(use_gpio=False)

        gpio.register_callback(GPIOPin.PAUSE_PLAY, callback)
        gpio.simulate_button_press(GPIOPin.PAUSE_PLAY)

        callback.assert_called_once()

    def test_reverse_signal_triggers_callback(self):
        """Test reverse signal detection triggers callback"""
        callback = Mock()
        gpio = GPIOService(use_gpio=False)

        gpio.register_reverse_callback(callback)
        gpio.simulate_reverse_signal(True)

        callback.assert_called_with(True)


if __name__ == '__main__':
    # Run tests with: python -m pytest tests/test_services.py -v
    pytest.main([__file__, '-v'])
