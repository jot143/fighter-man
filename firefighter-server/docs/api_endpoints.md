# API Endpoints - Purpose & Reasoning

## Overview

This document explains **why** each endpoint exists and how it fits into the Firefighter Activity Recognition pipeline.

---

## Data Flow

```
Firefighter wears sensors
        |
Pi collects BLE data (sensor-hub)
        |
Socket.IO streams to server
        |
Server accumulates 500ms windows
        |
Converts to 270-dim vectors (180 foot + 90 accel)
        |
Stores in Qdrant for ML training
        |
Researcher labels windows via PUT /api/sessions/:id
        |
Export labeled data for model training
```

---

## Socket.IO Events (`/iot` namespace)

### Why Socket.IO?

Real-time streaming is essential for continuous sensor data during firefighter training. HTTP polling would be too slow and resource-intensive for 10-100Hz sensor data.

| Event                | Direction    | Purpose                                                   |
| -------------------- | ------------ | --------------------------------------------------------- |
| `connect`            | Pi -> Server | Pi connects to start streaming data                       |
| `authenticate`       | Pi -> Server | Validate device with `device_key` before accepting data   |
| `foot_pressure_data` | Pi -> Server | Stream foot pressure sensor readings (18 values per foot) |
| `accelerometer_data` | Pi -> Server | Stream IMU data (acc/gyro/angle - 9 values)               |
| `session_started`    | Server -> Pi | Notify Pi that recording has begun                        |
| `session_stopped`    | Server -> Pi | Notify Pi that recording ended                            |

---

## REST API Endpoints

### Health Check

| Method | Endpoint  | Purpose                                          |
| ------ | --------- | ------------------------------------------------ |
| `GET`  | `/health` | Check server + Qdrant status, see active session |

**Why:** Quick way to verify the entire stack is operational before starting a training session.

---

### Session Management

| Method   | Endpoint                 | Purpose                                                 |
| -------- | ------------------------ | ------------------------------------------------------- |
| `POST`   | `/api/sessions`          | **Start recording** - Creates new session, notifies Pi  |
| `GET`    | `/api/sessions`          | List all recorded sessions                              |
| `PUT`    | `/api/sessions/:id`      | **Label data** - Assign activity labels to time windows |
| `DELETE` | `/api/sessions/:id`      | Delete session and all sensor data                      |
| `POST`   | `/api/sessions/:id/stop` | **Stop recording** - Flush buffers, mark complete       |

**Why Sessions Exist:**

- Group sensor data by training exercise (e.g., "Morning Drill 2024-12-02")
- Allow labeling data windows with activities for supervised ML training
- Export labeled datasets for model training
- Track which data has been processed/labeled

---

### Data Export

| Method | Endpoint                               | Purpose                          |
| ------ | -------------------------------------- | -------------------------------- |
| `GET`  | `/api/sessions/:id/export?format=json` | Export for ML training pipelines |
| `GET`  | `/api/sessions/:id/export?format=csv`  | Export for spreadsheet analysis  |

**Why:** ML pipelines need clean, labeled datasets in standard formats. Researchers may need CSV for manual review in Excel/Sheets.

---

### Similarity Search

| Method | Endpoint             | Purpose                                           |
| ------ | -------------------- | ------------------------------------------------- |
| `POST` | `/api/query/similar` | Find similar sensor patterns by vector similarity |

**Why This Is Powerful:**

- Find similar movement patterns across sessions
- "Show me other times the firefighter did this movement"
- Accelerate labeling: label one window, find 10 similar unlabeled ones
- Detect anomalies (find patterns that don't match known activities)
- Quality check: verify similar patterns have consistent labels

---

## Typical Workflows

### 1. Recording a Training Session

```bash
# 1. Check server is healthy
curl http://localhost:4100/health

# 2. Create a new session
curl -X POST http://localhost:4100/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "ladder_climb_drill_001"}'

# 3. Pi automatically starts streaming data via Socket.IO

# 4. After training, stop the session
curl -X POST http://localhost:4100/api/sessions/{session_id}/stop
```

### 2. Labeling Data

```bash
# 1. Get session details with windows
curl http://localhost:4100/api/sessions/{session_id}

# 2. Review windows and assign labels
curl -X PUT http://localhost:4100/api/sessions/{session_id} \
  -H "Content-Type: application/json" \
  -d '{
    "labels": {
      "window-id-1": "Walking",
      "window-id-2": "Walking",
      "window-id-3": "Climbing",
      "window-id-4": "Climbing"
    }
  }'
```

### 3. Exporting for ML Training

```bash
# Export all labeled windows as JSON
curl "http://localhost:4100/api/sessions/{session_id}/export?format=json&include_raw=true" \
  > training_data.json

# Or as CSV for quick review
curl "http://localhost:4100/api/sessions/{session_id}/export?format=csv" \
  > session_summary.csv
```

### 4. Finding Similar Patterns

```bash
# Given a "Walking" window, find similar unlabeled windows
curl -X POST http://localhost:4100/api/query/similar \
  -H "Content-Type: application/json" \
  -d '{
    "window_id": "known-walking-window-id",
    "limit": 20
  }'
```

---

## Activity Labels (Expected)

The system is designed to capture and label these firefighter activities:

| Label          | Description                  |
| -------------- | ---------------------------- |
| Walking        | Normal walking pace          |
| Running        | Fast movement                |
| Crawling       | Low crawl (smoke simulation) |
| Climbing       | Ladder ascent/descent        |
| Standing       | Stationary, upright          |
| Kneeling       | One or both knees down       |
| Sitting        | Seated with minimal foot contact |
| Carrying       | Carrying equipment/person    |
| Hose_Operation | Using fire hose              |
| Idle           | No activity / rest           |

---

## Vector Composition (270 dimensions)

Understanding how sensor data becomes ML-ready vectors:

```
Dimensions [0-179]  : 10 foot readings x 18 pressure values = 180 dims
Dimensions [180-269]: 10 accel readings x 9 values = 90 dims
                      (acc xyz, gyro xyz, angle roll/pitch/yaw)
```

Each 500ms window captures enough data to characterize the movement pattern while being granular enough for precise activity boundaries.

---

**Document Version:** 1.0
**Last Updated:** December 2, 2025
