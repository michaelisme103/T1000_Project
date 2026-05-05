# T1000 Bench Testing Guide

Complete walkthrough for testing the T1000 infotainment system without vehicle integration or physical hardware.

## What You'll Need

✅ **Included with this repository:**
- All Python source code
- Kivy UI framework
- Simulated OBD2 data
- Simulated camera data
- GPIO simulation layer

❓ **Optional hardware for enhanced testing:**
- ELM327 OBD2 adapter (real diagnostics)
- USB camera card + RCA camera (real camera feed)
- Bluetooth speaker or audio output (music tests)

## Phase 1 Setup (Bench Testing)

### Step 1: Install Dependencies

On your Raspberry Pi 4B:

```bash
# Navigate to project directory
cd ~/t1000

# Run setup script (installs all packages)
bash setup.sh

# Verify installation
python3 -c "import kivy; import cv2; print('✅ Ready!')"
```

This will:
- Install system libraries (SDL2, ffmpeg, etc)
- Install Python packages (kivy, opencv, python-obd, etc)
- Create directory structure
- Enable SSH daemon
- Set up logging directories

### Step 2: Run the Application

```bash
python3 main.py
```

You should see:
- Kivy window opening with T1000 home screen
- 5 colored buttons: Camera, Music, Diagnostics, Navigation, Settings
- Status bar at bottom showing "Status: Ready"

### Step 3: Test Keyboard Navigation

**Home Screen:**
- Press **H** → Should already be on home screen
- Press **Esc** → Should stay on home screen (it's the default)

**Navigate between screens using buttons:**
- Click **Camera** button or press **C** key
- Click **Music** button
- Click **Diagnostics** button
- Click **Navigation** button

**Return to Home:**
- Press **H** key from any screen
- Click **Back (H)** button

## Testing Each Screen

### 1. Camera Screen

**What it does:**
- Displays live video from USB capture card
- Allows recording in 30-minute segments
- Supports cycling between multiple cameras
- Auto-manages rolling buffer (max 1 hour)

**Bench Testing (without camera hardware):**

```bash
# The UI will show:
# "[Camera Feed - OpenCV Output]"
# "Waiting for USB capture card..."
# "Device: /dev/video0"
```

**Test Controls:**
1. Navigate to Camera screen
2. Press **C** key → Should toggle between "Camera 1" and "Camera 2"
3. Press **R** key → Should toggle recording on/off
   - Button changes color to red when recording
   - Status text shows "⏹ Recording... (R)"
4. Press **H** key → Return to home
5. Press **Esc** → Also returns to home

**With USB Camera (Optional):**
```bash
# Check if camera is connected
v4l2-ctl --list-devices

# Test capture
python services/camera_service.py
```

### 2. Music Screen

**What it does:**
- Controls music playback (Spotify via iPad or MPD)
- Adjusts volume from 0-100%
- Shows now-playing info
- Skip forward/back tracks

**Bench Testing:**

```bash
# Start the app
python3 main.py
# Navigate to Music screen
```

**Test Controls:**
1. **Volume Control:**
   - Press **Up Arrow** (↑) → Volume increases by 5%
   - Press **Down Arrow** (↓) → Volume decreases by 5%
   - Volume bar shows visual indicator

2. **Playback Control:**
   - Press **Space** → Play button changes to "⏸ Pause"
   - Play again → Changes back to "▶ Play"
   - Status changes: "Playback started" / "Playback paused"

3. **Track Navigation:**
   - Press **Left Arrow** (←) → Status shows "Previous track requested"
   - Press **Right Arrow** (→) → Status shows "Next track requested"

4. **Return Home:**
   - Press **H** → Back to home screen

**With Spotify iPad (Optional):**
```bash
# No special setup needed - system just controls volume
# Audio feeds through 3.5mm aux to TPA3116 amp
# Test actual volume control with speakers connected
```

**With Local Music (Optional):**
```bash
# Start MPD server
sudo systemctl start mpd

# Load music library
echo "playlist" | mpc listall | mpc add

# Set use_mpd to true in config/settings.json
# Then restart application
```

### 3. Diagnostics Screen

**What it does:**
- Displays OBD2 sensor data in real-time
- Shows Priority 1 data always (RPM, Speed, Temp, Voltage)
- Scrollable access to Priority 2 & 3 data
- Detects Check Engine Light codes
- Tracks fuel economy
- Performs historical analysis

**Bench Testing:**

```bash
python3 main.py
# Navigate to Diagnostics screen
```

**Initial State:**
```
Status: Connecting to OBD2 adapter...
RPM: 0
Speed: 0 MPH
Engine Temp: --°F
Battery: 12.5V
```

**Test Controls:**

1. **Without OBD2 Adapter (Simulated Data):**
   - System auto-generates random sensor values every 5 seconds
   - RPM ranges: 700-3000
   - Speed ranges: 0-65 MPH
   - Engine Temp ranges: 160-210°F
   - Values update automatically

2. **View More Data:**
   - Click **More Data** button or press arrow keys
   - Shows Priority 2 sensors:
     ```
     Intake Temp: --°F | Throttle: 0% | Fuel Press: -- PSI
     ```

3. **Fuel Tracking:**
   - Click **Fuel Track** button
   - Shows MPG, range, last fillup info
   - In real app: manually enter fillup data

4. **Super Diagnostics:**
   - Click **Super Diag** button
   - Shows charts and historical analysis
   - Highlights anomalies and trends

**With ELM327 Adapter (Optional):**
```bash
# Verify adapter is connected
lsusb | grep FTDI

# Check serial port
ls /dev/ttyUSB*

# Test OBD connection
python services/obd_service.py

# Should show real vehicle data:
# RPM: 1200
# SPEED: 35 mph
# COOLANT_TEMP: 190°F
# BATTERY_VOLTAGE: 13.2V
```

### 4. Navigation Screen

**What it does:**
- Placeholder for future offline map system
- Will integrate OpenStreetMap tiles
- Future: GPS, turn-by-turn guidance

**Bench Testing:**

```bash
# Navigate to Navigation screen
# You'll see:
# "[Navigation Coming Soon]"
# "Future features:
#  • Offline OpenStreetMap tiles
#  • GPS integration
#  • Turn-by-turn guidance
#  • Route planning"
```

### 5. Home Screen

**What it does:**
- Main menu showing all available systems
- Status indicators
- System state at bottom

**Bench Testing:**

```bash
# Default on startup
# Shows:
# - Title: "T1000 Infotainment System"
# - 5 buttons in grid: Camera, Music, Diagnostics, Navigation, Settings
# - Status bar: "Status: Ready"
```

**Test Navigation:**
```bash
# From any screen, press H → Returns to home
# On home, press Esc → Stays on home (it's the default)
# Click any button or use arrow keys + Enter to navigate
```

## Testing All Keyboard Shortcuts

Create a checklist and verify each control:

```
✓ H = Home (always returns to menu)
✓ Esc = Back (returns from any screen except home)
✓ Space = Play/Pause (music only)
✓ Up/Down Arrows = Volume (music) or Navigate (menu)
✓ Left/Right Arrows = Previous/Next track (music)
✓ C = Camera toggle (camera screen)
✓ R = Record toggle (camera screen)
✓ P = Power (experimental)
✓ B / Shift+B = Brightness (experimental)
✓ Enter = Select menu item
```

## Testing With Simulated Hardware

### Simulate GPIO Button Press

```python
# In Python REPL on the Pi
from services.gpio_service import GPIOService, GPIOPin

gpio = GPIOService(use_gpio=False)
gpio.register_callback(GPIOPin.PAUSE_PLAY, lambda: print("Play!"))
gpio.simulate_button_press(GPIOPin.PAUSE_PLAY)
# Output: Play!
```

### Simulate Reverse Signal

```python
from services.gpio_service import GPIOService

gpio = GPIOService(use_gpio=False)
gpio.register_reverse_callback(lambda x: print(f"Reverse: {x}"))
gpio.simulate_reverse_signal(True)
# Output: Reverse: True
# Expected: Should trigger auto-switch to camera screen
```

### Simulate OBD2 Data

```bash
# Run OBD service standalone
python services/obd_service.py

# Shows simulated sensor readings:
# RPM: 2450 rpm
# SPEED: 55 mph
# COOLANT_TEMP: 195°F
# BATTERY_VOLTAGE: 13.1V
```

## Running Unit Tests

```bash
# Run all tests
python -m pytest tests/test_services.py -v

# Run specific test
python -m pytest tests/test_services.py::TestOBDService -v

# Run with coverage
python -m pytest tests/test_services.py --cov=services
```

**Expected Output:**
```
test_services.py::TestOBDService::test_init PASSED
test_services.py::TestOBDService::test_get_reading_nonexistent PASSED
test_services.py::TestCameraService::test_init PASSED
test_services.py::TestGPIOService::test_simulate_button_press PASSED
...
======================== X passed in Y.XXs ========================
```

## Monitoring Logs

### Real-Time Monitoring

```bash
# Watch logs as app runs
tail -f logs/t1000.log

# Filter for errors
tail -f logs/t1000.log | grep ERROR

# Count messages by level
grep -c DEBUG logs/t1000.log
grep -c INFO logs/t1000.log
grep -c ERROR logs/t1000.log
```

### Log Sample Output

```
2026-05-04 14:32:15,123 - __main__ - INFO - ==========================================
2026-05-04 14:32:15,124 - __main__ - INFO - T1000 Infotainment System - Starting
2026-05-04 14:32:15,125 - __main__ - INFO - ==========================================
2026-05-04 14:32:15,234 - __main__ - INFO - Configuration loaded successfully
2026-05-04 14:32:16,456 - __main__ - INFO - T1000 Application initializing
2026-05-04 14:32:18,789 - __main__ - INFO - T1000 Application built successfully
2026-05-04 14:32:19,012 - services.obd_service - INFO - OBDService initialized
2026-05-04 14:32:20,345 - screens.home_screen - INFO - Home screen displayed
```

## Remote Testing via SSH

### Connect from Another Computer

```bash
# SSH into Raspberry Pi
ssh mc103.acprivilege@t1000.local
# Password: 1245

# Run application remotely
python3 main.py

# Or run in screen for disconnection tolerance
screen -S t1000
python3 main.py
# Detach: Ctrl+A, D
# Reattach: screen -r t1000
```

### VNC Remote Desktop

```bash
# From another computer
vncviewer t1000.local:1

# Then click to interact with T1000 UI as if you were at the keyboard
```

## Next Steps: Integration Testing

Once bench testing is complete, you're ready for:

1. **Phase 2:** Power Harness & Vehicle Integration
   - Connect 12V switched ignition
   - Install buck converter (12V→5V)
   - Wire voltage divider for reverse signal
   - Mount in vehicle console

2. **Phase 3:** Physical Controls
   - Install rotary encoders for volume/brightness
   - Mount push buttons for controls
   - Design custom control panel

3. **Phase 4:** Advanced Features
   - Ollama AI integration
   - Predictive fuel consumption
   - Solar backup power
   - iPad secondary display

## Troubleshooting

### Application Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check imports
python3 -c "import kivy; import cv2; import obd; print('OK')"

# Check configuration
cat config/settings.json

# Reinstall if corrupted
pip3 install --upgrade --force-reinstall kivy --break-system-packages
```

### High CPU Usage

```bash
# Monitor CPU
top -b -n 1 | head -20

# Reduce polling intervals in services
# Set debug_mode to false in config/settings.json
# Disable verbose logging
```

### Display Issues

```bash
# Check display resolution
fbset  # Frame buffer settings

# Resize window
# Edit main.py, change Window.size = (1280, 800)

# Fullscreen mode
# Edit config/settings.json: "fullscreen": true
```

### Git Status (Version Control)

```bash
# Initialize git repo
git init
git add .
git commit -m "T1000 Phase 1 - Bench Testing Complete"

# Create branch for your modifications
git checkout -b feature/my-enhancement
```

## Success Criteria

You've successfully completed Phase 1 bench testing when:

- ✅ Application starts without errors
- ✅ All 5 screens navigate correctly
- ✅ All keyboard controls work as documented
- ✅ Simulated OBD2 data displays and updates
- ✅ Unit tests pass (pytest)
- ✅ Logs show expected activity (tail -f logs/t1000.log)
- ✅ No crashes during 10+ minute continuous operation
- ✅ CPU usage stays below 50% at idle
- ✅ Temperature stays below 70°C (heatsink helps)
- ✅ SSH access confirmed working

## Next: Phase 2 Planning

After bench testing validates the software architecture, proceed to:

```bash
# Create Phase 2 branch
git checkout -b phase2/vehicle-integration

# Document hardware modifications needed
cat PHASE2_PLAN.md
```

---

**Last Updated:** 2026-05-04  
**Testing Status:** Ready for bench validation  
**Next Phase:** Vehicle integration after software verification
