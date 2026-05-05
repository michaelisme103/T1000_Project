#!/bin/bash
# T1000 Update Script
# Run this after SSH-ing in to pull latest files from the SD card boot partition
# Usage:  bash ~/T1000/update.sh

set -e

BOOT_SRC="/boot/firmware/T1000"
DEST="$HOME/T1000"

echo "==================================="
echo "T1000 Update from SD card"
echo "==================================="
echo ""

if [ ! -d "$BOOT_SRC" ]; then
    echo "ERROR: $BOOT_SRC not found. Is the SD card boot partition mounted?"
    exit 1
fi

echo "[1/3] Syncing files from $BOOT_SRC..."
rsync -av --delete \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='video_storage/' \
    --exclude='config/settings.json' \
    "$BOOT_SRC/" "$DEST/"
echo "[1/3] Files updated"
echo ""

echo "[2/3] Ensuring dependencies are installed..."
# Install kivy and heavy packages via apt if not already present
sudo apt-get install -y python3-kivy python3-psutil python3-numpy 2>/dev/null || true
pip3 install --break-system-packages -r "$DEST/requirements.txt" 2>/dev/null || true
echo "[2/3] Dependencies checked"
echo ""

echo "[3/4] Creating log directories..."
mkdir -p "$DEST/logs/diagnostics" "$DEST/logs/work_miles" "$DEST/logs/personal_miles"
mkdir -p "$DEST/data" "$DEST/video_storage"
echo "[3/4] Done"
echo ""

echo "[4/4] Setting hostname to t1000..."
sudo hostnamectl set-hostname t1000
sudo sed -i 's/127\.0\.1\.1.*/127.0.1.1\tt1000/' /etc/hosts
echo "[4/4] Hostname set — SSH as: mc103-1@t1000.local (after reboot)"
echo ""

echo "==================================="
echo "Update complete!"
echo "To launch:  cd ~/T1000 && DISPLAY=:0 python3 main.py"
echo "==================================="
