# T1000 Infotainment System - Raspberry Pi Edition

A comprehensive vehicle computing platform for a **1997 Toyota T100** pickup truck. This custom infotainment system replaces the factory head unit with a Raspberry Pi 4B-based system featuring live backup camera, OBD2 diagnostics, music control, and data logging.

## Project Overview

**T1000** is a modular, phase-gated implementation providing:
- **Phase 1 (Current):** Bench Testing - Software core + UI framework
- **Phase 2:** Power Harness & Vehicle Integration
- **Phase 3:** Physical Controls Installation
- **Phase 4:** Advanced Features (AI, solar backup, predictive fuel)

## Quick Start

### Prerequisites
- Raspberry Pi 4B 4GB RAM running Raspberry Pi OS (Desktop)
- Python 3.8+
- USB devices (when available): ELM327 OBD2 adapter, USB camera card
- Network access for initial setup

### Installation

1. **Clone/Download Project**
   ```bash
   cd ~/t1000
   ```

2. **Run Setup Script**
   ```bash
   bash setup.sh
   ```
   This automatically installs all system and Python dependencies.

3. **Verify Installation**
   ```bash
   python3 -c "import kivy; import cv2; import obd; print('✅ All dependencies OK')"
   ```

4. **Start Application**
   ```bash
   python3 main.py
   ```

## Project Structure

```
t1000/
├── main.py                    # Main Kivy application
├── requirements.txt           # Python dependencies
├── setup.sh                   # Automated setup script
├── config/
│   └── settings.json          # Configuration file
├── screens/
│   ├── __init__.py
│   ├── home_screen.py         # Main menu
│   ├── camera_screen.py       # Backup camera display
│   ├── music_screen.py        # Music player control
│   ├── diagnostics_screen.py  # OBD2 dashboard
│   └── navigation_screen.py   # Navigation placeholder
├── services/
│   ├── __init__.py
│   ├── obd_service.py         # OBD2 communication
│   ├── camera_service.py      # Video capture & recording
│   ├── gpio_service.py        # Button/sensor inputs
│   ├── audio_service.py       # Music control
│   └── data_logger.py         # Sensor logging & analytics
├── assets/
│   ├── fonts/
│   ├── icons/
│   └── maps/
├── config/
│   └── settings.json
├── logs/
│   ├── diagnostics/           # OBD2 historical data
│   ├── rolling_footage/       # Camera rolling buffer
│   └── saved_footage/         # Manual camera saves
├── tests/
│   └── test_services.py       # Unit tests
└── README.md                  # This file
```

## Usage Guide

### Keyboard Controls (Bench Testing)

| Function | Key | Purpose |
|----------|-----|---------|
| **Home** | `H` | Return to main menu |
| **Back** | `Esc` | Return to previous screen |
| **Up/Down** | Arrow Keys ↑↓ | Volume (music), Menu navigation |
| **Left/Right** | Arrow Keys ←→ | Previous/Next track (music) |
| **Play/Pause** | `Space` | Start/stop music |
| **Camera Toggle** | `C` | Switch between cameras |
| **Record** | `R` | Save camera footage |
| **Power** | `P` | Display on/off |
| **Brightness** | `B` / `Shift+B` | Increase/decrease brightness |
| **Select** | `Enter` | Activate menu item |

### Menu Navigation

#### Home Screen
- **Camera** - View live backup camera feed
- **Music** - Control music playback (Spotify or MPD)
- **Diagnostics** - View real-time OBD2 data
- **Navigation** - Map view (future feature)
- **Settings** - System configuration (coming soon)

#### Camera Screen
- Live feed from USB RCA→USB capture card
- Auto-records in 30-minute rolling segments
- Press **R** to save current + next hour of footage
- Press **C** to cycle between camera inputs

#### Music Screen
- Primary source: **Spotify via iPad** (aux audio)
- Fallback: **MPD** for local MP3 files on Pi
- Volume bar shows 0-100% level
- Use arrow keys to adjust volume

#### Diagnostics Screen
- **Priority 1 (Always Visible):** RPM, Speed, Engine Temp, Battery Voltage
- **Priority 2 (Scrollable):** Intake Temp, Throttle Position, Fuel Pressure, MAF, O2
- **Priority 3 (Deep Dive):** Freeze frame, all supported PIDs
- **Fuel Tracking:** Manual MPG calculation from fillups
- **Super Diagnostics:** Historical data analysis & anomaly detection

## Hardware Configuration

### Currently Owned
- ✅ Raspberry Pi 4B 4GB
- ✅ RCA backup camera (hitch mount)
- ✅ RCA-to-USB converter
- ✅ Portable 10" monitor
- ✅ Keyboard & mouse
- ✅ Sense HAT

### Need to Source
| Item | Est. Cost | Source |
|------|-----------|--------|
| USB Capture Card (UTV007) | $25-40 | Amazon |
| 12V-to-5V Buck Converter | $12-20 | Amazon |
| ELM327 OBD2 Adapter | $15-25 | Amazon/eBay |
| TPA3116 Mini Amplifier | $20-30 | Amazon |
| WiFi Router (TP-Link) | $35-50 | Walmart |
| 12V Cooling Fans (×2) | $16-30 | Amazon |
| Rotary Encoders | $15-25 | Amazon |
| Push Buttons | $10-15 | Amazon |

## Configuration

Edit `config/settings.json` to customize:

```json
{
  "obd2": {
    "enabled": true,
    "port": "/dev/ttyUSB0",
    "baudrate": 38400
  },
  "camera": {
    "device": "/dev/video0",
    "resolution": [720, 480],
    "fps": 30
  },
  "audio": {
    "use_mpd": false,
    "mpd_port": 6600
  }
}
```

## Testing

### Run Unit Tests
```bash
python -m pytest tests/test_services.py -v
```

### Run Specific Service Test
```bash
python -m pytest tests/test_services.py::TestOBDService -v
```

### Test Individual Service
```bash
# Test OBD service
python services/obd_service.py

# Test camera service
python services/camera_service.py

# Test GPIO service
python services/gpio_service.py
```

## Logging & Debugging

### Application Logs
```bash
# View real-time logs
tail -f logs/t1000.log

# Search for errors
grep ERROR logs/t1000.log
```

### OBD2 Data Logs
```bash
# Sensor data CSV files
ls logs/diagnostics/session_*.csv

# Fuel tracking history
cat logs/diagnostics/fuel_tracking.csv

# Trip history
cat logs/diagnostics/trip_history.csv
```

### Camera Footage
```bash
# Rolling buffer (auto-deleted after 1 hour)
ls logs/rolling_footage/

# Manually saved footage
ls logs/saved_footage/
```

## Troubleshooting

### OBD2 Not Connecting
1. Check ELM327 adapter is plugged in: `lsusb | grep FTDI`
2. Check port in settings: `ls /dev/tty*`
3. Verify baudrate (usually 38400)
4. Test with: `python services/obd_service.py`

### Camera Not Working
1. Check USB device: `ls /dev/video*`
2. Test with: `python services/camera_service.py`
3. Verify capture card drivers: `v4l2-ctl --list-devices`

### Missing Dependencies
1. Re-run: `bash setup.sh`
2. Or manually: `pip3 install -r requirements.txt --break-system-packages`

### Performance Issues
- Disable debug logging: Set `"debug_mode": false` in `config/settings.json`
- Reduce polling interval in services
- Use SSH connection instead of HDMI display
- Monitor CPU: `top` or `htop`

## SSH Access

Pre-configured for remote development:
```bash
ssh mc103.acprivilege@t1000.local
# Password: 1245
```

Or use VNC for remote desktop:
```bash
vncviewer t1000.local:1
```

## Development Notes

### Adding New Screens
1. Create `screens/new_screen.py` inheriting from `Screen`
2. Register in `main.py` ScreenManager
3. Add navigation button in HomeScreen

### Adding New Services
1. Create `services/new_service.py` with service class
2. Implement `start()` and `stop()` methods
3. Use threading for background operations
4. Add error handling and logging
5. Create unit tests in `tests/test_services.py`

### Extending Diagnostics
- Modify `DiagnosticsScreen` to add new data displays
- Update `OBDService` to log additional PIDs
- Extend `DataLogger` for new calculations

## Performance Specifications

| Component | Spec |
|-----------|------|
| CPU | Raspberry Pi 4B (ARM Cortex-A72) |
| RAM | 4 GB LPDDR4 |
| Storage | microSD card (32GB recommended) |
| Display | 1280×800 portable monitor |
| OBD2 | ELM327 v1.5 @ 38400 baud |
| Camera | 720×480 @ 30 FPS |
| Battery | Vehicle 12V system |

## Operating Conditions

- **Location:** Mississippi / Deep South USA
- **Temperature:** 40°F to 130°F (vehicle interior)
- **Mitigation:** Active cooling fans, heatsinks, thermal management

## Known Limitations

- 1997 T100 has limited OBD2 PID support (no fuel level)
- Manual fuel tracking required for economy calculations
- Backup camera is RCA analog (requires conversion)
- Local music requires MPD server running on Pi

## Future Enhancements (Phase 4)

- [ ] Offline AI assistant via Ollama
- [ ] Predictive fuel consumption ML model
- [ ] Solar panel + battery backup for post-engine-off processing
- [ ] iPad as secondary display (Type-C dock)
- [ ] Real-time weather integration
- [ ] Remote telemetry to home server
- [ ] Physical rotary encoder volume knob
- [ ] Custom 3D-printed control panel

## Support & Contact

**Project Owner:** Michael Carroll  
**Email:** michaelisme103@gmail.com  
**Vehicle:** 1997 Toyota T100 Pickup  
**Location:** Mississippi, USA

## License

This project is provided as-is for personal vehicle use. Modify and extend as needed.

## Changelog

### v1.0.0 (2026-05-04)
- Initial Phase 1 codebase generation
- All 5 main screens implemented
- Services for OBD2, camera, GPIO, audio, logging
- Comprehensive unit tests
- Setup automation
- Bench-testing ready

---

**Last Updated:** 2026-05-04  
**Status:** Phase 1 - Bench Testing (ACTIVE)
