#!/usr/bin/env python3
"""
Simple BLE Insole Sensor Monitor
Connects to left foot sensor and displays pressure data in real-time
Press Ctrl+C to stop
"""

import asyncio
from bleak import BleakClient
import numpy as np
import signal
import sys

# ==================== CONFIGURATION ====================

# Left foot device
DEVICE_MAC = "ed:63:5b:c4:2d:92"

# BLE UUIDs
NOTIFY_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"  # Read/Notify
WRITE_UUID = "0000FFF2-0000-1000-8000-00805F9B34FB"   # Write

# Sensor configuration
# Excluded indices (no physical sensors at these positions)
EXCLUDED_INDICES = {8, 12, 16, 19, 20, 23}

# ==================== GLOBAL STATE ====================

data_buffer = ""
packet_count = 0
running = True

# ==================== FUNCTIONS ====================

def parse_packet(line):
    """Parse pressure data packet"""
    if not line or len(line) < 3:
        return None

    try:
        # Identify foot
        if line.startswith('L_'):
            foot = 'LEFT'
            data_str = line[2:]
        elif line.startswith('R_'):
            foot = 'RIGHT'
            data_str = line[2:]
        else:
            return None

        # Parse nested array format: [[a,b,c,d],[e,f,g,h],...]
        data_str = data_str.replace('[', '').replace(']', '')
        values = [float(x.strip()) for x in data_str.split(',') if x.strip()]

        if len(values) != 24:
            print(f"Warning: Expected 24 values, got {len(values)}")
            return None

        # Extract 18 active sensors (exclude indices 8,12,16,19,20,23)
        active_sensors = [v for i, v in enumerate(values) if i not in EXCLUDED_INDICES]

        return {
            'foot': foot,
            'matrix_6x4': np.array(values).reshape(6, 4),
            'active_18': np.array(active_sensors)
        }

    except Exception as e:
        print(f"Parse error: {e}")
        return None


def display_data(data):
    """Display pressure data to console"""
    global packet_count
    packet_count += 1

    print(f"\n{'='*60}")
    print(f"Packet #{packet_count} - {data['foot']} FOOT")
    print(f"{'='*60}")
    print(data['matrix_6x4'])
    print(f"\nMax: {data['active_18'].max():.1f} | "
          f"Avg: {data['active_18'].mean():.1f} | "
          f"Active: {np.count_nonzero(data['active_18'])}/18")


def notification_handler(sender, raw_data):
    """Handle incoming BLE notifications"""
    global data_buffer

    try:
        # Decode chunk
        chunk = raw_data.decode('utf-8')
        data_buffer += chunk

        # Process complete lines
        while '\n' in data_buffer:
            line, data_buffer = data_buffer.split('\n', 1)
            line = line.strip()

            if line:
                result = parse_packet(line)
                if result:
                    display_data(result)

    except Exception as e:
        print(f"Notification error: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\nStopping... Please wait for clean disconnect.")
    running = False


async def main():
    """Main function"""
    global running

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("="*60)
    print("BLE INSOLE SENSOR MONITOR")
    print("="*60)
    print(f"Device: {DEVICE_MAC}")
    print(f"Press Ctrl+C to stop\n")

    print(f"Connecting to device...")

    try:
        async with BleakClient(DEVICE_MAC, timeout=15.0) as client:
            print(f"Connected: {client.is_connected}")

            # Enable notifications
            await client.start_notify(NOTIFY_UUID, notification_handler)
            print("Notifications enabled")

            # Start data collection
            await client.write_gatt_char(WRITE_UUID, b'begin', response=True)
            print("Data collection started\n")
            print("Receiving data...\n")

            # Run until interrupted
            while running and client.is_connected:
                await asyncio.sleep(0.1)

            # Stop collection
            print("\nStopping data collection...")
            await client.write_gatt_char(WRITE_UUID, b'end', response=True)
            await client.stop_notify(NOTIFY_UUID)

            print(f"\nSession complete!")
            print(f"Total packets received: {packet_count}")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the device is powered on and in range")
        print("2. Check that Bluetooth is enabled on your system")
        print("3. Verify the MAC address is correct")
        sys.exit(1)


# ==================== ENTRY POINT ====================

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
