# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a BLE-based insole sensor monitoring system for firefighter safety applications. The system connects to Bluetooth Low Energy (BLE) insole pressure sensors to collect real-time pressure data from 18 sensors arranged in a 6x4 matrix pattern on each foot.

## Quick Commands

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the main monitor
python3 app.py

# Stop monitoring
# Press Ctrl+C

# Deactivate virtual environment
deactivate
```

### First Time Setup

```bash
# System dependencies (Raspberry Pi only)
sudo apt-get install libopenblas-dev
sudo usermod -a -G bluetooth $USER
sudo reboot

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Architecture

### BLE Communication Protocol

**Device Configuration:**
- Left foot MAC: `ed:63:5b:c4:2d:92`
- Right foot MAC: To be discovered via scanning
- Service UUID: `0000FFF0-0000-1000-8000-00805F9B34FB`
- Read/Notify UUID: `0000FFF1-0000-1000-8000-00805F9B34FB`
- Write UUID: `0000FFF2-0000-1000-8000-00805F9B34FB`

**Commands:**
- Start collection: `b'begin'`
- Stop collection: `b'end'`
- Switch to left foot: `b'left\n'`
- Switch to right foot: `b'right\n'`

**Data Format:**
- Prefix: `L_` (left foot) or `R_` (right foot)
- Format: 6x4 nested array (24 total values)
- Example: `L_[[0.0,0.0,0.0,0.0],[0.0,0.0,0.0,0.0],...[0.0,0.0,0.0,0.0]]`
- Terminator: `\n` (newline)
- Values: Float numbers representing pressure readings

### Sensor Layout

The insole contains 24 matrix positions (6 rows × 4 columns) but only 18 have physical sensors.

**Excluded indices:** 8, 12, 16, 19, 20, 23 (no physical sensors at these positions)

**Active sensor positions:**
```
[0] [1] [2] [3]     <- Toes (4 sensors)
[4] [5] [6] [7]     <- Front foot (4 sensors)
    [9] [10] [11]   <- Mid foot (3 sensors, index 8 excluded)
    [13] [14] [15]  <- Mid foot (3 sensors, index 12 excluded)
    [17] [18]       <- Heel (2 sensors, indices 16,19,20 excluded)
    [21] [22]       <- Heel (2 sensors, index 23 excluded)
```

### Data Processing Pipeline

1. **Connection**: BleakClient establishes BLE connection to device
2. **Notification Handler**: Receives raw byte data from NOTIFY_UUID
3. **Buffering**: Incomplete packets are buffered until newline delimiter
4. **Parsing**: Extract foot identifier (L_/R_) and parse 24 float values
5. **Filtering**: Extract 18 active sensors by excluding hardcoded indices
6. **Reshaping**: Convert flat list to 6x4 NumPy array for visualization
7. **Display**: Show matrix, statistics (max, avg, active sensor count)

### Key Implementation Details

**Async Architecture:**
- Uses Python's `asyncio` for non-blocking BLE operations
- BleakClient provides async context manager for connection lifecycle
- Notification handler runs in callback context (synchronous function called by async loop)

**Buffer Management:**
- Global `data_buffer` accumulates chunks until complete line detected
- Critical for handling fragmented BLE packets (MTU size ~20 bytes)
- Lines split on `\n`, processed immediately, remainder stays in buffer

**Signal Handling:**
- SIGINT handler sets `running = False` for graceful shutdown
- Ensures proper BLE cleanup (send 'end' command, stop notifications, disconnect)
- Prevents device from staying in active collection mode after exit

## Development Notes

### Working with BLE on Raspberry Pi

- User must be in `bluetooth` group to avoid requiring sudo
- BlueZ stack must be running: `sudo systemctl status bluetooth`
- Connection timeout set to 15 seconds (devices can be slow to respond)
- Device must be unpaired from other systems before connecting

### Testing Without Hardware

The sensor only transmits data when pressure is applied. If testing with actual hardware:
1. "Receiving data..." message is normal when no pressure detected
2. Step on insole or apply hand pressure to trigger data transmission
3. Packets should appear immediately when pressure exceeds threshold

### Extending Functionality

To add dual-foot monitoring (see task.md for complete implementation):
1. Scan for right foot device and update MAC address
2. Create separate `FootMonitor` class instances for each device
3. Use `asyncio.gather()` to monitor both feet concurrently
4. Implement separate data buffers to avoid cross-contamination

To add real-time analysis (see task.md for alert system):
1. Calculate statistics on `active_18` array (max, mean, min)
2. Set thresholds for high pressure alerts (e.g., > 80.0)
3. Detect weight distribution bias (compare front vs rear sensor means)
4. Check for low contact warnings (< 5 active sensors)

## File Structure

```
foot/
├── app.py              # Main application - simple real-time monitor
├── requirements.txt    # Python dependencies (bleak, numpy)
├── doc.md             # Quick start guide for end users
├── task.md            # Comprehensive developer guide with all tasks
├── html/              # SVG graphics for foot visualization
│   ├── L foot.svg
│   └── R foot.svg
└── CLAUDE.md          # This file
```

## Important Constraints

- Only works with Nordic-based BLE devices using provided UUIDs
- Requires Python 3.8+ for asyncio features
- NumPy dependency requires system BLAS library (libopenblas on Raspberry Pi)
- Maximum connection distance ~5 meters (standard BLE range)
- Data rate varies by device (typically 10-50 packets/second)

## Development Workflow

When modifying the code:

1. Always test connection stability over extended periods (60+ seconds)
2. Verify data parsing with all 24 values before filtering to 18
3. Ensure buffer handling works with partial packets
4. Test graceful shutdown (Ctrl+C) to prevent device staying in active mode
5. Monitor packet loss rate (should be < 1%)

When adding features, refer to `task.md` which contains complete implementations for:
- Device scanning
- Command testing
- Data logging with JSON storage
- Real-time pressure analysis with alerts
- Dual-foot simultaneous monitoring
