# Testing Guide

## Test Files Overview

| File                  | Purpose                                                              |
| --------------------- | -------------------------------------------------------------------- |
| `test_api.py`         | Tests REST API endpoints only (no data)                              |
| `test_client.py`      | Simulates Pi sending sensor data via Socket.IO                       |
| `test_integration.py` | Full end-to-end test (create session → send data → verify → cleanup) |

---

## Prerequisites

Before running tests, ensure both services are running:

```bash
# Check Qdrant
curl http://localhost:6333/health

# Check Server
curl http://localhost:4100/health
```

If not running:

```bash
# Start Qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Start Server
./start.sh
```

---

## Quick Start

```bash
cd /Users/gorki/Herd/neuronso-connection/firefighter-server
source venv/bin/activate
```

---

## Run All Tests

```bash
./run_tests.sh
```

This runs API tests + integration tests automatically.

---

## Individual Tests

### 1. API Tests (REST endpoints)

Tests all API endpoints without sending sensor data.

```bash
python tests/test_api.py
```

### 2. Test Client (Simulate Pi sending data)

Simulates a Raspberry Pi sending sensor data via Socket.IO.

```bash
# Send data for 10 seconds
python tests/test_client.py --duration 10

# Send data for 30 seconds
python tests/test_client.py --duration 30

# Custom server
python tests/test_client.py --server http://192.168.1.100:4100 --duration 10
```

### 3. Integration Test (Full flow)

Creates session, sends data, verifies storage, exports, and cleans up.

```bash
python tests/test_integration.py --duration 5
```

---

## Manual Testing with curl

### Health Check

```bash
curl http://localhost:4100/health
```

### Create Session

```bash
curl -X POST http://localhost:4100/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "my_test_session"}'
```

### List Sessions

```bash
curl http://localhost:4100/api/sessions
```

### Get Session Details

```bash
curl http://localhost:4100/api/sessions/{SESSION_ID}
```

### Stop Session

```bash
curl -X POST http://localhost:4100/api/sessions/{SESSION_ID}/stop
```

### Export Session

```bash
curl "http://localhost:4100/api/sessions/{SESSION_ID}/export?format=json"
```

### Delete Session

```bash
curl -X DELETE http://localhost:4100/api/sessions/{SESSION_ID}
```

---

## Complete Test Workflow

```bash
# 1. Start server (Terminal 1)
./start.sh

# 2. Run test client (Terminal 2)
source venv/bin/activate
python tests/test_client.py --duration 10

# 3. Verify data
curl http://localhost:4100/health
# Check points_count > 0

curl http://localhost:4100/api/sessions
# See your session listed
```

---

## Troubleshooting

| Issue              | Solution                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| Connection refused | Check server is running: `./start.sh`                                    |
| Auth failed        | Check `.env` has `ALLOWED_DEVICE_KEYS=firefighter_pi_001` or leave empty |
| No windows created | Send data for at least 1 second (500ms window size)                      |
| Qdrant not running | `docker start qdrant`                                                    |
