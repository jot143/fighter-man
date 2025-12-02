#!/bin/bash
# Quick stop script for development

echo "========================================"
echo "Firefighter Server - Stopping Services"
echo "========================================"

# Stop Python server on port 4100
echo "Stopping server..."
SERVER_PID=$(lsof -ti :4100 2>/dev/null)
if [ -n "$SERVER_PID" ]; then
    kill $SERVER_PID 2>/dev/null
    sleep 1
    # Force kill if still running
    if lsof -ti :4100 > /dev/null 2>&1; then
        kill -9 $(lsof -ti :4100) 2>/dev/null
    fi
    echo "Server stopped"
else
    echo "Server not running"
fi

# Optionally stop Qdrant (pass --all flag)
if [ "$1" = "--all" ]; then
    echo "Stopping Qdrant..."
    docker stop qdrant 2>/dev/null && echo "Qdrant stopped" || echo "Qdrant not running"
fi

echo "========================================"
echo "Done"
echo "========================================"
