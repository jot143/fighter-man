# Central BLE Sensor Monitor

Unified monitoring system for multiple BLE sensors: foot pressure sensors and accelerometer IMU.

## Features

- **Concurrent monitoring** of multiple BLE devices using async/await
- **Clean architecture** with separate sensor classes and parsers
- **JSON output** for structured, parseable data streams
- **Graceful shutdown** with proper BLE cleanup
- **Cross-platform** support (Windows, macOS, Linux)
- **No sudo required** (with proper setup)

## Architecture

```
central/
├── main.py                 # Entry point - monitors all sensors
├── .env                    # Device MAC addresses (configure this)
├── requirements.txt        # Python dependencies
├── sensors/
│   ├── __init__.py
│   ├── foot_sensor.py      # FootSensor class for pressure sensors
│   ├── accel_sensor.py     # AccelSensor class for IMU
│   └── parsers.py          # Data parsing functions
└── README.md               # This file
```

## Setup

### 1. Install System Dependencies

**Raspberry Pi:**
```bash
sudo apt-get update
sudo apt-get install libopenblas-dev
sudo usermod -a -G bluetooth $USER
sudo reboot
```

**macOS:**
```bash
# No additional setup needed
```

**Linux (non-Raspberry Pi):**
```bash
sudo usermod -a -G bluetooth $USER
# Log out and back in
```

### 2. Create Virtual Environment

```bash
cd central
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Device MAC Addresses

Edit `.env` file and add your device MAC addresses:

```bash
# Find device MAC addresses using:
# - bluetoothctl (Linux)
# - System Settings > Bluetooth (macOS)
# - Device Manager (Windows)

LEFT_FOOT_MAC=ed:63:5b:c4:2d:92
RIGHT_FOOT_MAC=XX:XX:XX:XX:XX:XX
ACCELEROMETER_MAC=XX:XX:XX:XX:XX:XX
```

**Note**: You can leave RIGHT_FOOT_MAC or ACCELEROMETER_MAC with XX:XX:XX:XX:XX:XX if you don't have those devices - the system will skip them.

## Usage

### Run the Monitor

```bash
source venv/bin/activate
python3 main.py
```

### Stop Monitoring

Press `Ctrl+C` to gracefully shutdown. The system will:
1. Send stop commands to all sensors
2. Disable notifications
3. Disconnect from all devices

## Output Format

All sensor data is output as JSON to console (stdout).

### Foot Pressure Sensor Output

```json
{
  "timestamp": "2025-11-24T10:30:45.123456",
  "device": "LEFT_FOOT",
  "data": {
    "foot": "LEFT",
    "max": 45.2,
    "avg": 23.1,
    "active_count": 12,
    "values": [23.5, 45.2, 12.8, 34.1, ...]
  }
}
```

**Fields**:
- `max`: Maximum pressure value across all 18 sensors
- `avg`: Average pressure value
- `active_count`: Number of sensors with non-zero values (0-18)
- `values`: Array of 18 pressure values from active sensors

### Accelerometer IMU Output

```json
{
  "timestamp": "2025-11-24T10:30:45.234567",
  "device": "ACCELEROMETER",
  "data": {
    "acc": {"x": 0.98, "y": 0.15, "z": 0.02},
    "gyro": {"x": 2.5, "y": -1.3, "z": 0.8},
    "angle": {"roll": 5.2, "pitch": 12.3, "yaw": 180.0}
  }
}
```

**Units**:
- `acc`: Acceleration in g (gravity units)
- `gyro`: Angular velocity in degrees/second
- `angle`: Orientation in degrees (roll/pitch/yaw)

## Troubleshooting

### "Connection failed" Errors

1. Verify device is powered on and in range (<5 meters)
2. Check Bluetooth is enabled on your system
3. Verify MAC address in `.env` is correct
4. Ensure device is not connected to another system
5. Try power-cycling the sensor device

### "Notify UUID not found"

This is normal for the accelerometer - the system will use fallback UUIDs. If data still doesn't appear, the device may use different UUIDs.

### No Data Appearing

**Foot sensors**: Apply pressure to the insole - sensors only transmit when pressure is detected.

**Accelerometer**: The device should transmit continuously. If not:
- Check that notifications are enabled (logged on startup)
- Verify the device is the WT901BLE67 model
- Try moving the device to trigger transmission

### Permission Denied (Linux)

```bash
# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Log out and back in, then verify:
groups | grep bluetooth
```

## BLE Protocol Details

### Foot Pressure Sensors

- **Protocol**: Text-based with newline delimiters
- **Service UUID**: `0000FFF0-0000-1000-8000-00805F9B34FB`
- **Notify UUID**: `0000FFF1-0000-1000-8000-00805F9B34FB`
- **Write UUID**: `0000FFF2-0000-1000-8000-00805F9B34FB`
- **Data format**: `L_[[v1,v2,...],[v5,v6,...],...]\\n`
- **Sensors**: 6×4 matrix (24 positions, 18 active)
- **Commands**: `begin` (start), `end` (stop)

### Accelerometer (WT901BLE67)

- **Protocol**: Binary 20-byte packets
- **Notify UUIDs**: `0000ffe4-...` or `0000fff1-...`
- **Write UUIDs**: `0000ffe9-...` or `0000fff2-...`
- **Packet format**:
  - Header: `0x55 0x61`
  - Accelerometer: 6 bytes (3×2 signed shorts)
  - Gyroscope: 6 bytes (3×2 signed shorts)
  - Angles: 6 bytes (3×2 signed shorts)
- **Ranges**: ±16g (acc), ±2000°/s (gyro), ±180° (angle)

## Extending the System

### Add Custom Data Processing

Create a callback function:

```python
async def my_callback(sensor_data):
    # Process data here
    print(f"Received from {sensor_data['device']}")

# Pass to sensor
foot = FootSensor(mac, "LEFT_FOOT", data_callback=my_callback)
```

### Log Data to File

Redirect stdout to a file:

```bash
python3 main.py > sensor_data.jsonl
```

Each line will be a complete JSON object (JSONL format).

### Filter Specific Sensor

Modify `main.py` to only instantiate the sensors you want:

```python
# Only monitor left foot
sensors = []
left_foot = FootSensor(left_mac, "LEFT_FOOT")
sensors.append(left_foot.monitor_loop())

await asyncio.gather(*sensors)
```

## Technical Notes

- **Async architecture**: Uses `asyncio.gather()` for true concurrent monitoring
- **Buffering**: FootSensor buffers fragmented BLE packets until newline delimiter
- **Keep-alive**: AccelSensor sends periodic commands to maintain connection
- **MTU size**: BLE packets limited to ~20 bytes - larger data arrives fragmented
- **Connection timeout**: 15 seconds for initial connection
- **Platform compatibility**: bleak abstracts platform-specific BLE APIs

## Dependencies

- `bleak>=0.21.0` - Modern async BLE library
- `numpy>=1.24.0` - Array processing for sensor data
- `python-dotenv>=1.0.0` - Environment variable management

## License

Part of the neuronso-connection project.
