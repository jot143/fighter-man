# BLE Insole Sensor Monitor - Quick Start Guide

Simple guide to run the insole pressure monitoring app.

---

## System Requirements (Raspberry Pi)

Before setting up Python environment, install required system libraries:

```bash
sudo apt-get update
sudo apt-get install libopenblas-dev
```

This installs OpenBLAS, which is required for NumPy to work properly.

### Bluetooth Permissions

Add your user to the bluetooth group (so you don't need sudo):

```bash
sudo usermod -a -G bluetooth $USER
```

Then logout and login again, or reboot:

```bash
sudo reboot
```

---

## Setup (First Time Only)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal prompt.

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

---

## Running the App

### 1. Make Sure Virtual Environment is Active

```bash
source venv/bin/activate
```

### 2. Run the App

```bash
python3 app.py
```

### 3. Stop the App

Press `Ctrl + C` to stop monitoring.

---

## Testing the Sensor

### What You'll See

When you run `python3 app.py`, you'll see:

```
============================================================
BLE INSOLE SENSOR MONITOR
============================================================
Device: ed:63:5b:c4:2d:92
Press Ctrl+C to stop

Connecting to device...
Connected: True
Notifications enabled
Data collection started

Receiving data...
```

**This is normal!** The app is connected and waiting for data.

### Getting Data to Appear

The insole sensor only sends data when **pressure is applied**. To see data:

1. Place the insole in a shoe
2. Step on it or apply pressure with your hand
3. You'll immediately see packets appear:

```
============================================================
Packet #1 - LEFT FOOT
============================================================
[[23.5 45.2 12.8 34.1]
 [56.7 78.9 23.4 45.6]
 [34.2 67.8 89.1  0.0]
 [12.3 45.6 78.9  0.0]
 [23.4  0.0 56.7  0.0]
 [45.6 67.8  0.0  0.0]]

Max: 89.1 | Avg: 38.5 | Active: 14/18
```

**No data appearing?** The sensor is working fine - it's just not detecting pressure. Try stepping on it!

---

## Exit Virtual Environment

When you're done, deactivate the virtual environment:

```bash
deactivate
```

---

## Complete Workflow

```bash
# System requirements (Raspberry Pi)
sudo apt-get update
sudo apt-get install libopenblas-dev
sudo usermod -a -G bluetooth $USER
sudo reboot  # Logout and login after this

# First time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the app
python3 app.py

# Stop with Ctrl+C

# Exit environment
deactivate
```

---

## Troubleshooting

**If device not found:**

- Make sure the insole sensor is powered on
- Check that it's within range (< 5 meters)
- Verify Bluetooth is enabled on your system

**If connection fails:**

- Restart Bluetooth: `sudo systemctl restart bluetooth`
- Try moving closer to the device
- Make sure device isn't connected to another device

**If "command not found" error:**

- Make sure you activated the virtual environment
- Check Python is installed: `python3 --version`

**If NumPy import error (libopenblas.so.0 not found):**

- Install system library: `sudo apt-get install libopenblas-dev`
- Deactivate and reactivate virtual environment
- If still failing, reinstall requirements: `pip install --force-reinstall -r requirements.txt`

**If you need sudo to run the app:**

- Add user to bluetooth group: `sudo usermod -a -G bluetooth $USER`
- Logout and login again, or reboot: `sudo reboot`
- After reboot, you can run without sudo: `python3 app.py`

**If no data appears (stuck at "Receiving data..."):**

- This is normal! The sensor only sends data when pressure is applied
- Step on the insole or press it with your hand
- Data will immediately appear when pressure is detected
- If still no data after applying pressure, check device battery

---

## Device Information

- **Left Foot MAC:** `ed:63:5b:c4:2d:92`
- **Device Name:** `Left01_foot`
- **Connection:** Bluetooth Low Energy (BLE)

---

## Quick Reference

| Command                           | Description                |
| --------------------------------- | -------------------------- |
| `python3 -m venv venv`            | Create virtual environment |
| `source venv/bin/activate`        | Enter virtual environment  |
| `pip install -r requirements.txt` | Install dependencies       |
| `python3 app.py`                  | Run the monitor            |
| `Ctrl + C`                        | Stop the monitor           |
| `deactivate`                      | Exit virtual environment   |
