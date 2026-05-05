# T1000 Installation & Setup Guide

Complete step-by-step installation guide for T1000 on Raspberry Pi 4B with Raspberry Pi OS.

## Prerequisites

- Raspberry Pi 4B with 4GB RAM
- microSD card (32GB+ recommended for rolling buffer space)
- Raspberry Pi OS (Desktop edition) flashed to SD card
- Keyboard and mouse (for initial setup)
- Portable 10" monitor (or HDMI display)
- Network connectivity (Ethernet or WiFi)

## Initial Raspberry Pi OS Setup

### 1. Flash Operating System

```bash
# On your computer, download Raspberry Pi Imager
# https://www.raspberrypi.com/software/

# Use it to flash Raspberry Pi OS (Desktop) to microSD card
# Configuration during flashing:
# - Set hostname: t1000
# - Set username: mc103.acprivilege
# - Set password: 1245
# - Enable SSH
# - Configure WiFi (if applicable)
```

### 2. First Boot Configuration

```bash
# Insert microSD, power on Pi with keyboard/mouse attached
# Complete initial setup wizard
# Set timezone to US/Chicago (Mississippi Central Time)

# Open terminal (Ctrl+Alt+T)
sudo raspi-config

# Navigate to:
# - Interface Options > SSH > Enable
# - Interface Options > VNC > Enable (optional)
# - Localization > Timezone > America > Chicago

# Exit and reboot
sudo reboot
```

### 3. Update System

```bash
# After reboot, open terminal
sudo apt update
sudo apt upgrade -y
sudo apt clean

# Reboot if kernel updated
sudo reboot
```

## T1000 Installation

### Option A: Automated Setup (Recommended)

```bash
# Download or clone the project
cd ~
git clone <repository-url> t1000
cd t1000

# Run automated setup script
bash setup.sh

# Script will:
# ✓ Update package lists
# ✓ Install system dependencies
# ✓ Install Python packages
# ✓ Create directory structure
# ✓ Configure settings.json
# ✓ Enable SSH daemon
# ✓ Set file permissions

# Verify installation
python3 -c "import kivy; import cv2; import obd; print('✅ All OK')"
```

### Option B: Manual Installation

#### Step 1: Install System Dependencies

```bash
# Update and upgrade
sudo apt update
sudo apt upgrade -y

# Install build tools
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    build-essential \
    git

# Install Kivy dependencies
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    libfreetype6-dev

# Install audio/video tools
sudo apt install -y \
    mpd \
    mpc \
    ffmpeg \
    v4l-utils

# Install image libraries
sudo apt install -y \
    libopenjp2-7 \
    libtiff6 \
    libharfbuzz0b \
    libwebp6
```

#### Step 2: Install Python Packages

```bash
# Upgrade pip
pip3 install --upgrade pip setuptools wheel

# Install Python dependencies
pip3 install --break-system-packages -r requirements.txt

# This includes:
# - kivy (UI framework)
# - opencv-python (computer vision)
# - python-obd (OBD2 diagnostics)
# - RPi.GPIO (GPIO control)
# - pandas, numpy (data processing)
# - matplotlib (charts/graphs)
# - pyttsx3 (text-to-speech)
# - pytest (testing)
```

#### Step 3: Configure Project

```bash
# Create project directory
mkdir -p ~/t1000
cd ~/t1000

# Copy all files (assumes you have them)
# wget <repo-link>/archive/main.zip
# unzip main.zip && mv t1000-main/* .

# Create directory structure
mkdir -p {screens,services,config,assets/{fonts,icons,maps},logs/{diagnostics,rolling_footage,saved_footage},tests}
touch screens/__init__.py services/__init__.py

# Create settings
cat > config/settings.json << 'EOF'
{
  "system": {
    "hostname": "t1000",
    "volume": 50,
    "brightness": 80,
    "theme": "dark",
    "debug_mode": true
  },
  "obd2": {
    "enabled": true,
    "port": "/dev/ttyUSB0",
    "baudrate": 38400
  },
  "camera": {
    "enabled": true,
    "device": "/dev/video0",
    "resolution": [720, 480],
    "fps": 30
  },
  "gpio": {
    "reverse_signal_pin": 17,
    "use_gpio": false
  }
}
EOF

# Set permissions
chmod +x setup.sh main.py
chmod 755 -R logs/
```

#### Step 4: Enable SSH

```bash
# Start SSH daemon
sudo systemctl enable ssh
sudo systemctl start ssh

# Verify
sudo systemctl status ssh

# Test remote connection (from another computer)
ssh mc103.acprivilege@t1000.local
# Password: 1245
```

## Verification

### Test Installation

```bash
# Check all imports work
python3 << 'EOF'
import kivy
import cv2
import obd
import RPi.GPIO
import pandas
import numpy
import matplotlib
import pytest
print("✅ All imports successful")
print(f"Kivy: {kivy.__version__}")
print(f"OpenCV: {cv2.__version__}")
EOF

# Check GPIO mode
python3 -c "import RPi.GPIO; print(f'GPIO module available')"

# Test OBD service
python3 services/obd_service.py &
sleep 5
pkill -f obd_service.py

# Test camera service
python3 services/camera_service.py &
sleep 5
pkill -f camera_service.py

# Run unit tests
python3 -m pytest tests/test_services.py -v
```

### Check Directory Structure

```bash
# Verify all directories exist
cd ~/t1000
ls -la

# Expected:
# drwxr-xr-x  config/
# drwxr-xr-x  screens/
# drwxr-xr-x  services/
# drwxr-xr-x  assets/
# drwxr-xr-x  logs/
# drwxr-xr-x  tests/
# -rwxr-xr-x  main.py
# -rwxr-xr-x  setup.sh
# -rw-r--r--  requirements.txt
# -rw-r--r--  README.md
```

## First Run

### Start Application

```bash
cd ~/t1000
python3 main.py
```

You should see:
- Kivy window opens with T1000 logo/title
- Home screen with 5 buttons (Camera, Music, Diagnostics, Navigation, Settings)
- Status bar showing "Status: Ready"

### Test Controls

```bash
# From the running application:
H       → Verify Home screen always accessible
Esc     → Try from different screens
Space   → Go to Music, test play/pause
↑/↓     → Volume adjustment (music screen)
←/→     → Previous/next track
C       → Camera screen toggle
R       → Camera record toggle
```

### Monitor Logs

```bash
# In another terminal/SSH session
tail -f logs/t1000.log

# Watch for successful initialization:
# INFO - Configuration loaded successfully
# INFO - OBDService initialized
# INFO - T1000 Application initializing
# INFO - T1000 Application built successfully
```

## Configuration Customization

Edit `config/settings.json` to customize:

```json
{
  "system": {
    "volume": 50,           // 0-100
    "brightness": 80,       // 0-100
    "debug_mode": true      // verbose logging
  },
  "obd2": {
    "port": "/dev/ttyUSB0", // Serial port for ELM327
    "baudrate": 38400       // Usually 38400
  },
  "camera": {
    "device": "/dev/video0",    // Camera device
    "resolution": [720, 480],   // Width x Height
    "fps": 30                   // Frames per second
  },
  "audio": {
    "use_mpd": false,       // Enable local music
    "mpd_port": 6600        // MPD server port
  },
  "gpio": {
    "use_gpio": false       // Set to true when controls installed
  }
}
```

## Autostart on Boot (Optional)

### Create Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/t1000.service > /dev/null << 'EOF'
[Unit]
Description=T1000 Infotainment System
After=network.target

[Service]
Type=simple
User=mc103.acprivilege
WorkingDirectory=/home/mc103.acprivilege/t1000
ExecStart=/usr/bin/python3 /home/mc103.acprivilege/t1000/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

# Enable and test
sudo systemctl daemon-reload
sudo systemctl enable t1000.service
sudo systemctl start t1000.service

# Check status
sudo systemctl status t1000.service

# View logs
journalctl -u t1000.service -f
```

### Or Use cron (Alternative)

```bash
# Edit crontab
crontab -e

# Add line:
@reboot sleep 5 && cd ~/t1000 && /usr/bin/python3 main.py
```

## Troubleshooting

### Import Errors

```bash
# If imports fail, reinstall with break-system-packages
pip3 install --break-system-packages --upgrade -r requirements.txt

# Check Kivy specifically
pip3 install --break-system-packages --force-reinstall kivy
```

### GPIO Not Available

```bash
# This is normal in test environment
# Set use_gpio to false in config/settings.json
# GPIO will work automatically when physical pins are wired
```

### OBD2 Adapter Not Found

```bash
# Check if ELM327 is connected
lsusb | grep FTDI

# List USB devices
ls -la /dev/ttyUSB*

# If not found, driver may be needed:
sudo apt install -y ftdi-eeprom libftdi-dev

# Update port in config/settings.json to match
```

### Camera Not Detected

```bash
# List video devices
v4l2-ctl --list-devices

# If no devices, ensure USB capture card is connected
# Test with:
ffplay /dev/video0

# Or check with OpenCV
python3 << 'EOF'
import cv2
cap = cv2.VideoCapture(0)
print(f"Camera connected: {cap.isOpened()}")
cap.release()
EOF
```

### High Memory Usage

```bash
# Check memory
free -h

# Monitor processes
ps aux --sort=-%mem | head -10

# Reduce rolling buffer size in config/settings.json:
# "max_stored_hours": 0.5  (instead of 1)

# Disable debug logging:
# "debug_mode": false
```

### Display Issues

```bash
# Check HDMI/Monitor
tvservice -s

# If display not detected:
sudo rpi-eeprom-update -u

# Force HDMI output
sudo tvservice -p
fbset -depth 32 -res 1280 800

# Edit /boot/config.txt if needed
sudo nano /boot/config.txt
# Add: hdmi_force_hotplug=1
```

## Performance Optimization

### Reduce CPU Load

```bash
# Disable unneeded services
sudo systemctl disable cups.service
sudo systemctl disable avahi-daemon.service

# Reduce swap (if low on RAM)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change: CONF_SWAPSIZE=100  (from 2048)
sudo dphys-swapfile setup
```

### Temperature Management

```bash
# Monitor temperature
watch -n 1 vcgencmd measure_temp

# If above 80°C:
# - Ensure cooling fan is running
# - Add heatsink
# - Reduce polling intervals in services
# - Set "debug_mode": false in config
```

### SD Card Health

```bash
# Check SD card health
sudo smartctl -a /dev/mmcblk0

# Monitor writes
iotop -o

# Reduce writes by moving logs to RAM disk:
# (Advanced topic - see separate guide)
```

## Network Setup

### Static IP (Optional)

```bash
# Edit DHCP configuration
sudo nano /etc/dhcpcd.conf

# Add at end:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8

# Reboot
sudo reboot

# Verify
ip addr show
```

### SSH Configuration

```bash
# SSH is enabled by default
# Test from another computer:
ssh mc103.acprivilege@t1000.local

# For passwordless login (advanced):
# Generate key on client, copy to ~/.ssh/authorized_keys
ssh-keygen -t rsa -b 4096
ssh-copy-id mc103.acprivilege@t1000.local
```

## Backup & Recovery

### Create Backup

```bash
# Backup entire SD card (on another computer with Linux)
sudo dd if=/dev/sdX of=t1000_backup.img bs=4M
# Replace /dev/sdX with actual SD card device

# Or backup important files only:
tar -czf t1000_config_backup.tar.gz ~/t1000/config/ ~/t1000/logs/
```

### Restore from Backup

```bash
# Restore full image
sudo dd if=t1000_backup.img of=/dev/sdX bs=4M
sudo sync

# Or restore files:
tar -xzf t1000_config_backup.tar.gz -C ~/
```

## Next Steps

1. **Bench Testing** → See `BENCH_TESTING_GUIDE.md`
2. **Hardware Integration** → See `PHASE2_PLAN.md` (after validation)
3. **Development** → Modify screens/services as needed
4. **Testing** → Run `pytest` after changes

## Support

- **Documentation:** See `README.md` for feature overview
- **Logs:** Check `logs/t1000.log` for debugging
- **Issues:** Create GitHub issues for bugs/features
- **Contact:** michaelisme103@gmail.com

---

**Installation Status:** Complete  
**Version:** Phase 1 - Bench Testing  
**Last Updated:** 2026-05-04
