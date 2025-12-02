# Testing Guide

## Overview

This guide explains how to test the firefighter-server with simulated sensor data.

---

## Prerequisites

1. **Server running:**

   ```bash
   cd /Users/gorki/Herd/neuronso-connection/firefighter-server
   ./start.sh
   ```

2. **Qdrant running:** (start.sh handles this automatically)
   ```bash
   # Verify Qdrant is up
   curl http://localhost:6333/health
   ```

---

## Quick Test (5 Steps)

### Step 1: Check Server Health

```bash
curl http://localhost:4100/health
```

**Expected:**

```json
{
  "status": "healthy",
  "server": "running",
  "qdrant": { "status": "healthy", "points_count": 0 },
  "active_session": null
}
```

### Step 2: Create a Session

```bash
curl -X POST http://localhost:4100/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "test_session_001"}'
```

**Expected:**

```json
{
  "id": "uuid-here",
  "name": "test_session_001",
  "status": "recording"
}
```

**Save the session ID for later!**

### Step 3: Run Test Client (Send Random Data)

```bash
cd /Users/gorki/Herd/neuronso-connection/firefighter-server
source venv/bin/activate
python tests/test_client.py --duration 10
```

**Expected output:**

```
==================================================
Simulated Pi Test Client
==================================================
Server: http://localhost:4100
Device Key: firefighter_pi_001
Duration: 10.0s
==================================================
[Client] Connected to http://localhost:4100
[Client] Authenticated: {'device_key': 'firefighter_pi_001', 'session_id': 'uuid'}

[Simulation] Starting 10.0s simulation
[Simulation] Foot: 10Hz, Accel: 20Hz

[Simulation] Complete!
[Simulation] Duration: 10.0s
[Simulation] Foot readings sent: 100
[Simulation] Accel readings sent: 200

[Done] Test client finished
```

### Step 4: Verify Data Stored

```bash
curl http://localhost:4100/health
```

**Expected:** `points_count` should be > 0 now:

```json
{
  "qdrant": { "points_count": 20, "status": "healthy" }
}
```

### Step 5: Stop Session

```bash
curl -X POST http://localhost:4100/api/sessions/{SESSION_ID}/stop
```

---

## Test Client Options

```bash
python tests/test_client.py [OPTIONS]

Options:
  --server URL       Server URL (default: http://localhost:4100)
  --duration SECS    Duration in seconds (default: 10)
  --device-key KEY   Device key for auth (default: firefighter_pi_001)
```

### Examples

```bash
# Short 5-second test
python tests/test_client.py --duration 5

# Longer 60-second test
python tests/test_client.py --duration 60

# Custom server
python tests/test_client.py --server http://192.168.1.100:4100
```

---

## What the Test Client Generates

### Foot Pressure Data

Simulates walking with oscillating pressure:

```python
{
  "timestamp": "2025-12-02T10:30:00.000Z",
  "device": "LEFT_FOOT",
  "data": {
    "foot": "LEFT",
    "max": 85.3,
    "avg": 52.1,
    "active_count": 15,
    "values": [50.3, 62.1, 45.8, ...]  # 18 pressure values
  }
}
```

### Accelerometer Data

Simulates walking motion:

```python
{
  "timestamp": "2025-12-02T10:30:00.050Z",
  "device": "ACCELEROMETER",
  "data": {
    "acc": {"x": 0.1, "y": -0.2, "z": 9.8},
    "gyro": {"x": 5.2, "y": 3.1, "z": -1.0},
    "angle": {"roll": 5.0, "pitch": 3.0, "yaw": 180.0}
  }
}
```

---

## Other Test Files

| File                        | Purpose                          |
| --------------------------- | -------------------------------- |
| `tests/test_api.py`         | Tests REST API endpoints         |
| `tests/test_client.py`      | Simulates Pi sending sensor data |
| `tests/test_integration.py` | Full end-to-end integration test |

### Run All Tests

```bash
./run_tests.sh
```

### Run Individual Tests

```bash
# API tests only
python tests/test_api.py

# Integration test
python tests/test_integration.py
```

---

## Viewing Data in Qdrant

### Check Collection Info

```bash
curl http://localhost:6333/collections/sensor_windows
```

### View Points Count

```bash
curl http://localhost:6333/collections/sensor_windows | python3 -m json.tool
```

### Export Session Data

```bash
curl "http://localhost:4100/api/sessions/{SESSION_ID}/export?format=json" | python3 -m json.tool
```

---

## Troubleshooting

### "Connection refused"

```bash
# Check server is running
lsof -i :4100

# Restart server
./stop.sh
./start.sh
```

### "Auth failed"

The test client uses `firefighter_pi_001` as device key. Make sure it's in your `.env`:

```bash
# .env
ALLOWED_DEVICE_KEYS=firefighter_pi_001,test_pi_001
```

Or leave empty to accept all:

```bash
ALLOWED_DEVICE_KEYS=
```

### "No windows created"

- Data is accumulated into 500ms windows
- Need at least 1 second of data
- Check server logs for "Stored window" messages

### Check Server Logs

```bash
# If running in background, check output
# Or run server in foreground to see logs:
python server.py
```

---

## Complete Test Workflow

```bash
# Terminal 1: Start server
cd /Users/gorki/Herd/neuronso-connection/firefighter-server
./start.sh

# Terminal 2: Run test
cd /Users/gorki/Herd/neuronso-connection/firefighter-server
source venv/bin/activate

# Create session
curl -X POST http://localhost:4100/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "full_test"}'

# Send data for 30 seconds
python tests/test_client.py --duration 30

# Check results
curl http://localhost:4100/health
curl http://localhost:4100/api/sessions

# Stop session (replace with your session ID)
curl -X POST http://localhost:4100/api/sessions/{SESSION_ID}/stop

# Export data
curl "http://localhost:4100/api/sessions/{SESSION_ID}/export?format=json"
```

---

**Document Version:** 1.0
**Last Updated:** December 2, 2025
