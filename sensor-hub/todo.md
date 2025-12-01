# Firefighter Data Pipeline - TODO

## Status Legend

- [ ] Not started
- [~] In progress
- [x] Completed

---

## Phase 1: sensor-hub (Raspberry Pi)

### 1.1 Setup & Infrastructure

- [x] Copy reusable code from ssd-pi-engine
  - [x] `lib/config.py` - configuration management
  - [x] `lib/socket_client.py` - Socket.IO client
  - [x] `lib/database/base.py` - SQLite base class
  - [x] `senders/base.py` - sender base class
- [x] Update `requirements.txt` with new dependencies
- [x] Create folder structure (`lib/`, `senders/`, `database/`)
- [x] Create `lib/__init__.py`
- [x] Create `senders/__init__.py`

### 1.2 Database Layer (SQLite Backup)

- [x] Create `lib/database/__init__.py`
- [x] Create `lib/database/foot_db.py`
  - [x] Define table schema (foot_readings)
  - [x] Implement insert/fetch/delete methods
- [x] Create `lib/database/accel_db.py`
  - [x] Define table schema (accel_readings)
  - [x] Implement insert/fetch/delete methods
- [x] Test database operations (tests/test_database.py)

### 1.3 Sender Layer (Data Transmission)

- [x] Create `senders/__init__.py`
- [x] Adapt `senders/base.py` for sensor-hub
- [x] Create `senders/foot_sender.py`
  - [x] Define transform_record()
  - [x] Set Socket.IO event name
- [x] Create `senders/accel_sender.py`
  - [x] Define transform_record()
  - [x] Set Socket.IO event name
- [x] Create entry points: `send_foot_data.py`, `send_accel_data.py`

### 1.4 Integration with Existing Code

- [x] Modify `main.py`
  - [x] Add SQLite storage callback
  - [x] Add Socket.IO broadcast callback
  - [x] Handle both sensors with unified callback
- [x] Update `.env` with new configuration
  - [x] Socket.IO server URL
  - [x] Database paths
  - [x] Sender settings

### 1.5 Testing (Pi Side)

- [x] Create test scripts (tests/test_database.py)
- [x] Create test runner (run_tests.sh)
- [ ] Test with real BLE sensors (manual)
- [ ] Verify data stored in SQLite (manual)
- [ ] Verify data transmitted via Socket.IO (manual)
- [ ] Test failure scenario (disconnect network) (manual)
- [ ] Verify retry behavior works (manual)

---

## Phase 2: firefighter-server (Server)

### 2.1 Project Setup

- [x] Create `firefighter-server/` folder
- [x] Create `requirements.txt`
- [x] Create folder structure (`lib/`, `api/`, `data/`)
- [x] Create `lib/__init__.py`
- [x] Create `api/__init__.py`
- [x] Create `.env` template

### 2.2 Socket.IO + Flask Server

- [x] Create `server.py`
  - [x] Flask app setup
  - [x] Socket.IO namespace `/iot`
  - [x] Device authentication
  - [x] Event handlers for sensor data
- [x] Create `lib/config.py`

### 2.3 Vector Database (Qdrant Docker)

- [x] Set up Qdrant Docker container (docker-compose.yml)
- [x] Create `lib/vector_store.py`
  - [x] Initialize Qdrant client connection
  - [x] Create collections (sensor_windows)
  - [x] Implement add_reading() with windowing
  - [x] Implement query_similar()
  - [x] Implement get_session_data()

### 2.4 REST API

- [x] Create REST endpoints in `server.py`
  - [x] POST /api/sessions (create)
  - [x] GET /api/sessions (list)
  - [x] GET /api/sessions/:id (details)
  - [x] PUT /api/sessions/:id (update labels)
  - [x] DELETE /api/sessions/:id (delete)
  - [x] POST /api/sessions/:id/stop (stop recording)
- [x] Query endpoints
  - [x] POST /api/query/similar
- [x] Export endpoints
  - [x] GET /api/sessions/:id/export (JSON/CSV)

### 2.5 Testing (Server Side)

- [x] Create API test scripts (tests/test_api.py)
- [x] Create test client (tests/test_client.py)
- [x] Create integration test (tests/test_integration.py)
- [x] Create test runner (run_tests.sh)
- [ ] Run tests with real Qdrant (manual)
- [ ] Test similarity search with real data (manual)

---

## Phase 3: Integration

### 3.1 End-to-End Testing

- [x] Create integration test script
- [ ] Connect real Pi to firefighter-server (manual)
- [ ] Record test session (1 minute) (manual)
- [ ] Verify data in Qdrant (manual)
- [ ] Test export format (manual)

### 3.2 Failure Scenarios

- [ ] Test network disconnect during recording (manual)
- [ ] Verify SQLite backup on Pi (manual)
- [ ] Verify retry after reconnect (manual)
- [ ] Verify no data loss (manual)

### 3.3 Performance

- [ ] Measure latency (sensor → server) (manual)
- [ ] Test with high data rate (manual)
- [ ] Verify Pi memory/CPU usage (manual)
- [ ] Verify server storage growth (manual)

---

## Future Phases (Not in Current Scope)

### Phase 4: Annotation Tool Integration

- [ ] Connect annotation UI to server API
- [ ] Sync video with sensor data
- [ ] Add labeling functionality

### Phase 5: ML Training

- [ ] Export labeled data
- [ ] Train LSTM/CNN model
- [ ] Deploy model for real-time inference

---

## Testing Commands

### sensor-hub Tests

```bash
cd sensor-hub

# Run database tests
./run_tests.sh

# Or manually:
python tests/test_database.py
```

### firefighter-server Tests

```bash
cd firefighter-server

# 1. Start Qdrant (if not running)
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 2. Start server
./start.sh

# 3. In another terminal, run tests
./run_tests.sh

# Or run individual tests:
python tests/test_api.py           # API endpoint tests
python tests/test_client.py        # Simulated Pi client
python tests/test_integration.py   # Full integration test
```

### Simulated Pi Client

```bash
cd firefighter-server

# Run simulated Pi sending data for 30 seconds
python tests/test_client.py --duration 30

# With custom server
python tests/test_client.py --server http://your-server:4100 --duration 60
```

---

## Quick Start Commands

### Start Qdrant (Docker)

```bash
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Start Server (Development)

```bash
cd firefighter-server
./start.sh
```

### Start Server (Production with Docker)

```bash
cd firefighter-server
docker-compose up -d
```

### API Endpoints

| Method | Endpoint                      | Description                |
| ------ | ----------------------------- | -------------------------- |
| GET    | /health                       | Server health check        |
| POST   | /api/sessions                 | Create new session         |
| GET    | /api/sessions                 | List all sessions          |
| GET    | /api/sessions/:id             | Get session details        |
| PUT    | /api/sessions/:id             | Update session/labels      |
| DELETE | /api/sessions/:id             | Delete session             |
| POST   | /api/sessions/:id/stop        | Stop recording session     |
| GET    | /api/sessions/:id/export      | Export session data        |
| POST   | /api/query/similar            | Find similar patterns      |

---

## Files Created

### Phase 1 (sensor-hub)

| File                          | Purpose                           |
| ----------------------------- | --------------------------------- |
| `lib/__init__.py`             | Module init                       |
| `lib/config.py`               | Type-safe configuration           |
| `lib/socket_client.py`        | Socket.IO client with reconnect   |
| `lib/database/__init__.py`    | Database module init              |
| `lib/database/base.py`        | Abstract SQLite base class        |
| `lib/database/foot_db.py`     | Foot sensor database              |
| `lib/database/accel_db.py`    | Accelerometer database            |
| `senders/__init__.py`         | Senders module init               |
| `senders/base.py`             | Base sender with retry logic      |
| `senders/foot_sender.py`      | Foot data sender                  |
| `senders/accel_sender.py`     | Accelerometer data sender         |
| `send_foot_data.py`           | Entry point for foot sender       |
| `send_accel_data.py`          | Entry point for accel sender      |
| `tests/__init__.py`           | Tests module init                 |
| `tests/test_database.py`      | Database unit tests               |
| `run_tests.sh`                | Test runner script                |

### Phase 2 (firefighter-server)

| File                          | Purpose                           |
| ----------------------------- | --------------------------------- |
| `server.py`                   | Flask + Socket.IO main server     |
| `lib/__init__.py`             | Module init                       |
| `lib/config.py`               | Server configuration              |
| `lib/vector_store.py`         | Qdrant wrapper with windowing     |
| `api/__init__.py`             | API module init                   |
| `requirements.txt`            | Python dependencies               |
| `.env`                        | Environment configuration         |
| `docker-compose.yml`          | Qdrant + Server containers        |
| `Dockerfile`                  | Server container build            |
| `start.sh`                    | Development quick-start script    |
| `.gitignore`                  | Git ignore rules                  |
| `tests/__init__.py`           | Tests module init                 |
| `tests/test_api.py`           | REST API tests                    |
| `tests/test_client.py`        | Simulated Pi client               |
| `tests/test_integration.py`   | Full integration test             |
| `run_tests.sh`                | Test runner script                |

---

## Questions for Team Review

1. ~~Is ChromaDB the right choice for vector database?~~ **Resolved: Using Qdrant**
2. ~~Should we use the same Socket.IO namespace (`/iot`) as ssd-pi-engine?~~ **Resolved: Yes**
3. What is the expected data volume (recordings per day)?
4. Where will firefighter-server be deployed?
