#!/bin/bash

# T1000 Infotainment System - Automated Setup Script for Raspberry Pi OS Bookworm
# Handles: system packages, Python environment, directory structure, config generation

set -e  # Exit on any error

echo "================================"
echo "T1000 Setup - Raspberry Pi OS"
echo "================================"
echo ""

# Step 1: Update system package lists
echo "[1/8] Updating package lists..."
sudo apt-get update -y

# Step 2: Install heavy compiled packages via apt (pre-built ARM binaries — no pip build needed)
echo "[2/8] Installing system + Python packages via apt..."
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-kivy \
    python3-numpy \
    python3-opencv \
    python3-matplotlib \
    python3-psutil \
    git \
    mpd \
    mpc \
    v4l-utils \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libharfbuzz0b \
    libopenjp2-7 \
    libtiff6 \
    libjbig0 \
    libzstd1 \
    libopus0 \
    libvorbis0a \
    libvorbisfile3 \
    libsndfile1

echo "[2/8] System packages installed"
echo ""

# Step 3: Upgrade pip, setuptools, wheel
echo "[3/8] Upgrading pip, setuptools, wheel..."
pip3 install --upgrade pip setuptools wheel --break-system-packages

echo "[3/8] pip/setuptools/wheel upgraded"
echo ""

# Step 4: Install lightweight pure-Python packages from requirements.txt
echo "[4/8] Installing Python packages from requirements.txt..."
pip3 install --break-system-packages -r requirements.txt

echo "[4/8] Python packages installed"
echo ""

# Step 5: Create directory structure
echo "[5/8] Creating directory structure..."
mkdir -p logs/diagnostics
mkdir -p logs/work_miles
mkdir -p logs/personal_miles
mkdir -p data
mkdir -p config
mkdir -p services
mkdir -p screens
mkdir -p tests
mkdir -p video_storage

echo "[5/8] Directories created"
echo ""

# Step 6: Enable SSH
echo "[6/8] Ensuring SSH is enabled..."
sudo systemctl enable ssh
sudo systemctl start ssh 2>/dev/null || true

echo "[6/8] SSH enabled"
echo ""

# Step 7: Generate config/settings.json if not present
echo "[7/8] Checking config/settings.json..."
if [ ! -f "config/settings.json" ]; then
    cat > config/settings.json << 'EOF'
{
  "obd2": {
    "port": "/dev/ttyUSB0",
    "baudrate": 38400,
    "polling_interval_seconds": 5,
    "timeout_seconds": 2
  },
  "camera": {
    "device": "/dev/video0",
    "resolution": [720, 480],
    "fps": 30,
    "rolling_segment_minutes": 30,
    "max_storage_hours": 1,
    "video_storage_path": "video_storage"
  },
  "gpio": {
    "use_gpio": false,
    "reverse_signal_pin": 17,
    "polling_hz": 50,
    "debounce_ms": 50
  },
  "audio": {
    "use_mpd": false,
    "audio_mode": "SPOTIFY_IPAD",
    "mpd_host": "localhost",
    "mpd_port": 6600,
    "default_volume": 50
  },
  "data_logging": {
    "enabled": true,
    "csv_path": "data/trips.csv",
    "log_interval_seconds": 5,
    "retention_days": 30
  },
  "gps": {
    "gpsd_host": "localhost",
    "gpsd_port": 2947
  },
  "ui": {
    "debug_mode": false,
    "window_size": [1024, 768],
    "fullscreen": false
  }
}
EOF
    echo "[7/8] config/settings.json created"
else
    echo "[7/8] config/settings.json already exists, skipping"
fi

echo ""

# Step 8: Create autostart entry so T1000 launches on desktop login
echo "[8/8] Setting up autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$AUTOSTART_DIR/t1000.desktop" << EOF
[Desktop Entry]
Type=Application
Name=T1000 Infotainment
Exec=bash -c 'cd $SCRIPT_DIR && DISPLAY=:0 python3 main.py >> $SCRIPT_DIR/logs/t1000_autostart.log 2>&1'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo "[8/8] Autostart configured — T1000 will launch on next login"
echo ""

echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To launch now:  cd $(pwd) && DISPLAY=:0 python3 main.py"
echo "Or log out and back in — autostart will handle it."
echo ""
