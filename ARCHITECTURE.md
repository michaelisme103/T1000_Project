# T1000 System Architecture

Comprehensive technical architecture for the T1000 infotainment system.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    T1000 Infotainment System                 │
├─────────────────────────────────────────────────────────────┤
│                      Kivy UI Framework                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Screen Manager                                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Home │ Camera │ Music │ Diagnostics │ Navigation   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│              Background Service Layer (Threaded)            │
│  ┌────────────┬──────────────┬──────────────┬──────────┐   │
│  │ OBD        │ Camera       │ GPIO         │ Audio    │   │
│  │ Service    │ Service      │ Service      │ Service  │   │
│  └────────────┴──────────────┴──────────────┴──────────┘   │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Data Logger Service (CSV logging & analysis)      │    │
│  └────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│              Hardware Abstraction Layer                      │
├─────────────────────────────────────────────────────────────┤
│  USB Devices │ GPIO Pins │ Serial Ports │ Video Devices    │
├─────────────────────────────────────────────────────────────┤
│                    Raspberry Pi 4B Hardware                  │
│                   (4GB RAM, 4× ARM CPU)                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. UI Layer (main.py)

**Responsibility:** User interface rendering and keyboard control

```python
T1000App (Kivy Application)
├── ScreenManager
│   ├── HomeScreen
│   ├── CameraScreen
│   ├── MusicScreen
│   ├── DiagnosticsScreen
│   └── NavigationScreen
└── on_keyboard() → Route input to active screen
```

**Key Features:**
- Event-driven keyboard input handling
- Screen transitions via ScreenManager
- Non-blocking rendering (60 FPS)
- Responsive to 1280×800 display

**Design Patterns:**
- MVC (Model-View-Controller) through services
- Observer pattern for events
- Factory pattern for screen creation

### 2. OBD Service (services/obd_service.py)

**Responsibility:** Real-time vehicle diagnostics via ELM327 adapter

```python
OBDService
├── _connect() → Establish USB serial connection
├── _polling_loop() → Background thread (5 sec interval)
│   ├── _poll_sensors() → Read OBD PIDs
│   ├── _check_dtcs() → Monitor trouble codes
│   └── _generate_simulated_data() → Fallback mode
└── Public API:
    ├── get_reading(sensor_name)
    ├── get_all_readings(priority)
    ├── get_dtcs()
    └── clear_dtcs()
```

**Data Model:**

```python
SensorReading (dataclass)
├── name: str              # Sensor name (e.g., "RPM")
├── value: float          # Reading value
├── unit: str             # Unit (e.g., "rpm")
├── timestamp: datetime   # When sampled
└── priority: int         # Display priority (1-3)
```

**Priority System:**
- **Priority 1:** Always visible (RPM, Speed, Temp, Voltage)
- **Priority 2:** Scrollable (Intake Temp, Throttle, O2)
- **Priority 3:** Deep diagnostics (Freeze frame, PIDs)

**Error Handling:**
- Graceful degradation if ELM327 not found
- Automatic simulated data generation
- Non-blocking connection attempts with retry logic

### 3. Camera Service (services/camera_service.py)

**Responsibility:** Video capture and recording management

```python
CameraService
├── _connect_camera() → Open /dev/video0 via OpenCV
├── _capture_loop() → Background thread (30 FPS)
│   ├── Video frame capture
│   ├── Rolling segment writer (30-min segments)
│   ├── _finalize_segment() → Close video file
│   └── _cleanup_old_segments() → Auto-delete old footage
├── toggle_manual_recording() → Save current segment
└── Public API:
    ├── cycle_camera()
    ├── get_current_frame() → JPEG bytes for display
    ├── save_current_segment()
    └── get_status()
```

**Recording Architecture:**

```
Rolling Buffer (1 hour max):
├── Segment 1: 00:00-00:30 [rolling, auto-delete]
└── Segment 2: 00:30-01:00 [rolling, auto-delete]

Manual Save:
├── saved_20260504_143012.mp4 [persistent]
└── saved_20260504_144523.mp4 [persistent]
```

**Storage Management:**
- 30-minute segments in H.264 MP4 format
- Rolling buffer auto-deletes oldest when max age reached
- Manual saves move to permanent directory
- Path: `logs/rolling_footage/` and `logs/saved_footage/`

### 4. GPIO Service (services/gpio_service.py)

**Responsibility:** Physical button and sensor input handling

```python
GPIOService
├── GPIO Pin definitions (enum)
│   ├── REVERSE_SIGNAL (GPIO 17)
│   ├── PAUSE_PLAY, SKIP_FORWARD, SKIP_BACK
│   ├── VOLUME_UP, VOLUME_DOWN
│   └── HOME_BUTTON, CAMERA_SKIP, RECORD, etc.
├── _polling_loop() → Non-blocking button scan (50 Hz)
│   ├── _check_reverse_signal() → Voltage divider monitor
│   └── _check_buttons() → Button debounce (50ms)
└── Public API:
    ├── register_callback(pin, callback)
    ├── register_reverse_callback(callback)
    ├── simulate_button_press() → Bench testing
    └── simulate_reverse_signal() → Bench testing
```

**Debounce Strategy:**
- 50ms minimum time between state changes
- Prevents false triggers from electrical noise
- Keyboard shortcuts simulate GPIO during bench testing

**Hardware Integration (Future):**
```
GPIO 17 Voltage Divider:
    12V (Reverse Light) ─────┬────── GND
                             │
                        10kΩ Resistor
                             │
                             ├──── GPIO 17 (3.3V safe)
                             │
                        5.6kΩ Resistor
                             │
                            GND
```

### 5. Audio Service (services/audio_service.py)

**Responsibility:** Music playback and volume control

```python
AudioService
├── PlaybackMode enum
│   ├── SPOTIFY_IPAD (primary)
│   └── MPD_LOCAL (fallback)
├── set_volume(level) → ALSA or MPD volume control
├── toggle_play() → Start/stop playback
├── next() / previous() → Track navigation
├── set_mode() → Switch audio source
└── Public API:
    ├── get_current_track_info()
    └── get_status()
```

**Volume Control Path:**
```
Spotify via iPad (Primary):
    iPad Audio Out (3.5mm)
        ↓
    Pi Volume Control (ALSA)
        ↓
    TPA3116 Amplifier
        ↓
    Factory Speakers

Local Music (Fallback):
    MPD Server (on Pi)
        ↓
    Pi Audio Out (3.5mm)
        ↓
    (Same amplifier path)
```

### 6. Data Logger Service (services/data_logger.py)

**Responsibility:** Sensor data persistence and trip analytics

```python
DataLogger
├── Session Management
│   ├── start_session() → Open CSV for logging
│   ├── log_sensor_data(dict) → Write row to CSV
│   └── end_session(odometer) → Close session, calc trip summary
├── Fuel Tracking
│   ├── log_fuel_fillup()
│   ├── get_fuel_economy() → Calculate MPG
│   └── _save_fuel_history() → Persist fillups
├── Trip History
│   ├── TripSummary dataclass
│   └── _save_trip_history()
└── Maintenance
    └── cleanup_old_logs(max_age_days)
```

**Data Models:**

```python
FuelFillup:
├── timestamp: ISO 8601
├── odometer_miles: float
├── gallons: float
├── cost: float (optional)
└── notes: str (optional)

TripSummary:
├── start_time, end_time
├── duration_minutes, distance_miles
├── avg_speed_mph, max_speed_mph
├── avg_rpm, max_rpm
├── avg_temp_f, max_temp_f
└── fuel_used_gallons
```

**CSV Storage:**
```
logs/diagnostics/
├── session_20260504_143012.csv    [sensor data @ 5s intervals]
├── fuel_tracking.csv              [fillup history]
├── trip_history.csv               [trip summaries]
└── [auto-cleanup after 30 days]
```

## Data Flow Diagrams

### OBD2 to Display Pipeline

```
ELM327 Adapter
     ↓ (Serial 38400 baud)
OBDService._polling_loop()
     ↓ (parse OBD frames)
SensorReading objects
     ↓ (store in dict)
latest_readings {}
     ↓ (UI thread reads)
DiagnosticsScreen.on_enter()
     ↓ (format for display)
Kivy Labels/TextInputs
     ↓
Display on 1280×800 monitor
```

### Camera to Storage Pipeline

```
USB Capture Card (/dev/video0)
     ↓ (OpenCV VideoCapture)
CameraService._capture_loop()
     ↓ (30 FPS frames)
VideoWriter (MP4 H.264)
     ↓ (30 min segments)
logs/rolling_footage/segment_*.mp4
     ↓ (manual record button)
logs/saved_footage/saved_*.mp4 [persistent]
     ↓ (on demand)
Display in CameraScreen
```

### Reverse Signal to Auto-Switch

```
12V Reverse Light
     ↓ (voltage divider)
GPIO 17 (3.3V)
     ↓ (50Hz polling)
GPIOService._check_reverse_signal()
     ↓ (state change detected)
reverse_callback(True)
     ↓ (UI event)
ScreenManager.current = 'camera'
     ↓
CameraScreen displayed automatically
```

## Threading Model

### Main Thread
- Kivy event loop (UI rendering)
- Keyboard event handling
- Screen transitions
- Frame rate: 60 FPS

### Background Threads

| Thread | Service | Interval | Purpose |
|--------|---------|----------|---------|
| OBD Polling | OBDService | 5 sec | Read sensors, check DTCs |
| Camera Capture | CameraService | ~33 ms (30 FPS) | Capture frames, write video |
| GPIO Polling | GPIOService | 20 ms (50 Hz) | Button scan, reverse detect |
| Data Logging | DataLogger | Per-sensor | Write CSV entries |

**Thread Safety:**
- Shared data in dictionaries (thread-safe for dict operations)
- Sensor readings use dataclass (immutable reads)
- CSV writes serialized in DataLogger thread
- No locks needed (CPython GIL + dict atomicity)

## Configuration System

```
config/settings.json
├── system
│   ├── hostname, volume, brightness
│   └── debug_mode (verbose logging)
├── obd2
│   ├── enabled, port, baudrate
│   └── logging_interval
├── camera
│   ├── device, resolution, fps
│   ├── rolling_segment_minutes
│   └── max_stored_hours
├── audio
│   ├── use_mpd, mpd_host, mpd_port
│   └── default_volume
├── gpio
│   ├── reverse_signal_pin
│   ├── use_gpio
│   └── gpio_mode (BCM/BOARD)
└── logging
    ├── enabled, log_file, log_level
    └── max_log_size_mb
```

**Loading:**
```python
APP_CONFIG = load_config()  # Loads at startup
# All services read their section from APP_CONFIG
```

## Error Handling Strategy

### Graceful Degradation

```
Hardware Missing:
ELM327 not found
    ↓
OBDService.connected = False
    ↓
_generate_simulated_data()
    ↓
UI displays random but realistic values
    ↓
User sees functional diagnostics
```

### Timeout Handling

```
Operation takes > X seconds:
    ↓
Non-blocking connection with timeout
    ↓
Exception caught and logged
    ↓
Thread retries after N seconds
    ↓
UI remains responsive
```

### State Recovery

```
Thread crashes:
    ↓
Exception logged with traceback
    ↓
Thread waits 5-10 seconds
    ↓
Automatic reconnection attempt
    ↓
Service continues (or stays degraded)
```

## Performance Considerations

### Memory Usage
- Image buffers: ~2 MB (720×480 JPEG)
- OBD readings: ~100 KB (typical ~50 sensors)
- Rolling buffer: Depends on rolling_segment_minutes config
- Estimated: 50-100 MB baseline + storage overhead

### CPU Usage
- Idle (UI only): 5-10%
- OBD polling: +2-3%
- Camera capture: +10-15%
- Video encoding: +15-20%
- Total (full load): ~40-50% on RPi 4B

### Network Impact
- SSH: Minimal (on-demand)
- WiFi: Only if connected to local router
- Cellular: Future feature (iPad only)

## Logging Architecture

```
logs/t1000.log
├── Format: TIMESTAMP - LOGGER - LEVEL - MESSAGE
├── Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
├── Handlers: File + Console
├── Max size: 50 MB (rollover)
└── Log locations:
    ├── main.py: Application lifecycle
    ├── services/*.py: Service operations
    ├── screens: Screen transitions
    └── diagnostics: Sensor data summaries
```

**Example Log Output:**
```
2026-05-04 14:32:15,123 - services.obd_service - INFO - OBDService initialized
2026-05-04 14:32:15,234 - services.camera_service - INFO - Camera connected: /dev/video0
2026-05-04 14:32:15,345 - services.gpio_service - INFO - GPIO polling started
2026-05-04 14:32:20,456 - services.obd_service - DEBUG - Polled RPM: 2450 rpm
2026-05-04 14:32:25,567 - services.data_logger - INFO - Logged 5 sensor readings
```

## Testing Architecture

```python
tests/test_services.py
├── TestOBDService
│   ├── test_init()
│   ├── test_get_reading()
│   └── test_dtc_descriptions()
├── TestCameraService
│   ├── test_init()
│   └── test_manual_recording()
├── TestGPIOService
│   ├── test_register_callback()
│   └── test_simulate_button_press()
├── TestAudioService
│   ├── test_set_volume()
│   └── test_switch_mode()
├── TestDataLogger
│   ├── test_start_session()
│   ├── test_log_sensor_data()
│   └── test_calculate_fuel_economy()
└── TestIntegration
    ├── test_multiple_services_init()
    └── test_gpio_triggers_ui_event()
```

**Coverage:**
- Service initialization
- Method return values
- Error conditions
- Data persistence
- Integration scenarios

## Future Architecture Enhancements

### Phase 2: Physical Controls
```
Rotary Encoders → GPIO (SPI/I2C)
     ↓
GPIOService processes
     ↓
Volume/Brightness updated
```

### Phase 3: Advanced Features
```
Ollama AI Server → Local inference
     ↓
Processes real-time sensor data
     ↓
Alerts on anomalies via TTS
```

### Phase 4: Remote Connectivity
```
iPad (cellular) ↔ Home Server (WiFi)
     ↓
Telemetry upload
     ↓
Web dashboard (future)
```

## Deployment Checklist

- [ ] All Python packages installed
- [ ] Kivy renders without errors
- [ ] Services start without crashing
- [ ] Unit tests pass (pytest)
- [ ] Keyboard controls respond
- [ ] Logs show expected messages
- [ ] SSH connection works
- [ ] No memory leaks after 1 hour
- [ ] CPU usage stable under load
- [ ] Temperature under 70°C
- [ ] Ready for Phase 2 integration

---

**Architecture Version:** 1.0  
**Last Updated:** 2026-05-04  
**Maintainer:** T1000 Development Team
