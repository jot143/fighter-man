#!/usr/bin/env python3
"""BLE Device Scanner - Find nearby Bluetooth devices and their MAC addresses."""

import asyncio
import sys
from bleak import BleakScanner


async def scan_devices(duration=10):
    """
    Scan for BLE devices for specified duration.

    Args:
        duration: Scan duration in seconds (default: 10)

    Returns:
        dict: Dictionary of unique devices {mac: (name, rssi)}
    """
    print(f"Scanning for BLE devices ({duration} seconds)...")
    print("Please wait", end="", flush=True)

    devices_found = {}

    def detection_callback(device, advertisement_data):
        """Called when a device is discovered."""
        mac = device.address.lower()
        name = device.name or "Unknown"
        rssi = advertisement_data.rssi

        # Store only if new or has stronger signal
        if mac not in devices_found or devices_found[mac][1] < rssi:
            devices_found[mac] = (name, rssi)
            print(".", end="", flush=True)

    # Start scanning
    scanner = BleakScanner(detection_callback=detection_callback)

    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()

    print()  # New line after dots
    return devices_found


def display_results(devices):
    """
    Display scan results in a formatted table.

    Args:
        devices: Dictionary of devices {mac: (name, rssi)}
    """
    if not devices:
        print("\nNo devices found!")
        print("\nTroubleshooting:")
        print("1. Make sure Bluetooth is enabled")
        print("2. Ensure devices are powered on and in range")
        print("3. Try running with sudo: sudo python3 scanner.py")
        return

    # Sort by RSSI (strongest signal first)
    sorted_devices = sorted(devices.items(), key=lambda x: x[1][1], reverse=True)

    print(f"\n{'=' * 70}")
    print(f"Found {len(devices)} unique BLE device(s)")
    print(f"{'=' * 70}")
    print(f"{'MAC Address':<20} {'Device Name':<25} {'Signal':<10}")
    print(f"{'-' * 70}")

    for mac, (name, rssi) in sorted_devices:
        # Truncate long names
        if len(name) > 24:
            name = name[:21] + "..."

        # Signal strength indicator
        if rssi >= -60:
            signal = f"{rssi} dBm (Excellent)"
        elif rssi >= -70:
            signal = f"{rssi} dBm (Good)"
        elif rssi >= -80:
            signal = f"{rssi} dBm (Fair)"
        else:
            signal = f"{rssi} dBm (Weak)"

        print(f"{mac:<20} {name:<25} {signal:<10}")

    print(f"{'=' * 70}")
    print("\nTip: Copy the MAC address to your .env file")
    print("Example:")
    print("  LEFT_FOOT_MAC=ed:63:5b:c4:2d:92")
    print("  ACCELEROMETER_MAC=c7:f7:92:82:f2:f9")


async def main():
    """Main entry point."""
    try:
        print("=" * 70)
        print("BLE Device Scanner")
        print("=" * 70)

        devices = await scan_devices(duration=10)
        display_results(devices)

    except KeyboardInterrupt:
        print("\n\nScan cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure you run this script with sudo:")
        print("  sudo python3 scanner.py")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
