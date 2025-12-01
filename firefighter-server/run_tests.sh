#!/bin/bash
# Master test runner for firefighter-server

set -e

echo "========================================"
echo "Firefighter Server - Test Suite"
echo "========================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt --quiet
pip install python-socketio[client] requests --quiet

echo ""
echo "========================================"
echo "1. Checking Prerequisites"
echo "========================================"

# Check Qdrant
echo -n "Qdrant: "
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo "Running"
else
    echo "NOT RUNNING"
    echo ""
    echo "Start Qdrant first:"
    echo "  docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant"
    exit 1
fi

# Check server
echo -n "Server: "
if curl -s http://localhost:4100/health > /dev/null 2>&1; then
    echo "Running"
else
    echo "NOT RUNNING"
    echo ""
    echo "Start server first:"
    echo "  ./start.sh"
    exit 1
fi

echo ""
echo "========================================"
echo "2. Running API Tests"
echo "========================================"
python tests/test_api.py

echo ""
echo "========================================"
echo "3. Running Integration Test"
echo "========================================"
python tests/test_integration.py --duration 3

echo ""
echo "========================================"
echo "All tests completed!"
echo "========================================"
