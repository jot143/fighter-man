#!/usr/bin/env python3
"""Central BLE sensor monitoring system - monitors foot sensors and accelerometer concurrently."""

import asyncio
import sys
import os
from dotenv import load_dotenv
from sensors import FootSensor, AccelSensor


async def main():
    """Main entry point - monitor all sensors concurrently."""
    # Load environment variables
    load_dotenv()

    left_mac = os.getenv('LEFT_FOOT_MAC')
    right_mac = os.getenv('RIGHT_FOOT_MAC')
    accel_mac = os.getenv('ACCELEROMETER_MAC')

    # Load performance tuning parameters with defaults
    try:
        foot_throttle = int(os.getenv('FOOT_THROTTLE', '2'))
        accel_throttle = int(os.getenv('ACCEL_THROTTLE', '5'))
        connection_retries = int(os.getenv('CONNECTION_RETRIES', '3'))

        # Validate ranges
        foot_throttle = max(1, min(10, foot_throttle))
        accel_throttle = max(1, min(10, accel_throttle))
        connection_retries = max(1, min(10, connection_retries))
    except ValueError:
        print("Warning: Invalid performance tuning values in .env, using defaults")
        foot_throttle = 2
        accel_throttle = 5
        connection_retries = 3

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

    print("=" * 60)
    print("Sensor Hub - BLE Monitor")
    print("=" * 60)
    print(f"Left Foot:      {left_mac}")
    print(f"Right Foot:     {right_mac or 'Not configured'}")
    print(f"Accelerometer:  {accel_mac or 'Not configured'}")
    print("=" * 60)
    print(f"Throttle:       Foot={foot_throttle}, Accel={accel_throttle}")
    print(f"Retries:        {connection_retries} attempts per device")
    print("=" * 60)
    print("\nConnecting to devices with 3s delays...\n")

    # Create sensor instances and tasks with delays
    tasks = []

    # Connect to left foot first (critical sensor)
    print(f"[PRIORITY] Connecting to left foot sensor (throttle={foot_throttle})...")
    left_foot = FootSensor(left_mac, "LEFT_FOOT", throttle=foot_throttle)
    tasks.append(asyncio.create_task(left_foot.monitor_loop()))
    await asyncio.sleep(3)  # Increased delay to avoid BLE stack overload

    # Connect to right foot
    if right_mac:
        print(f"[PRIORITY] Connecting to right foot sensor (throttle={foot_throttle})...")
        right_foot = FootSensor(right_mac, "RIGHT_FOOT", throttle=foot_throttle)
        tasks.append(asyncio.create_task(right_foot.monitor_loop()))
        await asyncio.sleep(3)  # Increased delay to avoid BLE stack overload

    # Connect to accelerometer (with throttling, lower priority)
    if accel_mac:
        print(f"[SECONDARY] Connecting to accelerometer (throttle={accel_throttle})...")
        accelerometer = AccelSensor(accel_mac, "ACCELEROMETER", throttle=accel_throttle)
        tasks.append(asyncio.create_task(accelerometer.monitor_loop()))

    print("\n" + "=" * 60)
    print("All configured devices connected. Monitoring... (Ctrl+C to stop)")
    print("=" * 60 + "\n")

    # Monitor all sensors concurrently
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("\n\nShutting down... Cleaning up connections.")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        # Wait for all tasks to finish cleanup
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("\n\nShutting down... Cleaning up connections.")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        # Wait for all tasks to finish cleanup
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"\nError: {e}")
        # Cancel all tasks on error
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    print("\n" + "=" * 60)
    print("All sensors disconnected. Goodbye!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted during startup.")
