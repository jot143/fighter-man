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
    print("\nConnecting to devices with 3s delays...")
    print("(Foot sensors are prioritized, accelerometer data is throttled)\n")

    # Create sensor instances and tasks with delays
    tasks = []

    # Connect to left foot first (critical sensor)
    print("[PRIORITY] Connecting to left foot sensor first...")
    left_foot = FootSensor(left_mac, "LEFT_FOOT")
    tasks.append(asyncio.create_task(left_foot.monitor_loop()))
    await asyncio.sleep(3)  # Increased delay to avoid BLE stack overload

    # Connect to right foot
    if right_mac:
        print("[PRIORITY] Connecting to right foot sensor...")
        right_foot = FootSensor(right_mac, "RIGHT_FOOT")
        tasks.append(asyncio.create_task(right_foot.monitor_loop()))
        await asyncio.sleep(3)  # Increased delay to avoid BLE stack overload

    # Connect to accelerometer (with throttling, lower priority)
    if accel_mac:
        print("[SECONDARY] Connecting to accelerometer (throttled to 20Hz)...")
        accelerometer = AccelSensor(accel_mac, "ACCELEROMETER", throttle=5)
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
