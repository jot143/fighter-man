#!/bin/bash
# Helper script to cleanly run sensor-hub

echo "Cleaning up..."

# Kill any existing Python processes
sudo pkill -9 python3 2>/dev/null

# Wait a moment
sleep 2

# Restart Bluetooth service
echo "Restarting Bluetooth..."
sudo systemctl restart bluetooth

# Wait for Bluetooth to stabilize
sleep 3

# Clear Python cache
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo ""
echo "Starting sensor-hub..."
echo ""

# Run the monitor
sudo python3 main.py
