# Realistic Activity Client Documentation

Simulated Pi client that sends realistic sensor data for validated activities to the firefighter-server for frontend testing.

## Overview

This script generates realistic accelerometer and foot pressure sensor data based on validated thresholds from the archived detection script (`/archived/accelerator/blue/analyze.py`). Unlike `test_client.py` which sends random values, this client generates physiologically accurate sensor readings for each specific activity.

**Validated Activities:**

- Standing
- Sitting
- Bent_Forward
- Lying_Down
- Jumping

**Source:** Thresholds validated with real WT901BLE67 IMU sensor data from `archived/accelerator/blue/analyze.py` (lines 46-78)

**Important:** Y-axis is VERTICAL (not Z-axis) when standing upright, based on the archived script coordinate system.

---

## Usage Examples

```bash
# Send realistic SITTING data for 30 seconds
python realistic_activity_client.py --activity Sitting --duration 30

# Send STANDING data continuously (Ctrl+C to stop)
python realistic_activity_client.py --activity Standing

# Send JUMPING data without auto session management
python realistic_activity_client.py --activity Jumping --no-auto-session

# Send BENT_FORWARD data
python realistic_activity_client.py --activity Bent_Forward --duration 60

# Send LYING_DOWN data
python realistic_activity_client.py --activity Lying_Down
```

---

## Command Line Parameters

### Required Parameters

| Parameter    | Type   | Choices                                                        | Description                                      |
| ------------ | ------ | -------------------------------------------------------------- | ------------------------------------------------ |
| `--activity` | string | `Standing`, `Sitting`, `Bent_Forward`, `Lying_Down`, `Jumping` | Activity to simulate (validated activities only) |

### Optional Parameters

| Parameter           | Type    | Default                 | Description                                          |
| ------------------- | ------- | ----------------------- | ---------------------------------------------------- |
| `--server`          | string  | `http://localhost:3000` | Server URL to connect to                             |
| `--pi-id`           | string  | `test-pi-001`           | Pi ID for this simulated device                      |
| `--duration`        | integer | None (continuous)       | Duration in seconds to send data                     |
| `--no-auto-session` | flag    | False                   | Disable automatic session start/end (send data only) |

### Parameter Details

**`--activity`** (REQUIRED)

- Choose exactly ONE activity to simulate
- Only validated activities are available
- Script will send continuous realistic data for the selected activity

**`--server`**

- URL of the firefighter-server
- Default connects to local development server
- Example: `--server http://192.168.1.100:3000`

**`--pi-id`**

- Identifier for this simulated Raspberry Pi
- Useful when testing multiple Pi connections
- Example: `--pi-id firefighter-01`

**`--duration`**

- How long to send data (in seconds)
- If omitted, runs continuously until Ctrl+C
- Example: `--duration 60` (runs for 1 minute)

**`--no-auto-session`**

- By default, script automatically starts/ends sessions
- Use this flag to only send sensor data without session management
- Useful when testing data flow without session lifecycle

---

## Key Features

### Simple Parameter Selection

Choose exactly ONE activity to simulate:

- `--activity Sitting` → sends only sitting data
- `--activity Standing` → sends only standing data
- `--activity Bent_Forward` → sends only bent forward data
- `--activity Lying_Down` → sends only lying down data
- `--activity Jumping` → sends only jumping data

### Realistic Sensor Values

Based on validated thresholds from `archived/accelerator/blue/analyze.py`:

| Activity         | acc.y                   | Pitch    | Gyro        | Foot Pressure             |
| ---------------- | ----------------------- | -------- | ----------- | ------------------------- |
| **Standing**     | 0.9-1.1g                | -10°~10° | -30~30°/s   | 100-200                   |
| **Sitting**      | 0.6-0.85g               | 20°~40°  | -15~15°/s   | 0-80                      |
| **Bent_Forward** | 0.2-0.65g               | 40°~80°  | -40~40°/s   | 120-220 (shifted to toes) |
| **Lying_Down**   | -0.25~0.25g             | ±75°~95° | -20~20°/s   | 0-50                      |
| **Jumping**      | 0.4-1.45g (oscillating) | -20°~20° | -120~120°/s | 0-800 (oscillating)       |

**Units:**

- Acceleration: g (gravity, where 1g = 9.81 m/s²)
- Gyroscope: degrees per second (°/s)
- Angle: degrees (°)
- Foot Pressure: arbitrary units (0-1000+ range)

---

## Activity Descriptions

### Standing

- **Characteristics:** Upright stable posture with gravity on Y-axis
- **Use Case:** Testing standing firefighter display
- **Sensor Behavior:**
  - Y-axis acceleration near 1.0g (gravity)
  - Minimal pitch/roll angles
  - Low gyroscope activity
  - Full weight distribution on feet

### Sitting

- **Characteristics:** Seated with moderate forward pitch
- **Use Case:** Testing resting/recovery state
- **Sensor Behavior:**
  - Lower Y-axis acceleration (0.6-0.85g) - weight on seat
  - Moderate pitch angle (20-40°)
  - Minimal foot pressure
  - Stable position

### Bent_Forward

- **Characteristics:** Forward bend with high pitch angle
- **Use Case:** Testing firefighter working posture
- **Sensor Behavior:**
  - Low Y-axis acceleration (<0.7g)
  - High pitch angle (40-80°)
  - Weight shifted to toes
  - Moderate movement

### Lying_Down

- **Characteristics:** Horizontal orientation
- **Use Case:** Testing down firefighter alert
- **Sensor Behavior:**
  - Y-axis near 0g (horizontal)
  - Gravity on X or Z axis instead
  - Extreme pitch/roll angles (±75-95°)
  - Minimal foot pressure

### Jumping

- **Characteristics:** Rapid vertical acceleration spikes
- **Use Case:** Testing dynamic movement detection
- **Sensor Behavior:**
  - Oscillating Y-axis (0.4-1.45g)
  - High gyroscope activity (>100°/s)
  - Alternating high/low foot pressure
  - ~1 jump per second cycle

---

## Example Session Output

```
======================================================================
  Realistic Activity Simulation Client
======================================================================
  Activity: Sitting
  Server: http://localhost:3000
  Pi ID: test-pi-001
======================================================================

🔌 Connecting to http://localhost:3000...
✅ Connected to server (ID: abc123xyz)

🎬 Starting session for Pi: test-pi-001

📡 Sending realistic Sitting sensor data...
   Activity: Sitting
   Duration: 30s
   Source: Validated thresholds from archived/accelerator/blue/analyze.py

📊 5s elapsed | 150 packets sent | Activity: Sitting
📊 10s elapsed | 300 packets sent | Activity: Sitting
📊 15s elapsed | 450 packets sent | Activity: Sitting
📊 20s elapsed | 600 packets sent | Activity: Sitting
📊 25s elapsed | 750 packets sent | Activity: Sitting
📊 30s elapsed | 900 packets sent | Activity: Sitting

🛑 Ending session for Pi: test-pi-001

✅ Session complete:
   Duration: 30.0s
   Packets sent: 900
   Activity simulated: Sitting
```

---

## Technical Details

### Data Generation Rate

- **Frequency:** 10Hz (100ms intervals)
- **Packets per cycle:** 3 (left foot + right foot + accelerometer)
- **Total rate:** ~30 packets/second

### Socket.IO Events

- **Emitted:** `sensor_data` (foot and accelerometer readings)
- **Emitted:** `start_session` (if auto-session enabled)
- **Emitted:** `end_session` (if auto-session enabled)
- **Received:** `command` (from server)

### Data Format

**Foot Pressure Data:**

```json
{
  "timestamp": 1734567890.123,
  "device": "LEFT",
  "data": [120, 115, 125, ..., 130]  // 18 sensor values
}
```

**Accelerometer Data:**

```json
{
  "timestamp": 1734567890.123,
  "device": "ACCELEROMETER",
  "acc": { "x": -0.2, "y": 1.05, "z": 0.1 },
  "gyro": { "x": 15.3, "y": -8.2, "z": 22.1 },
  "angle": { "pitch": 5.2, "roll": -3.1, "yaw": 180.5 }
}
```

---

## Coordinate System

**IMPORTANT:** Based on archived script validation:

- **Y-axis:** VERTICAL (down -/ up +) when standing upright

  - Standing: acc.y ≈ 1.0g
  - Lying down: acc.y ≈ 0g

- **X-axis:** LEFT (-) / RIGHT (+)

- **Z-axis:** BACKWARD (-) / FORWARD (+)

**Angles:**

- **Roll:** Rotation around X-axis (sideways tilt)
- **Pitch:** Rotation around Y-axis (forward/backward tilt)
- **Yaw:** Rotation around Z-axis (compass heading)

This differs from some documentation that assumes Z-axis is vertical.

---

## Testing Workflow

### 1. Test Individual Activities

```bash
# Test each activity individually to verify frontend display
python realistic_activity_client.py --activity Standing --duration 20
python realistic_activity_client.py --activity Sitting --duration 20
python realistic_activity_client.py --activity Bent_Forward --duration 20
python realistic_activity_client.py --activity Lying_Down --duration 20
python realistic_activity_client.py --activity Jumping --duration 20
```

### 2. Test Continuous Monitoring

```bash
# Run continuous data stream to test long-term stability
python realistic_activity_client.py --activity Standing
# Press Ctrl+C when done
```

### 3. Test Multiple Pi Connections

```bash
# Terminal 1
python realistic_activity_client.py --activity Standing --pi-id firefighter-01

# Terminal 2
python realistic_activity_client.py --activity Sitting --pi-id firefighter-02
```

### 4. Test Without Session Management

```bash
# Send data only, no session start/end
python realistic_activity_client.py --activity Jumping --no-auto-session
```

---

## Differences from test_client.py

| Feature                | `test_client.py`           | `realistic_activity_client.py`               |
| ---------------------- | -------------------------- | -------------------------------------------- |
| **Data source**        | Random values              | Validated thresholds from archived script    |
| **Activity selection** | Random walking pattern     | Specific activity via `--activity` parameter |
| **Realism**            | Simulated random motion    | Physiologically accurate sensor readings     |
| **Use case**           | Basic connectivity testing | Frontend display validation                  |
| **Thresholds**         | Generic ranges             | Activity-specific validated ranges           |

---

## Troubleshooting

### Connection Issues

```bash
# Check if server is running
curl http://localhost:3000

# Try different server URL
python realistic_activity_client.py --activity Standing --server http://192.168.1.100:3000
```

### Script Hangs

- Press `Ctrl+C` to stop gracefully
- Script will display summary statistics before exiting

### No Data Appearing in Frontend

1. Check server logs for incoming `sensor_data` events
2. Verify Pi ID matches expected value in frontend
3. Try with `--no-auto-session` flag to isolate session management issues

---

## Related Documentation

- **Threshold Sources:** `/sensor-hub/docs/THRESHOLD_SOURCES.md`
- **Accelerometer Thresholds:** `/sensor-hub/docs/accelerometer_thresholds.json`
- **Activity Detection Guide:** `/sensor-hub/docs/ACTIVITY_DETECTION_GUIDE.md`
- **Archived Script:** `/archived/accelerator/blue/analyze.py` (lines 46-78)

---

## Validation Status

All 5 activities in this script have been **validated** with real sensor data:

| Activity        | IMU Validated | Source           |
| --------------- | ------------- | ---------------- |
| Standing ✅     | Yes           | analyze.py:50-53 |
| Sitting ✅      | Yes           | analyze.py:60-64 |
| Bent_Forward ✅ | Yes           | analyze.py:56-57 |
| Lying_Down ✅   | Yes           | analyze.py:67-68 |
| Jumping ✅      | Yes           | analyze.py:71-74 |

**Note:** Foot pressure patterns are estimated based on biomechanical expectations, as the archived script only validated IMU sensor thresholds.

---

## Future Enhancements

Potential additions (not currently implemented):

- Activity transitions (smooth change from one activity to another)
- Multi-firefighter simulation mode
- Data recording/playback functionality
- Custom threshold override options
- Additional unvalidated activities (Walking, Running, etc.) marked as experimental

---

**Last Updated:** 2025-12-19
**Script Version:** 1.0
**Author:** Auto-generated documentation for realistic_activity_client.py
