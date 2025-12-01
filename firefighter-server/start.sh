#!/bin/bash
# Quick start script for development

echo "========================================"
echo "Firefighter Server - Development Mode"
echo "========================================"

# Check if Qdrant is running
echo "Checking Qdrant..."
if ! curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "Qdrant not running. Starting with Docker..."
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v $(pwd)/data/qdrant:/qdrant/storage \
        qdrant/qdrant

    echo "Waiting for Qdrant to start..."
    sleep 5
fi

echo "Qdrant is running"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install -r requirements.txt --quiet

# Start server
echo "Starting server on http://localhost:4100"
python server.py
