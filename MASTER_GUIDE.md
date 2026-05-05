# T1000 INFOTAINMENT SYSTEM - COMPLETE MASTER GUIDE

**All-in-one guide for implementation, testing, and development**

---

## 📑 TABLE OF CONTENTS

1. [Quick Start (5 Minutes)](#quick-start)
2. [Visual Setup Guide (45 Minutes)](#visual-setup-guide)
3. [Installation Details](#installation-details)
4. [Project Architecture](#project-architecture)
5. [Bench Testing Guide](#bench-testing-guide)
6. [Module Documentation](#module-documentation)
7. [Troubleshooting](#troubleshooting)
8. [Next Steps](#next-steps)

---

# QUICK START

## For the Impatient (3 Commands)

```bash
# 1. Get the code on your Pi
cd ~
unzip T1000_Phase1_Code.zip
cd T100

# 2. Install everything (takes 25 minutes)
bash setup.sh

# 3. Run it!
python3 main.py
```

**That's it.** T1000 will be running in ~30 minutes.

---

# VISUAL SETUP GUIDE

## Complete 45-Minute Setup (Step-by-Step with Diagrams)

### STEP 1: Flash Raspberry Pi OS (10 minutes)

#### What You Need
- Computer with SD card reader
- 32GB+ SD card
- Download: Raspberry Pi Imager from https://www.raspberrypi.com/software/

#### 1a. Download and Open Imager

```
https://www.raspberrypi.com/software/
       ↓
[Download for Windows/Mac/Linux]
       ↓
Open the application
```

#### 1b. Insert SD Card

```
Your Computer:
┌─────────────────────┐
│  SD Card Slot       │◄─── Insert SD card here
│  (gold side down)   │
└─────────────────────┘
```

#### 1c. Raspberry Pi Imager Main Screen

```
╔═══════════════════════════════════════════════╗
║      Raspberry Pi Imager - Main Window         ║
╟───────────────────────────────────────────────╢
║                                               ║
║  [Choose OS]                                  ║
║  → Raspberry Pi OS (Desktop)                  ║
║                                               ║
║  [Choose Storage]                             ║
║  → Your SD Card (32 GB)                       ║
║                                               ║
║  [Advanced Settings] ⚙️                        ║
║  → Click gear icon for configuration          ║
║                                               ║
║  [WRITE] (red button)                         ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

#### 1d. Advanced Settings Configuration

**Click the ⚙️ gear icon**

```
╔═══════════════════════════════════════════════╗
║         Advanced Options                      ║
╟───────────────────────────────────────────────╢
║                                               ║
║  ☑ Set hostname:                              ║
║    [t1000]                                    ║
║                                               ║
║  ☑ Enable SSH                                 ║
║                                               ║
║  ☑ Set username and password:                 ║
║    Username: [mc103.acprivilege]              ║
║    Password: [1245]                           ║
║                                               ║
║  ☑ Configure wireless LAN (optional)          ║
║    SSID: [your-wifi]                          ║
║    Password: [your-password]                  ║
║                                               ║
║  Timezone: [America/Chicago]                  ║
║  Keyboard: [us]                               ║
║                                               ║
║  [SAVE]                                       ║
║                                               ║
╚═══════════════════════════════════════════════╝

KEY SETTINGS:
✓ Hostname: t1000
✓ Username: mc103.acprivilege
✓ Password: 1245
✓ Enable SSH: ☑
✓ Timezone: America/Chicago
```

#### 1e. Click WRITE

```
╔═══════════════════════════════════════════════╗
║           Flashing in Progress                ║
╟───────────────────────────────────────────────╢
║                                               ║
║  Status: Flashing Raspberry Pi OS             ║
║                                               ║
║  ████████████████░░░░░░░  65%                 ║
║                                               ║
║  Estimated time: 5 minutes                    ║
║                                               ║
╚═══════════════════════════════════════════════╝

⏳ Wait 5-10 minutes
```

When done:

```
╔═══════════════════════════════════════════════╗
║         ✅ Write Complete!                     ║
║                                               ║
║  Raspberry Pi OS successfully flashed         ║
║                                               ║
║  [CONTINUE]                                   ║
╚═══════════════════════════════════════════════╝
```

**Eject SD card from computer**

---

### STEP 2: First Boot on Raspberry Pi (10 minutes)

#### 2a. Insert SD Card into Pi

```
Raspberry Pi 4B:
┌─────────────────────────────┐
│                             │
│  ◄──── SD Card Slot         │
│  (insert with gold side in) │
│                             │
│  [USB-C Power Port]         │
│  [HDMI Ports]               │
│  [Network Port]             │
│                             │
└─────────────────────────────┘
```

#### 2b. Connect Everything

```
Your Setup:
                    ┌─ HDMI Monitor
                    │
                    ↓
    ┌───────────────────────────────┐
    │   Raspberry Pi 4B             │
    │                               │
    │  ◄─ USB Keyboard              │
    │  ◄─ USB Mouse                 │
    │  ◄─ Ethernet Cable (or WiFi)  │
    │  ◄─ USB-C Power (3A+)         │
    └───────────────────────────────┘
```

#### 2c. Power On

**Connect USB-C power adapter**

Monitor will show:

```
[Raspberry Pi Logo]

Loading...

Welcome to Raspberry Pi Desktop!
```

After 60 seconds, you'll see:

```
╔═══════════════════════════════════════════════╗
║      Welcome to Raspberry Pi Setup             ║
╟───────────────────────────────────────────────╢
║                                               ║
║  This wizard will help you get started        ║
║                                               ║
║  ☑ Country (pre-configured)                   ║
║  ☑ Timezone (pre-configured)                  ║
║  ☑ Keyboard (pre-configured)                  ║
║  ☐ WiFi (optional)                            ║
║                                               ║
║  [Next]  [Skip]                               ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

Click **[Next]** or **[Skip]** - these are already configured.

After wizard completes:

```
╔═══════════════════════════════════════════════╗
║          Raspberry Pi Desktop                  ║
║  File  Edit  View  Help          [_][□][X]   ║
╟───────────────────────────────────────────────╢
║                                               ║
║   [Desktop with icons]                        ║
║                                               ║
║   [Taskbar: File Manager, Terminal, etc]      ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

✅ **Raspberry Pi is ready!**

---

### STEP 3: Transfer T1000 Code (5 minutes)

#### 3a. Open Terminal

Click the Terminal icon in taskbar:

```
Desktop Taskbar:
[File Manager] [Terminal] [Web Browser] ... [System Tray]
               ↓
              Click here
```

You'll see:

```
╔═══════════════════════════════════════════════╗
║ mc103.acprivilege@t1000:~ $                  ║
║                                               ║
║ [cursor]                                      ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

#### 3b. Get T1000 Code (Choose ONE method)

**METHOD A: Download from Internet (Easiest)**

```bash
mkdir ~/t1000
cd ~/t1000

# If you have a download link:
wget https://example.com/T1000_Phase1_Code.zip
unzip T1000_Phase1_Code.zip

# Move files out of subfolder if needed
mv T100/* .
rm -rf T100
```

**METHOD B: Copy from USB Drive**

```bash
# Insert USB drive with T1000_Phase1_Code.zip

mkdir ~/t1000
cd ~/t1000

# Check USB mount point
ls /media/pi/

# Copy (replace USB-NAME with actual name)
cp /media/pi/USB-NAME/T1000_Phase1_Code.zip .
unzip T1000_Phase1_Code.zip

# Move files
mv T100/* .
rm -rf T100
```

**METHOD C: Transfer from Another Computer via SCP**

From your computer (not the Pi):
```bash
scp -r T100/ mc103.acprivilege@t1000.local:~/t1000/
```

#### 3c. Verify Files

On the Pi terminal:

```bash
cd ~/t1000
ls -la
```

You should see:

```
mc103.acprivilege@t1000:~/t1000$ ls
ARCHITECTURE.md
BENCH_TESTING_GUIDE.md
INSTALLATION.md
MASTER_GUIDE.md
README.md
config/
main.py
requirements.txt
screens/
services/
setup.sh
tests/

✅ All files present!
```

---

### STEP 4: Install Dependencies (25 minutes)

#### 4a. Run Setup Script

```bash
bash setup.sh
```

You'll see tons of output:

```
╔═══════════════════════════════════════════════╗
║  Terminal Output                              ║
╟───────────────────────────────────────────────╢
║                                               ║
║  ==========================================   ║
║  T1000 Infotainment System - Setup Script     ║
║  ==========================================   ║
║                                               ║
║  📦 Updating system packages...               ║
║  Reading package lists... Done                ║
║  Building dependency tree... Done             ║
║  ...                                          ║
║                                               ║
║  📦 Installing system dependencies...         ║
║  Setting up python3-pip...                    ║
║  Setting up python3-dev...                    ║
║  Setting up libsdl2-dev...                    ║
║  Setting up libsdl2-image-dev...              ║
║  ...                                          ║
║                                               ║
║  📦 Installing Python packages...             ║
║  Collecting kivy==2.2.1                       ║
║  Downloading kivy-2.2.1-cp39...               ║
║  Installing collected packages...             ║
║  Successfully installed kivy opencv-python   ║
║  python-obd RPi.GPIO pandas numpy matplotlib ║
║  ...                                          ║
║                                               ║
║  📁 Creating project directory structure...   ║
║  🔐 Setting file permissions...               ║
║  🔌 Enabling SSH...                           ║
║  ⚙️  Creating default settings.json...         ║
║  📋 Setting up logging directories...         ║
║                                               ║
║  ==========================================   ║
║  ✅ T1000 Setup Complete!                     ║
║  ==========================================   ║
║                                               ║
║  mc103.acprivilege@t1000:~/t1000$            ║
║                                               ║
╚═══════════════════════════════════════════════╝

⏳ Total time: 20-30 minutes
   (Kivy compilation is longest step)
```

#### 4b. Verify Installation

```bash
python3 -c "import kivy; import cv2; import obd; print('✅ All OK')"
```

You should see:

```
mc103.acprivilege@t1000:~/t1000$ python3 -c "import kivy; import cv2; import obd; print('✅ All OK')"
✅ All OK
```

---

### STEP 5: Run T1000! (5 seconds)

#### 5a. Start the Application

```bash
python3 main.py
```

A Kivy window will open:

```
╔═══════════════════════════════════════════════╗
║         T1000 Infotainment System              ║
╟───────────────────────────────────────────────╢
║                                               ║
║                                               ║
║       T1000 Infotainment System                ║
║                                               ║
║                                               ║
║    ┌────────────────┬────────────────┐        ║
║    │                │                │        ║
║    │    Camera      │     Music      │        ║
║    │                │                │        ║
║    └────────────────┴────────────────┘        ║
║                                               ║
║    ┌────────────────┬────────────────┐        ║
║    │                │                │        ║
║    │ Diagnostics    │  Navigation    │        ║
║    │                │                │        ║
║    └────────────────┴────────────────┘        ║
║                                               ║
║    ┌────────────────┐                         ║
║    │                │                         ║
║    │  Settings      │                         ║
║    │                │                         ║
║    └────────────────┘                         ║
║                                               ║
║  Status: Ready | 14:32:15                    ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

#### 5b. Test Keyboard Controls

Press these keys:

```
H     → Stay on home screen (already here)
Esc   → Stay on home (can't go back from home)
C     → Go to Camera screen
D     → Go to Diagnostics screen
M     → Go to Music screen
H     → Back to home
```

✅ **SUCCESS! T1000 is running!**

---

# INSTALLATION DETAILS

## System Requirements

- **Hardware:** Raspberry Pi 4B with 4GB RAM
- **Storage:** 32GB+ microSD card (for rolling buffer)
- **OS:** Raspberry Pi OS (Desktop edition)
- **Power:** USB-C 3A+ power adapter
- **Display:** Monitor with HDMI (1280×800 or larger)
- **Input:** Keyboard and mouse (for initial setup)
- **Network:** Ethernet or WiFi (for dependency installation)

## Configuration File

Edit `config/settings.json` to customize:

```json
{
  "system": {
    "hostname": "t1000",
    "volume": 50,                    // 0-100
    "brightness": 80,                // 0-100
    "theme": "dark",
    "debug_mode": true               // Verbose logging
  },
  "obd2": {
    "enabled": true,
    "port": "/dev/ttyUSB0",          // ELM327 serial port
    "baudrate": 38400,
    "logging_interval": 5            // Seconds
  },
  "camera": {
    "enabled": true,
    "device": "/dev/video0",         // USB capture card
    "resolution": [720, 480],
    "fps": 30,
    "rolling_segment_minutes": 30,
    "max_stored_hours": 1
  },
  "audio": {
    "use_mpd": false,                // Use local music (true/false)
    "mpd_host": "localhost",
    "mpd_port": 6600
  },
  "gpio": {
    "reverse_signal_pin": 17,        // Reverse light detection
    "use_gpio": false                // Enable when buttons installed
  },
  "logging": {
    "enabled": true,
    "log_file": "logs/t1000.log",
    "log_level": "DEBUG",
    "max_log_size_mb": 50
  }
}
```

## Directory Structure After Installation

```
~/t1000/
├── main.py                    # Main application entry
├── setup.sh                   # Setup automation
├── requirements.txt           # Python dependencies
├── config/
│   └── settings.json          # Configuration
├── screens/
│   └── __init__.py            # Screen module
├── services/
│   ├── __init__.py
│   ├── obd_service.py         # OBD2 diagnostics
│   ├── camera_service.py      # Video capture
│   ├── gpio_service.py        # Button inputs
│   ├── audio_service.py       # Music control
│   └── data_logger.py         # Data logging
├── tests/
│   └── test_services.py       # Unit tests (25+)
├── logs/
│   ├── t1000.log              # Application logs
│   ├── diagnostics/           # OBD2 CSV data
│   ├── rolling_footage/       # Camera buffer
│   └── saved_footage/         # Permanent videos
├── assets/
│   ├── fonts/
│   ├── icons/
│   └── maps/
└── *.md files                 # Documentation
```

---

# PROJECT ARCHITECTURE

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    T1000 Application                     │
├─────────────────────────────────────────────────────────┤
│                      Kivy UI Layer                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ScreenManager                                   │   │
│  │  ├─ HomeScreen                                  │   │
│  │  ├─ CameraScreen                                │   │
│  │  ├─ MusicScreen                                 │   │
│  │  ├─ DiagnosticsScreen                          │   │
│  │  └─ NavigationScreen                           │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│           Background Service Layer (Threaded)           │
│  ┌─────────────┬──────────────┬──────────┬──────────┐  │
│  │ OBDService  │ CameraService│GPIOServ. │AudioServ.│  │
│  └─────────────┴──────────────┴──────────┴──────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │        DataLogger (CSV logging & analysis)       │  │
│  └──────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│           Hardware Abstraction Layer                    │
├─────────────────────────────────────────────────────────┤
│  USB Devices │ GPIO Pins │ Serial Ports │ Video Dev's   │
├─────────────────────────────────────────────────────────┤
│          Raspberry Pi 4B (ARM, 4GB RAM)                 │
└─────────────────────────────────────────────────────────┘
```

## Core Services

### 1. OBDService (services/obd_service.py)

**Purpose:** Real-time vehicle diagnostics via ELM327 OBD2 adapter

**Key Classes:**
```python
SensorReading       # Data class for individual sensor readings
OBDService          # Main service managing connection & polling
```

**Public Methods:**
```python
start()                          # Start background polling
stop()                           # Stop and cleanup
get_reading(sensor_name)         # Get single sensor
get_all_readings(priority=None)  # Get readings (filtered by priority)
get_dtcs()                       # Get trouble codes & descriptions
clear_dtcs()                     # Clear trouble codes
get_status()                     # Get service status
```

**Features:**
- Non-blocking connection with auto-retry
- 5-second polling interval
- Priority-based sensor organization (1-3)
- Simulated data fallback (no hardware needed)
- DTC tracking with announcement prevention
- Graceful degradation

**Sensor Priorities:**
- **Priority 1:** Always visible (RPM, Speed, Temp, Voltage)
- **Priority 2:** Scrollable (Intake Temp, Throttle, O2)
- **Priority 3:** Deep dive (Freeze frame, all PIDs)

### 2. CameraService (services/camera_service.py)

**Purpose:** Video capture and rolling buffer recording

**Key Classes:**
```python
CameraService       # Manages video capture and recording
```

**Public Methods:**
```python
start()                          # Start capture thread
stop()                           # Stop and cleanup
cycle_camera()                   # Switch to next camera
toggle_manual_recording()        # Toggle save mode
get_current_frame()              # Get JPEG bytes for display
save_current_segment()           # Save rolling segment
get_status()                     # Get service status
```

**Features:**
- 720×480 @ 30 FPS capture
- 30-minute rolling buffer segments
- 1-hour max rolling storage (auto-delete old)
- Manual save to permanent directory
- Multi-camera support (up to 2)
- H.264 MP4 encoding

**Recording Flow:**
```
Rolling Buffer (Auto-Delete):
├─ Segment 1: 00:00-00:30 [oldest, deleted first]
└─ Segment 2: 00:30-01:00 [newest]

Manual Save:
├─ saved_20260504_143012.mp4
└─ saved_20260504_144523.mp4 [persistent]
```

### 3. GPIOService (services/gpio_service.py)

**Purpose:** Physical button and sensor input handling

**Key Classes:**
```python
GPIOPin             # Enum of all GPIO pin definitions
GPIOService         # Manages polling and callbacks
```

**GPIO Pin Definitions:**
```python
GPIO 17   → Reverse signal (12V→3.3V voltage divider)
GPIO 22   → Pause/Play button
GPIO 23   → Skip Forward button
GPIO 24   → Skip Back button
GPIO 25   → Volume Up
GPIO 26   → Volume Down
GPIO 27   → Home button
GPIO 4    → Camera Skip
GPIO 5    → Record button
GPIO 6    → Power button
GPIO 12   → Brightness Up
GPIO 13   → Brightness Down
```

**Public Methods:**
```python
start()                                    # Start polling
stop()                                     # Stop and cleanup
register_callback(pin, callback)           # Register button callback
register_reverse_callback(callback)        # Register reverse signal
simulate_button_press(pin)                 # For bench testing
simulate_reverse_signal(active)            # For bench testing
get_status()                               # Get service status
```

**Features:**
- 50 Hz polling (20ms interval)
- 50ms debounce for button stability
- Non-blocking I/O
- Reverse signal auto-triggers camera screen
- Bench testing simulation mode
- Callback-based event system

### 4. AudioService (services/audio_service.py)

**Purpose:** Music playback and volume control

**Key Classes:**
```python
PlaybackMode        # Enum: SPOTIFY_IPAD or MPD_LOCAL
AudioService        # Manages audio sources and controls
```

**Public Methods:**
```python
start()                          # Initialize
stop()                           # Cleanup
set_volume(level)                # Set volume 0-100
get_volume()                     # Get current volume
play()                           # Start playback
pause()                          # Pause playback
toggle_play()                    # Toggle play/pause
next()                           # Next track
previous()                       # Previous track
set_mode(PlaybackMode)           # Switch audio source
get_current_track_info()         # Get track metadata
get_status()                     # Get service status
```

**Audio Sources:**
- **Spotify via iPad (Primary):** Audio through 3.5mm aux to TPA3116 amp
- **MPD Local (Fallback):** Local MP3s on Pi with MPD server

**Volume Control Path:**
```
Source Audio → ALSA Volume Control → TPA3116 Amp → Speakers
```

### 5. DataLogger (services/data_logger.py)

**Purpose:** Sensor data persistence and trip analytics

**Key Classes:**
```python
FuelFillup          # Data class for fillup record
TripSummary         # Data class for trip statistics
DataLogger          # Manages logging and analysis
```

**Public Methods:**
```python
start_session()                          # Open new log file
stop_session()                           # Close and summarize
log_sensor_data(sensor_dict)             # Write to CSV
log_fuel_fillup(...)                     # Record fillup
get_fuel_economy()                       # Calculate MPG
cleanup_old_logs(max_age_days)           # Delete old logs
get_status()                             # Get service status
```

**Data Models:**
```python
FuelFillup:
  timestamp, odometer_miles, gallons,
  cost (optional), notes (optional)

TripSummary:
  start_time, end_time, duration_minutes,
  distance_miles, avg_speed_mph, max_speed_mph,
  avg_rpm, max_rpm, avg_temp_f, max_temp_f
```

**CSV Storage:**
```
logs/diagnostics/
├─ session_20260504_143012.csv    [5-sec intervals]
├─ fuel_tracking.csv              [fillup history]
├─ trip_history.csv               [trip summaries]
└─ [auto-cleanup after 30 days]
```

## Data Flow

### OBD2 Pipeline
```
ELM327 (Serial 38400 baud)
    ↓
OBDService._polling_loop()
    ↓
Parse OBD frames → SensorReading objects
    ↓
Store in latest_readings{}
    ↓
DiagnosticsScreen reads on-demand
    ↓
Format for display → Kivy Labels
    ↓
Monitor shows real-time data
```

### Camera Pipeline
```
USB Capture Card (/dev/video0)
    ↓
OpenCV VideoCapture (30 FPS)
    ↓
CameraService._capture_loop()
    ↓
Write frames to MP4 (H.264)
    ↓
30-min segments in rolling_footage/
    ↓
Auto-delete when >1 hour old
    ↓
Display in CameraScreen on-demand
```

### Reverse Signal Pipeline
```
12V Reverse Light
    ↓
Voltage Divider (10kΩ + 5.6kΩ) → 3.3V
    ↓
GPIO 17 (50 Hz polling)
    ↓
GPIOService detects HIGH
    ↓
Calls reverse_callback(True)
    ↓
ScreenManager.current = 'camera'
    ↓
CameraScreen auto-displays
```

## Threading Model

### Main Thread
- Kivy event loop (UI rendering at 60 FPS)
- Keyboard event handling
- Screen transitions
- Frame rate: 60 FPS

### Background Threads

| Service | Interval | Purpose |
|---------|----------|---------|
| OBDService | 5 sec | Read sensors, check DTCs |
| CameraService | ~33 ms (30 FPS) | Capture frames, encode video |
| GPIOService | 20 ms (50 Hz) | Poll buttons, reverse signal |
| DataLogger | Per-operation | Write CSV entries |

**Thread Safety:**
- Shared data in thread-safe dict structures
- Sensor readings are immutable dataclasses
- CSV writes serialized in logger thread
- CPython GIL + dict atomicity = no locks needed

---

# BENCH TESTING GUIDE

## Testing Each Screen

### Home Screen

**What it does:**
- Main menu with 5 button options
- Status bar showing time and state
- Navigation hub

**Test:**
```bash
# Press H from any screen
# Should return to home

# Click each button
# Should navigate to: Camera, Music, Diagnostics, Navigation, Settings
```

### Camera Screen

**What it does:**
- Live video from USB capture card
- Recording in 30-minute segments
- Camera cycling
- Rolling buffer management

**Test (without camera hardware):**
```bash
# Navigate to Camera screen
# Press C → Toggle between Camera 1 and Camera 2
# Press R → Toggle recording (button changes color)

# Terminal logs should show:
# "Switched to camera X"
# "Recording started"
# "Recording stopped"
```

**With USB capture card:**
```bash
# Check device exists
v4l2-ctl --list-devices

# Test capture
ffplay /dev/video0

# Should show live video from backup camera
```

### Music Screen

**What it does:**
- Control music playback
- Adjust volume (0-100%)
- Navigate tracks
- Show now-playing info

**Test:**
```bash
# Navigate to Music screen
# Press Space → Toggle play/pause
# Press ↑/↓ → Adjust volume (watch bar update)
# Press →/← → Next/previous track

# For Spotify: No special setup (audio handled via iPad aux)
# For MPD: Configure "use_mpd": true in settings.json
```

### Diagnostics Screen

**What it does:**
- Real-time OBD2 sensor display
- Priority 1 data (RPM, Speed, Temp, Voltage)
- Scrollable Priority 2 & 3 data
- Check Engine Light detection
- Fuel tracking
- Super diagnostics mode

**Test (without OBD2 adapter):**
```bash
# Navigate to Diagnostics screen
# See simulated sensor values updating
# RPM: 700-3000 (random)
# Speed: 0-65 MPH (random)
# Temp: 160-210°F (random)
# Voltage: 12.0-14.5V (random)

# Click buttons:
# "More Data" → Shows Priority 2 sensors
# "Fuel Track" → Shows MPG and fuel data
# "Super Diag" → Shows historical analysis

# Terminal logs show:
# "Polled RPM: XXXX rpm"
# "Polled SPEED: XX mph"
# etc.
```

**With ELM327 adapter:**
```bash
# Check adapter connected
lsusb | grep FTDI

# Verify port
ls -la /dev/ttyUSB*

# Run OBD service standalone
python3 services/obd_service.py

# Should show real vehicle data:
# RPM: 1200 rpm
# SPEED: 35 mph
# COOLANT_TEMP: 190°F
# BATTERY_VOLTAGE: 13.2V
```

### Navigation Screen

**What it does:**
- Placeholder for future GPS/offline maps
- Shows "Coming Soon" message
- Lists future features

**Test:**
```bash
# Navigate to Navigation screen
# See placeholder message
# Click Back (H) → Return to home
```

## Keyboard Control Reference

```
H                    Home (always returns to home)
Esc                  Back (from any non-home screen)
↑ (Up Arrow)         Volume Up (music) or Menu Up (home)
↓ (Down Arrow)       Volume Down (music) or Menu Down (home)
→ (Right Arrow)      Next Track (music)
← (Left Arrow)       Previous Track (music)
Space                Play/Pause (music)
C                    Camera Screen
D                    Diagnostics Screen
R                    Record Toggle (camera screen)
P                    Power (experimental)
B                    Brightness Up
Shift+B              Brightness Down
Enter                Select Menu Item
```

## Running Unit Tests

```bash
# Run all tests
python3 -m pytest tests/test_services.py -v

# Run specific test class
python3 -m pytest tests/test_services.py::TestOBDService -v

# Run with coverage
python3 -m pytest tests/test_services.py --cov=services

# Run one test
python3 -m pytest tests/test_services.py::TestOBDService::test_init -v
```

**Expected Output:**
```
test_services.py::TestOBDService::test_init PASSED
test_services.py::TestOBDService::test_get_reading PASSED
test_services.py::TestCameraService::test_init PASSED
...
======================== 25 passed in X.XXs =========================
```

## Monitoring Logs

```bash
# Real-time log view
tail -f logs/t1000.log

# Count errors
grep ERROR logs/t1000.log | wc -l

# View warnings
grep WARNING logs/t1000.log

# Live filter for DEBUG messages
tail -f logs/t1000.log | grep DEBUG
```

**Example Log Output:**
```
2026-05-04 14:32:15,123 - main - INFO - T1000 Application initializing
2026-05-04 14:32:15,234 - services.obd_service - INFO - OBDService initialized
2026-05-04 14:32:15,345 - services.camera_service - INFO - CameraService initialized
2026-05-04 14:32:20,456 - services.obd_service - DEBUG - Polled RPM: 2450 rpm
2026-05-04 14:32:25,567 - services.data_logger - INFO - Logged 5 sensor readings
```

---

# MODULE DOCUMENTATION

## main.py - Kivy Application

**Entry Point:** The main Kivy application that manages all screens and keyboard input

**Classes:**
```python
HomeScreen(Screen)         # Main menu (5 buttons)
CameraScreen(Screen)       # Live camera feed
MusicScreen(Screen)        # Music player controls
DiagnosticsScreen(Screen)  # OBD2 dashboard
NavigationScreen(Screen)   # Map placeholder
T1000App(App)              # Main application class
```

**Key Methods:**
```python
T1000App.build()           # Initialize UI
T1000App.on_keyboard()     # Handle keyboard input
```

**Keyboard Mapping:**
- `H` → Home screen
- `Esc` → Back/previous screen
- Arrow keys → Navigation
- `Space` → Play/Pause
- `C` → Camera
- `R` → Record
- `D` → Diagnostics

**Features:**
- ScreenManager for seamless transitions
- Non-blocking keyboard event handling
- 1280×800 display optimized UI
- Status bar showing time and state

## services/obd_service.py - OBD2 Diagnostics

**Purpose:** Communicate with vehicle via ELM327 OBD2 adapter

**Key Classes:**
```python
SensorReading           # Data class holding single reading
OBDService              # Main service class
```

**Initialization:**
```python
obd = OBDService(
    port='/dev/ttyUSB0',    # Serial port
    baudrate=38400          # Serial speed
)
obd.start()                 # Start polling thread
```

**Reading Sensor Data:**
```python
# Get single sensor
reading = obd.get_reading('RPM')
# Returns: SensorReading object or None

# Get all readings
all_readings = obd.get_all_readings()
# Returns: dict of all sensor readings

# Get priority 1 only (always-visible)
priority1 = obd.get_all_readings(priority=1)
```

**Trouble Code Handling:**
```python
# Get active DTCs
dtcs = obd.get_dtcs()
# Returns: {'P0301': 'Cylinder 1 Misfire...', ...}

# Clear DTCs
obd.clear_dtcs()
```

**Error Handling:**
- Missing ELM327 adapter → Simulated data
- Serial connection timeout → Automatic retry
- Unsupported PID → Logged and skipped

## services/camera_service.py - Video Capture

**Purpose:** Capture video from USB RCA→USB converter

**Key Classes:**
```python
CameraService           # Main camera service
```

**Initialization:**
```python
camera = CameraService(
    device='/dev/video0',           # Camera device
    resolution=(720, 480),          # Width × Height
    fps=30,                         # Frames per second
    rolling_segment_minutes=30,     # Segment duration
    max_stored_hours=1              # Max rolling storage
)
camera.start()                      # Start capture thread
```

**Recording:**
```python
# Auto rolling segments every 30 minutes
# Old segments auto-delete when >1 hour total

# Save current segment to permanent storage
camera.save_current_segment()

# Get current frame as JPEG bytes
jpeg_bytes = camera.get_current_frame()

# Cycle between cameras
camera.cycle_camera()
```

**File Organization:**
```
logs/
├─ rolling_footage/        # Auto-managed rolling buffer
│  ├─ segment_20260504_143000.mp4
│  └─ segment_20260504_143030.mp4
└─ saved_footage/          # Manually saved videos
   ├─ saved_20260504_143012.mp4
   └─ saved_20260504_144523.mp4
```

## services/gpio_service.py - Button Input

**Purpose:** Monitor physical buttons and reverse signal

**Key Classes:**
```python
GPIOPin                 # Enum of all GPIO pins
GPIOService             # Button polling service
```

**Initialization:**
```python
gpio = GPIOService(
    use_gpio=False,         # Set to True when buttons wired
    gpio_mode='BCM'         # BCM or BOARD numbering
)
gpio.start()                # Start polling thread
```

**Button Callbacks:**
```python
# Register callback for button press
def on_pause():
    print("Play/Pause pressed!")

gpio.register_callback(GPIOPin.PAUSE_PLAY, on_pause)

# When button pressed, callback is called
```

**Reverse Signal:**
```python
# Register reverse signal callback
def on_reverse(active):
    if active:
        print("Reverse detected - switch to camera!")

gpio.register_reverse_callback(on_reverse)
```

**Bench Testing:**
```python
# Simulate button press (for keyboard)
gpio.simulate_button_press(GPIOPin.PAUSE_PLAY)

# Simulate reverse signal
gpio.simulate_reverse_signal(True)
```

## services/audio_service.py - Music Control

**Purpose:** Control music playback and volume

**Key Classes:**
```python
PlaybackMode            # Enum: SPOTIFY_IPAD or MPD_LOCAL
AudioService            # Audio control service
```

**Initialization:**
```python
audio = AudioService(
    use_mpd=False,          # False for Spotify, True for MPD
    mpd_host='localhost',   # MPD server
    mpd_port=6600           # MPD port
)
```

**Volume Control:**
```python
audio.set_volume(75)        # Set to 75%
current = audio.get_volume()  # Get current volume

# Volume controls actual Pi audio output
# For Spotify: controls aux volume to amp
# For MPD: controls MPD volume
```

**Playback Control:**
```python
audio.play()                # Start playback
audio.pause()               # Pause playback
audio.toggle_play()         # Toggle play/pause
audio.next()                # Next track
audio.previous()            # Previous track
```

**Mode Switching:**
```python
# Switch to Spotify mode
audio.set_mode(PlaybackMode.SPOTIFY_IPAD)

# Switch to local music
audio.set_mode(PlaybackMode.MPD_LOCAL)

# Get current track info
info = audio.get_current_track_info()
# Returns: {'track': '', 'artist': '', 'album': '', 'mode': ''}
```

## services/data_logger.py - Data Logging

**Purpose:** Log sensor data and generate analytics

**Key Classes:**
```python
FuelFillup              # Data class for fillup record
TripSummary             # Data class for trip statistics
DataLogger              # Logging service
```

**Logging Sessions:**
```python
logger = DataLogger()

# Start logging
logger.start_session()

# Log sensor readings (call every 5 seconds)
logger.log_sensor_data({
    'rpm': 2000,
    'speed_mph': 45,
    'coolant_temp_f': 190,
    'battery_voltage': 13.2
})

# End session and get summary
trip = logger.end_session(final_odometer=150)
print(trip.distance_miles)  # 10 miles
print(trip.avg_speed_mph)   # 36.5 mph
```

**Fuel Tracking:**
```python
# Log a fillup event
logger.log_fuel_fillup(
    odometer=150,
    gallons=10,
    cost=35.50,
    notes="At Shell station"
)

# Calculate average MPG
mpg = logger.get_fuel_economy()
# Returns: 15.2 (average across all fillups)
```

**Data Export:**
```
logs/diagnostics/
├─ session_20260504_143012.csv     # Sensor readings @ 5s
├─ fuel_tracking.csv               # Fillup history
└─ trip_history.csv                # Trip summaries
```

---

# TROUBLESHOOTING

## Common Issues

### Issue: "ImportError: No module named 'kivy'"

**Solution:**
```bash
pip3 install --break-system-packages kivy
```

### Issue: "Error: OBDService connected = False"

**Meaning:** ELM327 adapter not found (expected in bench testing)

**Solution:** This is normal behavior:
- System falls back to simulated data
- UI shows random but realistic values
- When ELM327 is connected, real data will appear automatically

### Issue: "No module named 'cv2'"

**Solution:**
```bash
pip3 install --break-system-packages opencv-python
```

### Issue: "Permission denied" when running setup.sh

**Solution:**
```bash
chmod +x setup.sh
bash setup.sh
```

### Issue: "setup.sh is taking forever"

**Meaning:** Kivy is compiling (15-20 minutes is normal)

**Solution:**
- Don't interrupt it
- Be patient ☕
- Monitor with: `top` in another SSH session

### Issue: "USB device not recognized"

**Check what's connected:**
```bash
lsusb
# Look for FTDI (OBD2), UTV (camera), etc.
```

**Check serial ports:**
```bash
ls /dev/tty*
# ELM327 should appear as /dev/ttyUSB0 or /dev/ttyACM0
```

### Issue: "Camera not working"

**Check video devices:**
```bash
v4l2-ctl --list-devices
# Should show /dev/video0 with USB capture card
```

**Test capture:**
```bash
ffplay /dev/video0
# Should show live video
```

### Issue: "Terminal closed before setup finished"

**Resume setup:**
```bash
cd ~/t1000
# Setup script is idempotent - safe to run again
bash setup.sh
```

### Issue: "High CPU usage"

**Check processes:**
```bash
top -b -n 1 | head -15
# Find what's using CPU
```

**Reduce CPU load:**
```bash
# Edit config/settings.json
"debug_mode": false         # Disable verbose logging
"logging_interval": 10      # Increase OBD polling to 10 sec
```

### Issue: "Temperature too high (>80°C)"

**Check:**
```bash
vcgencmd measure_temp
# If >80°C:
# 1. Ensure cooling fan is running
# 2. Add heatsink to RAM
# 3. Reduce polling intervals
# 4. Set debug_mode to false
```

### Issue: "Out of disk space"

**Check:**
```bash
df -h
# If full, clean old logs:
rm logs/diagnostics/session_*.csv
rm logs/rolling_footage/*.mp4
```

### Issue: "WiFi not connecting"

**Use Ethernet instead** (more reliable)

**Or configure manually:**
```bash
sudo raspi-config
# Wireless LAN → Select your SSID → Enter password
```

---

# NEXT STEPS

## After Successful Phase 1 Testing

### 1. Verify All Screens Work
```bash
# Test each screen in running application
H       → Home
C       → Camera (see "[Camera Feed]" placeholder)
M       → Music (see "[Waiting for Spotify...]")
D       → Diagnostics (see sensor data updating)
N       → Navigation (see "[Coming Soon]")
H       → Back to home
```

### 2. Monitor Logs
```bash
# In another terminal/SSH session
tail -f logs/t1000.log

# Should see continuous entries:
# INFO - Screen displayed
# DEBUG - Sensor readings
# INFO - Button callbacks
```

### 3. Run Unit Tests
```bash
python3 -m pytest tests/test_services.py -v

# All 25+ tests should pass
# ===================== 25 passed in X.XXs =======================
```

### 4. Document Any Issues
```bash
# Capture your log for troubleshooting
cp logs/t1000.log ~/t1000_diagnostics.log
# Keep this file for reference
```

## Prepare for Phase 2

### Phase 2 Tasks (Vehicle Integration):

1. **Power Harness Design**
   - 12V switched ignition line → Buck converter (12V→5V)
   - USB-C 5V → Raspberry Pi
   - Wiring diagram in vehicle

2. **GPIO Wiring**
   - Reverse light signal → Voltage divider → GPIO 17
   - Push buttons → GPIO pins 22-27
   - Rotary encoders (future)

3. **Audio Integration**
   - 3.5mm audio out from Pi
   - TPA3116 amplifier input
   - Factory speaker wiring

4. **Camera Mounting**
   - Hitch mount for backup camera
   - RCA cable routing through vehicle
   - USB capture card under dashboard

5. **Physical Installation**
   - Console mounting bracket
   - Control panel design
   - Cable management
   - Thermal management

### Reading List

After Phase 1, review:
1. `ARCHITECTURE.md` - Technical deep dive
2. `BENCH_TESTING_GUIDE.md` - Advanced testing features
3. `services/obd_service.py` - OBD2 implementation
4. `services/camera_service.py` - Video recording logic
5. `services/data_logger.py` - Analytics features

### Development

To extend T1000:

1. **Add New Screen**
   ```python
   class NewScreen(Screen):
       def __init__(self, **kwargs):
           super().__init__(**kwargs)
           self.name = 'newscreen'
           # Add widgets
       def go_home(self, instance):
           self.manager.current = 'home'
   
   # In main.py: self.sm.add_widget(NewScreen())
   ```

2. **Add New Service**
   ```python
   class NewService:
       def __init__(self):
           self.data = {}
       def start(self):
           self.thread = threading.Thread(target=self._loop)
           self.thread.start()
       def _loop(self):
           while self.is_running:
               # Do work
               time.sleep(interval)
   ```

3. **Add Unit Test**
   ```python
   class TestNewService:
       def test_init(self):
           service = NewService()
           assert service is not None
   ```

---

# QUICK REFERENCE CARDS

## Keyboard Shortcuts (Bench Testing)

```
Navigation        Music Control         Utilities
───────────────   ─────────────────────  ─────────────
H    = Home       Space = Play/Pause     Esc  = Back
↑↓   = Menu Nav   ←→   = Prev/Next       C    = Camera
     & Volume     +/-  = Volume Adj      R    = Record
Enter = Select                           P    = Power
```

## Common Terminal Commands

```bash
# Start application
python3 main.py

# Run tests
python3 -m pytest tests/test_services.py -v

# Monitor logs
tail -f logs/t1000.log

# Check hardware
lsusb                    # Connected devices
ls /dev/video*          # Camera devices
ls /dev/ttyUSB*         # Serial devices
v4l2-ctl --list-devices # Video capture cards

# Temperature
vcgencmd measure_temp

# Disk usage
df -h

# SSH from another computer
ssh mc103.acprivilege@t1000.local
```

## File Locations

```
~/t1000/
├── main.py                      # Application
├── setup.sh                     # Installer
├── config/settings.json         # Configuration
├── services/                    # Backend services
│   ├── obd_service.py
│   ├── camera_service.py
│   ├── gpio_service.py
│   ├── audio_service.py
│   └── data_logger.py
├── tests/test_services.py       # Unit tests
├── logs/
│   ├── t1000.log                # Application logs
│   ├── diagnostics/             # OBD2 CSV data
│   ├── rolling_footage/         # Camera rolling buffer
│   └── saved_footage/           # Permanent videos
└── *.md files                   # Documentation
```

## Configuration Quick Edit

```bash
# Edit settings
nano config/settings.json

# Change common settings:
"debug_mode": false              # Reduce CPU/logs
"use_gpio": true                # Enable hardware buttons (when wired)
"rolling_segment_minutes": 60   # Longer video segments
"max_stored_hours": 2           # More rolling footage
```

---

# GETTING HELP

## Error Message Flowchart

```
Error occurs?
    ↓
Read the error message carefully
    ↓
Does it contain "ModuleNotFound" or "ImportError"?
    │ YES → Run: pip3 install --break-system-packages [module]
    │ NO  → Continue
    ↓
Check logs: tail -f logs/t1000.log
    ↓
Does it mention hardware connection?
    │ YES → Check lsusb, ls /dev/tty*, v4l2-ctl
    │ NO  → Continue
    ↓
Is it a performance issue?
    │ YES → Set debug_mode=false, check top
    │ NO  → Continue
    ↓
Check TROUBLESHOOTING section above
    ↓
Still stuck? Review logs carefully
```

## Useful Debug Info to Collect

```bash
# If reporting issues, collect:
uname -a                         # OS info
python3 --version              # Python version
cat ~/t1000/config/settings.json  # Configuration
lsusb                           # Hardware
df -h                           # Disk space
vcgencmd measure_temp           # Temperature
tail -100 logs/t1000.log        # Recent logs
```

---

# LICENSE & CREDITS

**Project:** T1000 Infotainment System  
**Version:** Phase 1 - Bench Testing  
**For:** 1997 Toyota T100 Pickup  
**Owner:** Michael Carroll  
**Email:** michaelisme103@gmail.com  
**Location:** Mississippi, USA  

**Built with:**
- Raspberry Pi 4B (ARM64)
- Python 3.8+
- Kivy 2.2.1 (UI framework)
- OpenCV (computer vision)
- python-obd (OBD2 communication)
- RPi.GPIO (hardware control)

---

# QUICK START SUMMARY

```
┌─────────────────────────────────────────────────────┐
│           T1000 Installation Flow                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Flash Raspberry Pi OS to SD card              │
│     (10 minutes)                                  │
│                                                     │
│  2. Insert SD card, boot Pi                       │
│     (10 minutes)                                  │
│                                                     │
│  3. Transfer T1000_Phase1_Code.zip to Pi          │
│     (5 minutes)                                   │
│                                                     │
│  4. Extract and run: bash setup.sh                │
│     (25 minutes - be patient!)                    │
│                                                     │
│  5. Run: python3 main.py                          │
│     (5 seconds - application starts!)             │
│                                                     │
│  TOTAL TIME: ~50 minutes                          │
│                                                     │
│  ✅ T1000 is now running on your Pi!             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Generated:** May 4, 2026  
**Last Updated:** May 4, 2026  
**Status:** Phase 1 - Bench Testing Ready  

**Questions?** Check the TROUBLESHOOTING section or review logs with `tail -f logs/t1000.log`

---

*This guide contains everything needed to implement, test, and develop T1000 on your Raspberry Pi 4B. Good luck! 🚀*
