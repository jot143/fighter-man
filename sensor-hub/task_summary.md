# Firefighter Data Pipeline - Implementation Summary

**Date:** December 1, 2025
**Status:** All development phases complete, ready for testing

---

## Project Overview

A data collection and storage system for training an AI model that recognizes firefighter activities (Walking, Running, Crawling, Sitting, Turn Left, Turn Right) using wearable sensor data.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RASPBERRY PI (sensor-hub)              SERVER (firefighter-server)         │
│  ┌─────────────────────────┐           ┌─────────────────────────────────┐  │
│  │ FootSensor + AccelSensor│           │ Socket.IO Receiver              │  │
│  │         ↓               │           │         ↓                       │  │
│  │ SQLite Buffer           │──────────▶│ Qdrant (Vector Database)        │  │
│  │ (backup on failure)     │ Socket.IO │         ↓                       │  │
│  │         ↓               │           │ REST API (for annotation tool)  │  │
│  │ Socket.IO Sender        │           └─────────────────────────────────┘  │
│  └─────────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Completed Components

### Phase 1: sensor-hub (Raspberry Pi)

| Component | Files | Status |
|-----------|-------|--------|
| Configuration | `lib/config.py` | ✅ Complete |
| Socket.IO Client | `lib/socket_client.py` | ✅ Complete |
| SQLite Database | `lib/database/base.py`, `foot_db.py`, `accel_db.py` | ✅ Complete |
| Data Senders | `senders/base.py`, `foot_sender.py`, `accel_sender.py` | ✅ Complete |
| Entry Points | `send_foot_data.py`, `send_accel_data.py` | ✅ Complete |
| Main Integration | `main.py` (modified) | ✅ Complete |
| Tests | `tests/test_database.py`, `run_tests.sh` | ✅ Complete |

**Data Flow:**
1. BLE sensors emit data
2. Data stored in SQLite (backup buffer)
3. Data broadcast via Socket.IO
4. Background senders retry failed transmissions

### Phase 2: firefighter-server

| Component | Files | Status |
|-----------|-------|--------|
| Flask + Socket.IO Server | `server.py` | ✅ Complete |
| Configuration | `lib/config.py` | ✅ Complete |
| Qdrant Vector Store | `lib/vector_store.py` | ✅ Complete |
| Docker Setup | `docker-compose.yml`, `Dockerfile` | ✅ Complete |
| Tests | `tests/test_api.py`, `test_client.py`, `test_integration.py` | ✅ Complete |

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| POST | `/api/sessions` | Create new recording session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/:id` | Get session details |
| PUT | `/api/sessions/:id` | Update session/labels |
| DELETE | `/api/sessions/:id` | Delete session |
| POST | `/api/sessions/:id/stop` | Stop recording session |
| GET | `/api/sessions/:id/export` | Export session data (JSON/CSV) |
| POST | `/api/query/similar` | Find similar movement patterns |

### Phase 3: Integration & Testing

| Component | Status |
|-----------|--------|
| Integration test script | ✅ Complete |
| Simulated Pi client | ✅ Complete |
| API test suite | ✅ Complete |
| Manual testing | ⏳ Pending |

---

## Files Created

### sensor-hub/ (15 new files)

```
sensor-hub/
├── lib/
│   ├── __init__.py
│   ├── config.py                 # Type-safe configuration
│   ├── socket_client.py          # Socket.IO client with auto-reconnect
│   └── database/
│       ├── __init__.py
│       ├── base.py               # Abstract SQLite base class
│       ├── foot_db.py            # Foot sensor database
│       └── accel_db.py           # Accelerometer database
├── senders/
│   ├── __init__.py
│   ├── base.py                   # Base sender with retry logic
│   ├── foot_sender.py            # Foot data sender
│   └── accel_sender.py           # Accelerometer sender
├── send_foot_data.py             # Background sender entry point
├── send_accel_data.py            # Background sender entry point
├── tests/
│   ├── __init__.py
│   └── test_database.py          # Database unit tests
├── run_tests.sh                  # Test runner
├── main.py                       # MODIFIED (added SQLite + Socket.IO)
├── requirements.txt              # MODIFIED (added dependencies)
└── .env                          # MODIFIED (added server config)
```

### firefighter-server/ (16 new files)

```
firefighter-server/
├── server.py                     # Flask + Socket.IO main server
├── lib/
│   ├── __init__.py
│   ├── config.py                 # Server configuration
│   └── vector_store.py           # Qdrant wrapper with windowing
├── api/
│   └── __init__.py
├── data/                         # Runtime data directory
├── tests/
│   ├── __init__.py
│   ├── test_api.py               # REST API tests
│   ├── test_client.py            # Simulated Pi client
│   └── test_integration.py       # Full integration test
├── requirements.txt              # Python dependencies
├── .env                          # Environment configuration
├── docker-compose.yml            # Qdrant + Server containers
├── Dockerfile                    # Server container build
├── start.sh                      # Development quick-start
├── run_tests.sh                  # Test runner
└── .gitignore
```

---

## Testing Instructions

### Prerequisites

1. **Docker** installed (for Qdrant)
2. **Python 3.11+** installed
3. Clone the repository

### Step 1: Start Qdrant (Vector Database)

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  qdrant/qdrant

# Verify it's running
curl http://localhost:6333/health
```

### Step 2: Start Firefighter Server

```bash
cd firefighter-server

# Option A: Quick start script
./start.sh

# Option B: Manual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

Server will be available at: `http://localhost:4100`

### Step 3: Run Automated Tests

```bash
# In a new terminal
cd firefighter-server

# Run all tests
./run_tests.sh

# Or run individual tests:
python tests/test_api.py           # API endpoint tests
python tests/test_client.py        # Simulated Pi (30 sec)
python tests/test_integration.py   # Full integration
```

### Step 4: Test with Simulated Pi Client

```bash
cd firefighter-server

# Send simulated sensor data for 60 seconds
python tests/test_client.py --duration 60

# The client will:
# 1. Connect via Socket.IO
# 2. Authenticate as firefighter_pi_001
# 3. Send foot pressure data at 10Hz
# 4. Send accelerometer data at 20Hz
```

### Step 5: Test sensor-hub Database Layer

```bash
cd sensor-hub

# Run database tests
./run_tests.sh
```

---

## Manual Testing Checklist

### Server Tests

- [ ] Health endpoint returns OK (`GET /health`)
- [ ] Can create session (`POST /api/sessions`)
- [ ] Can list sessions (`GET /api/sessions`)
- [ ] Can stop session (`POST /api/sessions/:id/stop`)
- [ ] Can export data as JSON (`GET /api/sessions/:id/export`)
- [ ] Can export data as CSV (`GET /api/sessions/:id/export?format=csv`)
- [ ] Can delete session (`DELETE /api/sessions/:id`)
- [ ] Similarity search works with data (`POST /api/query/similar`)

### Integration Tests

- [ ] Simulated Pi connects successfully
- [ ] Data appears in Qdrant (windows created)
- [ ] Session shows correct window count
- [ ] Export contains raw sensor data

### Real Hardware Tests (when Pi available)

- [ ] Pi connects to server via Socket.IO
- [ ] Foot sensor data stored in SQLite
- [ ] Accelerometer data stored in SQLite
- [ ] Data transmitted to server
- [ ] Network disconnect → data buffered in SQLite
- [ ] Network reconnect → buffered data sent

---

## Configuration Files

### sensor-hub/.env

```bash
# Socket.IO Server
SOCKETIO_SERVER_URL=http://localhost:4100
SOCKETIO_DEVICE_KEY=firefighter_pi_001
SOCKETIO_ENABLED=true

# Database
DB_FOOT_FILE=./database/foot.db
DB_ACCEL_FILE=./database/accel.db

# Sender Settings
SENDER_POLLING_INTERVAL=30
SENDER_MAX_RECORDS=100
```

### firefighter-server/.env

```bash
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=4100

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Auth
ALLOWED_DEVICE_KEYS=firefighter_pi_001,firefighter_pi_002
```

---

## Dependencies Added

### sensor-hub

```
python-socketio[client]>=5.10.0
requests>=2.31.0
```

### firefighter-server

```
flask>=3.0.0
flask-socketio>=5.3.0
flask-cors>=4.0.0
qdrant-client>=1.7.0
python-dotenv>=1.0.0
numpy>=1.24.0
gunicorn>=21.0.0
eventlet>=0.33.0
```

---

## Known Issues / Notes

1. **Window Size**: Sensor data is accumulated into 500ms windows before storing in Qdrant. If test duration is < 500ms, no windows will be created.

2. **Device Authentication**: Server accepts devices listed in `ALLOWED_DEVICE_KEYS`. Empty list = accept all.

3. **Session Persistence**: Sessions are stored in memory. Restart server = lose session list (but Qdrant data persists).

4. **Production Deployment**: Use `docker-compose up -d` for production with both Qdrant and server in containers.

---

## Contact

For questions about implementation, refer to:
- `sensor-hub/todo.md` - Detailed task checklist
- `sensor-hub/plan.md` - Architecture documentation
- Code comments in each file

---

**Ready for Testing!**
