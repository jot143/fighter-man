# Firefighter Activity Recognition - Data Pipeline

Data collection system for training an AI model that recognizes firefighter activities using wearable sensor data.

## Projects

| Folder             | Description                                                             |
| ------------------ | ----------------------------------------------------------------------- |
| sensor-hub         | Raspberry Pi - collects BLE sensor data (foot pressure + accelerometer) |
| firefighter-server | Server - stores data using Qdrant vector database                       |

## Quick Start

### Firefighter Server

```bash
cd firefighter-server

# Start the server with Docker (includes PostgreSQL and Qdrant)
docker-compose up -d

# (Optional) Send realistic test data
source venv/bin/activate
python tests/realistic_activity_client.py --activity Standing --duration 30

# Open the frontend
cd ../frontend
open record.html

# Stop the server (from firefighter-server directory)
cd ../firefighter-server
docker-compose down
```

## Quick Links

- [sensor-hub docs](./sensor-hub/docs/important_documents.md)
- [firefighter-server docs](./firefighter-server/docs/important_documents.md)
