#!/usr/bin/env python3
"""Central BLE sensor monitoring system - monitors foot sensors and accelerometer concurrently."""

import asyncio
import signal
import sys
import os
from dotenv import load_dotenv
from sensors import FootSensor, AccelSensor


# Global flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n\nShutting down... Please wait for clean disconnect.")
    running = False


async def main():
    """Main entry point - monitor all sensors concurrently."""
    global running

    # Load environment variables
    load_dotenv()

    left_mac = os.getenv('LEFT_FOOT_MAC')
    right_mac = os.getenv('RIGHT_FOOT_MAC')
    accel_mac = os.getenv('ACCELEROMETER_MAC')

    # Validate MAC addresses
    if not left_mac or 'XX:XX' in left_mac.upper():
        print("Error: LEFT_FOOT_MAC not configured in .env")
        sys.exit(1)

    if not right_mac or 'XX:XX' in right_mac.upper():
        print("Warning: RIGHT_FOOT_MAC not configured in .env - skipping right foot")
        right_mac = None

    if not accel_mac or 'XX:XX' in accel_mac.upper():
        print("Warning: ACCELEROMETER_MAC not configured in .env - skipping accelerometer")
        accel_mac = None

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 60)
    print("Central BLE Sensor Monitor")
    print("=" * 60)
    print(f"Left Foot:      {left_mac}")
    print(f"Right Foot:     {right_mac or 'Not configured'}")
    print(f"Accelerometer:  {accel_mac or 'Not configured'}")
    print("=" * 60)
    print("\nConnecting to devices...\n")

    # Create sensor instances
    sensors = []

    left_foot = FootSensor(left_mac, "LEFT_FOOT")
    sensors.append(left_foot.monitor_loop())

    if right_mac:
        right_foot = FootSensor(right_mac, "RIGHT_FOOT")
        sensors.append(right_foot.monitor_loop())

    if accel_mac:
        accelerometer = AccelSensor(accel_mac, "ACCELEROMETER")
        sensors.append(accelerometer.monitor_loop())

    # Monitor all sensors concurrently
    try:
        await asyncio.gather(*sensors)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\nError: {e}")

    print("\n" + "=" * 60)
    print("All sensors disconnected. Goodbye!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
