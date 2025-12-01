# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BLE sensor monitoring system for foot pressure sensors and accelerometer IMU (WT901BLE67). Uses async Python with the `bleak` library for cross-platform Bluetooth Low Energy communication.

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the main sensor monitor
python3 main.py

# Scan for nearby BLE devices (to find MAC addresses)
python3 scanner.py
```

## Configuration

Device MAC addresses and performance tuning are configured in `.env`:
- `LEFT_FOOT_MAC`, `RIGHT_FOOT_MAC`, `ACCELEROMETER_MAC` - Device addresses
- `FOOT_THROTTLE`, `ACCEL_THROTTLE` - Packet processing rate (1=every packet, 5=every 5th)
- `CONNECTION_RETRIES` - Max connection attempts per device

## Architecture

```
main.py           → Entry point, concurrent sensor monitoring via asyncio.gather()
scanner.py        → BLE device discovery utility
sensors/
  foot_sensor.py  → FootSensor class (text protocol, newline-delimited)
  accel_sensor.py → AccelSensor class (binary 20-byte packets)
  parsers.py      → Data parsing: parse_foot_data(), parse_accel_data()
```

**Key patterns:**
- Both sensor classes follow the same interface: `connect()` → `start_monitoring()` → `monitor_loop()` → `stop_monitoring()`
- Notification handlers accumulate fragmented BLE packets in buffers before parsing
- Throttling reduces data rate at packet level (e.g., throttle=5 processes every 5th packet)
- Output is JSON to stdout (JSONL format when redirected to file)

## BLE Protocol Details

**Foot sensors:** Text protocol with `L_[[values...]]\n` or `R_[[values...]]\n` format. Commands: `begin`/`end`. Service UUIDs: `FFF0`/`FFF1`/`FFF2`.

**Accelerometer (WT901BLE67):** Binary 20-byte packets with header `0x55 0x61`. Contains acc/gyro/angle as signed shorts. Requires periodic keep-alive commands. UUIDs: `ffe4`/`ffe9` or `fff1`/`fff2` depending on device variant.
