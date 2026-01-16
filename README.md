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

# Starting docker
firefighter-server git:(working) docker-compose up -d

# Activate virtual environment
source venv/bin/activate

# Send test data
python tests/realistic_activity_client.py --activity Standing --duration 30

# Start the server
python server.py
```

## Quick Links

- [sensor-hub docs](./sensor-hub/docs/important_documents.md)
- [firefighter-server docs](./firefighter-server/docs/important_documents.md)
