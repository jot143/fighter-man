# Firefighter Activity Recognition - Data Pipeline Plan

## Project Overview

Build a data collection and storage system for training an AI model that recognizes firefighter activities (Walking, Running, Crawling, Sitting, Turn Left, Turn Right) using wearable sensor data.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   RASPBERRY PI (sensor-hub)              SERVER (firefighter-server)         │
│   ┌─────────────────────────┐           ┌──────────────────────────────┐    │
│   │                         │           │                              │    │
│   │  FootSensor (BLE)       │           │  Socket.IO Receiver          │    │
│   │  AccelSensor (BLE)      │           │          ↓                   │    │
│   │          ↓              │           │  Qdrant (Vector Database)    │    │
│   │  SQLite Buffer          │──────────▶│          ↓                   │    │
│   │  (backup on failure)    │ Socket.IO │  REST API                    │    │
│   │          ↓              │   or      │   • Session management       │    │
│   │  Socket.IO Sender       │  HTTP     │   • Similarity search        │    │
│   │  (HTTP fallback)        │           │   • ML training export       │    │
│   │                         │           │                              │    │
│   └─────────────────────────┘           └──────────────────────────────┘    │
│                                                                              │
│         COLLECT & BROADCAST                    STORE & PROCESS              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: sensor-hub (Raspberry Pi)

### Goal

Adapt sensor-hub to broadcast data in real-time with SQLite backup for network failures.

### Pattern

Follow ssd-pi-engine architecture:

- **Broadcast immediately** via Socket.IO
- **Store locally** in SQLite as backup
- **Retry on failure** with exponential backoff
- **Delete after success**

### New Structure

```
sensor-hub/
├── main.py                      # Modified: add storage + broadcast
├── sensors/                     # Existing (unchanged)
├── lib/                         # NEW: shared utilities
│   ├── config.py                # Configuration management
│   ├── socket_client.py         # Socket.IO client
│   └── database/                # SQLite layer
│       ├── base.py
│       ├── foot_db.py
│       └── accel_db.py
├── senders/                     # NEW: background transmission
│   ├── base.py
│   ├── foot_sender.py
│   └── accel_sender.py
└── database/                    # SQLite files (runtime)
```

### Data Flow

```
BLE Sensors → Parse → Store in SQLite → Broadcast via Socket.IO
                              ↓
                    Delete after successful send
                              ↓
                    Retry if failed (exponential backoff)
```

---

## Phase 2: firefighter-server (New Instance)

### Goal

Create a server that receives sensor data and stores in Qdrant for AI/ML use cases.

### Docker Setup (Qdrant)

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

### Why Qdrant (Vector Database)

- Production-ready, battle-tested
- Better performance and memory efficiency
- Advanced filtering (range, geo, nested conditions)
- REST + gRPC APIs
- Horizontal scaling support
- Official Docker image

### Structure

```
firefighter-server/
├── server.py                    # Socket.IO + Flask
├── lib/
│   ├── config.py
│   └── vector_store.py          # Qdrant wrapper
├── api/
│   ├── sessions.py              # Session CRUD
│   ├── query.py                 # Similarity search
│   └── export.py                # ML export
├── docker-compose.yml           # Qdrant + Flask containers
└── .env
```

### Data Model

Store sensor readings as **time windows** (500ms each):

| Field     | Description                          |
| --------- | ------------------------------------ |
| id        | `{session}_{timestamp}_{device}`     |
| embedding | Normalized sensor values (vector)    |
| document  | Raw JSON readings                    |
| metadata  | session_id, device, timestamp, label |

### API Endpoints

| Endpoint                       | Purpose                        |
| ------------------------------ | ------------------------------ |
| `POST /api/sessions`           | Start recording session        |
| `GET /api/sessions/:id/export` | Export for annotation tool     |
| `POST /api/query/similar`      | Find similar movement patterns |

---

## Phase 3: Integration & Testing

### Goals

1. Connect Pi to server
2. Test end-to-end data flow
3. Verify failure/retry behavior
4. Test similarity search

### Success Criteria

- [ ] Pi broadcasts sensor data in real-time
- [ ] Server receives and stores in Qdrant
- [ ] Data survives network failures (SQLite backup works)
- [ ] Similarity search returns meaningful results
- [ ] Export format compatible with annotation tool

---

## Technology Stack

### sensor-hub (Pi)

- Python 3.11+
- bleak (BLE)
- SQLite3 (backup buffer)
- python-socketio (transmission)

### firefighter-server

- Python 3.11+
- Flask + Flask-SocketIO
- Qdrant (vector database, Docker)
- REST API

---

## Key Design Decisions

1. **SQLite on Pi, Qdrant on Server**

   - Pi: lightweight, reliable backup
   - Server: production-ready vector storage

2. **Socket.IO with HTTP fallback**

   - Real-time when possible
   - Reliable when network unstable

3. **Time windows as vectors**

   - 500ms windows = meaningful movement patterns
   - Enables similarity search for annotation

4. **Follow ssd-pi-engine patterns**
   - Proven architecture
   - Reusable code
   - Team familiarity

---

## References

- ssd-pi-engine: `../ssd-pi-engine/` (same parent directory)
- Project spec: `doc.pdf` (Firefighter Activity Recognition)
