# T1000 Quick Start - Visual Setup Guide

**Complete illustrated guide from blank SD card to running T1000 on your Raspberry Pi 4B**

---

## 🎯 Overview: 45-Minute Setup Process

```
Blank SD Card
     ↓ (Step 1: Flash OS - 10 min)
Raspberry Pi OS installed
     ↓ (Step 2: Transfer Code - 5 min)
T1000 code on Pi
     ↓ (Step 3: Install Dependencies - 25 min)
All packages installed
     ↓ (Step 4: Run Application - 5 sec)
T1000 Running!
```

---

# STEP 1: Flash Raspberry Pi OS (10 minutes)

## What You Need
- Computer (Windows, Mac, or Linux)
- SD card (32GB+ recommended)
- SD card reader (or USB adapter)
- Download: Raspberry Pi Imager

## What You'll See

### 1a. Download Raspberry Pi Imager

**On your computer, go to:**
```
https://www.raspberrypi.com/software/
```

**You'll see:**
```
╔════════════════════════════════════════════════════════════╗
║                  Raspberry Pi Imager                        ║
║                                                            ║
║  Download for Windows / Mac / Linux                       ║
║                                                            ║
║  [DOWNLOAD BUTTON]                                        ║
╚════════════════════════════════════════════════════════════╝
```

**Click the download button** for your operating system.

### 1b. Insert SD Card

**Insert your SD card into your computer's card reader:**

```
┌─────────────────────────────┐
│   Your Computer             │
│                             │
│   ┌─────────────────┐       │
│   │  SD Card Slot   │◄──────┼─── Insert SD Card here
│   └─────────────────┘       │
│                             │
└─────────────────────────────┘
```

### 1c. Open Raspberry Pi Imager

**After downloading, open the application:**

```
╔════════════════════════════════════════════════════════════╗
║            Raspberry Pi Imager - Main Window                ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │                                                        │ ║
║  │  [Choose OS]  Raspberry Pi OS (Desktop)              │ ║
║  │               (64-bit ARM version)                    │ ║
║  │                                                        │ ║
║  │  [Choose Storage] Your SD Card                        │ ║
║  │                                                        │ ║
║  │                                                        │ ║
║  │  [Advanced Settings] ⚙️  Click this gear icon       │ ║
║  │                                                        │ ║
║  │  [WRITE] (red button) - Click to start               │ ║
║  │                                                        │ ║
║  └──────────────────────────────────────────────────────┘ ║
╚════════════════════════════════════════════════════════════╝
```

### 1d. Select Operating System

**Click "Choose OS"**

```
What you'll see:
┌─────────────────────────────────┐
│ Raspberry Pi OS (Desktop)  ← Click this
├─────────────────────────────────┤
│ Raspberry Pi OS (Lite)
├─────────────────────────────────┤
│ Other general-purpose OS
├─────────────────────────────────┤
│ Erase (format card)
└─────────────────────────────────┘

✓ Select: Raspberry Pi OS (Desktop) 64-bit
```

### 1e. Select Storage (SD Card)

**Click "Choose Storage"**

```
You'll see your SD card listed:

┌─────────────────────────────────────────┐
│ Your SD Card (32 GB)  ← Click this      │
├─────────────────────────────────────────┤
│ (other drives will be listed)            │
└─────────────────────────────────────────┘

⚠️ WARNING: Choose the correct drive!
   Selecting wrong drive will erase your computer!
```

### 1f. Configure Settings (IMPORTANT!)

**Click the ⚙️ gear icon in Advanced Settings**

```
╔════════════════════════════════════════════════════════════╗
║         Advanced Options Configuration                      ║
║                                                            ║
║  ☑ Set hostname                                           ║
║    Hostname: [t1000____________]  ← Enter: t1000          ║
║                                                            ║
║  ☑ Enable SSH                                             ║
║                                                            ║
║  ☑ Set username and password                              ║
║    Username: [mc103.acprivilege____]                      ║
║    Password: [1245_____________]                          ║
║                                                            ║
║  ☑ Configure wireless LAN (optional)                       ║
║    SSID: [your wifi name______]                           ║
║    Password: [your wifi password___]                      ║
║                                                            ║
║  Set locale settings                                      ║
║    Timezone: [America/Chicago]  ← Select this             ║
║    Keyboard layout: [us]        ← Should be default        ║
║                                                            ║
║  [SAVE] [CANCEL]                                          ║
╚════════════════════════════════════════════════════════════╝

Key settings to change:
  • Hostname: t1000
  • Username: mc103.acprivilege
  • Password: 1245
  • Enable SSH: ✓ (checked)
  • Timezone: America/Chicago
```

**After entering settings, click [SAVE]**

### 1g. Write to SD Card

**Back on main window, click [WRITE]**

```
╔════════════════════════════════════════════════════════════╗
║                  Writing to SD Card...                      ║
║                                                            ║
║  Status: Flashing Raspberry Pi OS                         ║
║                                                            ║
║  ████████████████░░░░░░░  60%                             ║
║                                                            ║
║  Estimated time: 3 minutes                                ║
║                                                            ║
║  [CANCEL]                                                 ║
╚════════════════════════════════════════════════════════════╝

⏳ This will take 5-10 minutes. Go get coffee! ☕
```

**When complete, you'll see:**

```
╔════════════════════════════════════════════════════════════╗
║              ✅ Write Complete!                             ║
║                                                            ║
║  Raspberry Pi OS has been written to SD card              ║
║                                                            ║
║  [CONTINUE]                                               ║
╚════════════════════════════════════════════════════════════╝
```

**Click [CONTINUE], then eject the SD card from your computer.**

---

# STEP 2: First Boot & Network Setup (10 minutes)

## What You Need
- Raspberry Pi 4B
- SD card (just flashed)
- Power adapter (USB-C, 3A+)
- Monitor with HDMI cable
- Keyboard and mouse
- Ethernet cable (recommended) or WiFi

## What You'll See

### 2a. Insert SD Card into Pi

```
┌─────────────────────────────────────┐
│      Raspberry Pi 4B                │
│                                     │
│  ◄─────── SD Card Slot              │
│  Insert card here (gold side down)  │
│                                     │
│  [Power USB-C port]                 │
│  [HDMI ports]                       │
│  [Network ports]                    │
└─────────────────────────────────────┘
```

**Insert the SD card into the slot until it clicks.**

### 2b. Connect Peripherals

```
Your Setup:
                    ┌─ Monitor (HDMI)
                    │
                    ↓
    ┌───────────────────────────────┐
    │   Raspberry Pi 4B             │
    │                               │
    │  ◄─ Keyboard (USB)            │
    │  ◄─ Mouse (USB)               │
    │  ◄─ Network (Ethernet)        │
    │  ◄─ Power (USB-C)             │
    └───────────────────────────────┘
```

### 2c. Power On

**Connect the USB-C power adapter.**

**Monitor will show:**

```
[Raspberry Pi logo]

Initializing...

Welcome to Raspberry Pi Desktop!

```

**After 30-60 seconds, you'll see the welcome wizard:**

```
╔════════════════════════════════════════════════════════════╗
║          Welcome to Raspberry Pi Desktop                    ║
║                                                            ║
║  ┌──────────────────────────────────────────────────────┐ ║
║  │                                                        │ ║
║  │  Welcome!                                             │ ║
║  │                                                        │ ║
║  │  This wizard will help you get started with your     │ ║
║  │  Raspberry Pi.                                        │ ║
║  │                                                        │ ║
║  │  ☑ Country (already set)                              │ ║
║  │  ☑ Timezone (already set)                             │ ║
║  │  ☑ Keyboard layout (already set)                      │ ║
║  │  ☑ WiFi (if you want)                                 │ ║
║  │                                                        │ ║
║  │  [Next] [Skip]                                        │ ║
║  │                                                        │ ║
║  └──────────────────────────────────────────────────────┘ ║
╚════════════════════════════════════════════════════════════╝
```

**Click [Next] or [Skip]** - you've already configured these in setup.

### 2d. Complete Setup

**The wizard will complete and you'll see the desktop:**

```
╔════════════════════════════════════════════════════════════╗
║  File  Edit  View  Help                            [_][□][X]
║─────────────────────────────────────────────────────────── ║
║                                                            ║
║                                                            ║
║        ┌────────────────────────────────┐                 ║
║        │  Raspberry Pi Desktop           │                 ║
║        │                                 │                 ║
║        │                                 │                 ║
║        │  [File Manager] [Terminal] etc  │                 ║
║        │                                 │                 ║
║        └────────────────────────────────┘                 ║
║                                                            ║
║  [Desktop icons/shortcuts]                                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

✅ **Raspberry Pi is now running!**

---

# STEP 3: Transfer T1000 Code (5 minutes)

## What You Need
- T1000_Phase1_Code.zip file (from me)
- USB drive OR internet connection for git clone

## Option A: USB Drive Method (Easiest)

### 3a-i. Copy ZIP to USB Drive

**On your computer:**

1. Insert USB drive
2. Copy `T1000_Phase1_Code.zip` to the USB drive root
3. Safely eject USB drive

### 3a-ii. Insert USB Drive into Pi

**On your Pi:**

```
Pi with USB drive inserted:

    ┌──────────────────────────┐
    │  Raspberry Pi 4B         │
    │                          │
    │  USB ports:              │
    │  [USB drive] ◄────────── Connected here
    │  [empty]                 │
    │                          │
    └──────────────────────────┘

Monitor will show a notification:
┌──────────────────────────────┐
│ USB Drive Detected            │
│ Location: /media/pi/USB-XXXX │
└──────────────────────────────┘
```

### 3a-iii. Open Terminal

**Click on the Terminal icon in the taskbar:**

```
Desktop taskbar:
[File Manager] [Terminal] [Web Browser] ... [System Tray]
                  ↓
                  Click here
```

**You'll see a terminal window:**

```
╔════════════════════════════════════════════════════════════╗
║ mc103.acprivilege@t1000:~ $                               ║
║                                                            ║
║ [cursor blinking]                                         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### 3a-iv. Copy Files from USB

**Type these commands in the terminal:**

```bash
# Create T1000 directory
mkdir ~/t1000

# Find your USB drive (look for /media/pi/...)
ls /media/pi/

# Copy files (replace USB-XXXX with your actual USB name)
cp /media/pi/USB-XXXX/T1000_Phase1_Code.zip ~/t1000/
cd ~/t1000
unzip T1000_Phase1_Code.zip

# Move files up one level if they're in a subfolder
ls  # Check what's here
# If you see "T100/" folder:
mv T100/* .
rm -rf T100
```

**Terminal output will look like:**

```
mc103.acprivilege@t1000:~$ mkdir ~/t1000
mc103.acprivilege@t1000:~$ ls /media/pi/
USB-DRIVE-NAME
mc103.acprivilege@t1000:~$ cp /media/pi/USB-DRIVE-NAME/T1000_Phase1_Code.zip ~/t1000/
mc103.acprivilege@t1000:~$ cd ~/t1000
mc103.acprivilege@t1000:~/t1000$ unzip T1000_Phase1_Code.zip
Archive:  T1000_Phase1_Code.zip
  inflating: config/settings.json
  inflating: main.py
  inflating: services/obd_service.py
  ...
mc103.acprivilege@t1000:~/t1000$ ls
ARCHITECTURE.md        config/
BENCH_TESTING_GUIDE.md logs/
INSTALLATION.md        main.py
README.md              requirements.txt
setup.sh*              screens/
services/              tests/

✅ Files successfully copied!
```

---

## Option B: Git Clone (If You Have Internet)

**In terminal:**

```bash
cd ~
git clone https://github.com/YOUR-USERNAME/t1000.git
cd t1000
```

---

# STEP 4: Install Dependencies (25 minutes)

## What You'll See

### 4a. Run Setup Script

**In the terminal (you should be in ~/t1000):**

```bash
bash setup.sh
```

**You'll see output like this:**

```
╔════════════════════════════════════════════════════════════╗
║  Terminal Output                                           ║
║                                                            ║
║  ==========================================                ║
║  T1000 Infotainment System - Setup Script                 ║
║  ==========================================                ║
║                                                            ║
║  📦 Updating system packages...                           ║
║  Hit:1 http://raspbian.mirror.com/raspbian bullseye...   ║
║  Get:2 http://raspbian.mirror.com/raspbian bullseye...   ║
║  ...                                                      ║
║  Processing triggers for...                               ║
║                                                            ║
║  📦 Installing system dependencies...                     ║
║  Reading package lists... Done                            ║
║  Building dependency tree... Done                         ║
║  Setting up python3-pip (20.0.2-5)...                     ║
║  Setting up python3-dev...                                ║
║  ...                                                      ║
║  [many lines of installation output]                      ║
║  ...                                                      ║
║  📦 Installing Python packages...                         ║
║  Collecting kivy==2.2.1                                   ║
║  Downloading kivy-2.2.1...                                ║
║  ...                                                      ║
║  Successfully installed kivy opencv-python python-obd     ║
║  RPi.GPIO pandas numpy matplotlib pyttsx3 pytest         ║
║                                                            ║
║  📁 Creating project directory structure...               ║
║  🔐 Setting file permissions...                          ║
║  🔌 Enabling SSH...                                      ║
║  ⚙️  Creating default settings.json...                    ║
║  📋 Setting up logging directories...                     ║
║                                                            ║
║  ==========================================                ║
║  ✅ T1000 Setup Complete!                                 ║
║  ==========================================                ║
║                                                            ║
║  Next steps:                                               ║
║  1. Edit config/settings.json with your hardware config   ║
║  2. Run: python3 main.py                                  ║
║  3. Use keyboard shortcuts (H for home, Esc to go back)   ║
║                                                            ║
║  SSH is enabled. Connect with:                            ║
║    ssh mc103.acprivilege@t1000.local                      ║
║                                                            ║
║  mc103.acprivilege@t1000:~/t1000$                        ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

⏳ Total time: 20-30 minutes
   (Kivy takes the longest to compile)
```

### 4b. Verify Installation

**After setup.sh completes, verify everything works:**

```bash
# Check all imports
python3 -c "import kivy; import cv2; import obd; print('✅ All OK')"
```

**You should see:**

```
mc103.acprivilege@t1000:~/t1000$ python3 -c "import kivy; import cv2; import obd; print('✅ All OK')"
✅ All OK
```

---

# STEP 5: Run T1000! (5 seconds)

## What You'll See

### 5a. Start Application

**In terminal:**

```bash
python3 main.py
```

### 5b. Kivy Window Opens

**Within 2-3 seconds, a window will open:**

```
╔════════════════════════════════════════════════════════════╗
║                    T1000 Application                        ║
║                                                            ║
║                                                            ║
║            T1000 Infotainment System                       ║
║                                                            ║
║                                                            ║
║         ┌──────────────────────────┐                      ║
║         │      Camera              │                      ║
║         │                          │                      ║
║         │   [BUTTON]   [BUTTON]    │                      ║
║         └──────────────────────────┘                      ║
║                                                            ║
║         ┌──────────────────────────┐                      ║
║         │      Music               │                      ║
║         │                          │                      ║
║         │   [BUTTON]   [BUTTON]    │                      ║
║         └──────────────────────────┘                      ║
║                                                            ║
║         ┌──────────────────────────┐                      ║
║         │      Diagnostics         │                      ║
║         │                          │                      ║
║         │   [BUTTON]   [BUTTON]    │                      ║
║         └──────────────────────────┘                      ║
║                                                            ║
║    Status: Ready | 14:32:15                               ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### 5c. Test Keyboard Controls

**Press keys to test:**

```
H  →  Should already be on home screen
↑↓  →  Volume would change on music screen
Space  →  Play/pause (go to music screen first)
C  →  Camera (goes to camera screen)
D  →  Diagnostics (goes to diagnostics screen)
Esc  →  Go back to home (from any screen)
```

**After pressing H and Esc a few times:**

```
Terminal shows:
mc103.acprivilege@t1000:~/t1000$ python3 main.py
[INFO] Configuration loaded successfully
[INFO] T1000 Application initializing
[INFO] T1000 Application built successfully
[INFO] Home screen displayed
[INFO] Navigating to camera screen
[INFO] Returning to home screen from camera
...
```

✅ **SUCCESS! T1000 is running!**

---

# 🎓 Troubleshooting Quick Reference

## Problem: "No module named 'kivy'"

**Solution:**
```bash
pip3 install --break-system-packages kivy
```

## Problem: "Terminal not opening"

**Alternative:** Use SSH from another computer
```bash
# From your computer:
ssh mc103.acprivilege@t1000.local
# Password: 1245
```

## Problem: "Setup.sh not found"

**Verify you're in the right directory:**
```bash
pwd  # Should show: /home/mc103.acprivilege/t1000
ls   # Should show: main.py, setup.sh, config/, services/, etc.
```

## Problem: "No network/WiFi"

**Use Ethernet cable instead** (easier and more reliable)

Or configure WiFi manually:
```bash
sudo raspi-config
# Go to: Wireless LAN → Select your SSID → Enter password
```

## Problem: "It's taking forever"

**That's normal!** Kivy compilation takes 15-20 minutes.
- Don't interrupt it
- Have patience ☕
- Monitor with: `top` in another SSH session

---

# 📊 Timeline Summary

```
Total Time: ~45-50 minutes

├─ Step 1: Flash OS           10 minutes ⏱️
├─ Step 2: First Boot         10 minutes ⏱️
├─ Step 3: Transfer Code       5 minutes ⏱️
├─ Step 4: Install Deps       25 minutes ⏱️  (longest)
└─ Step 5: Run App             5 seconds ⏱️

Expected:
  14:00  Start flashing
  14:10  Start first boot
  14:20  Start transferring code
  14:25  Start setup.sh
  14:50  ✅ T1000 Running!
```

---

# ✅ Success Checklist

When you see the home screen with all 5 buttons and can press H/Esc without crashing:

```
✅ Step 1: Flashed Raspberry Pi OS
✅ Step 2: Booted successfully
✅ Step 3: Copied T1000 code
✅ Step 4: Installed dependencies
✅ Step 5: Application launched
✅ Step 6: Keyboard controls work
✅ Step 7: No crashes for 5+ minutes

🎉 Phase 1 Bench Testing Ready!
```

---

# 🚀 Next Steps

Now that T1000 is running:

1. **Test each screen** - Navigate through all 5 screens
2. **Monitor logs** - Open another terminal:
   ```bash
   tail -f logs/t1000.log
   ```
3. **Run unit tests** - Verify all services:
   ```bash
   python3 -m pytest tests/test_services.py -v
   ```
4. **Read the docs** - Check out:
   - `BENCH_TESTING_GUIDE.md` - How to test each feature
   - `ARCHITECTURE.md` - Technical deep dive
   - `README.md` - Feature overview

5. **Plan Phase 2** - Vehicle integration:
   - Power harness design
   - GPIO wiring for buttons
   - Camera mounting
   - Audio amplifier installation

---

**Good luck! You've got this! 🚀**

If you run into issues, check the logs and the troubleshooting sections above.

---

*Generated: 2026-05-04*  
*For: Michael Carroll*  
*Vehicle: 1997 Toyota T100*
