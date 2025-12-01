#!/bin/bash
# Test runner for sensor-hub

set -e

echo "========================================"
echo "Sensor Hub - Test Suite"
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

echo ""
echo "========================================"
echo "Running Database Tests"
echo "========================================"
python tests/test_database.py

echo ""
echo "========================================"
echo "All tests completed!"
echo "========================================"
