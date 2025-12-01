#!/usr/bin/env python
"""
Live Posture Detection - Production Script
===========================================

Real-time posture detection using WT901BLE67 IMU sensor
Combines sensor connection (wit_ble.py) with posture analysis (analyze.py)

Usage:
    sudo python live.py -n WT901BLE67              # Connect by device name
    sudo python live.py -m c7:f7:92:82:f2:f9       # Connect by MAC address
    sudo python live.py -n WT901BLE67 --log        # Save data to file
    sudo python live.py --minimal                  # Minimal output mode
"""

from __future__ import print_function
import sys
import time
import argparse
import struct
from bluepy import btle

# Import from analyze.py
from analyze import (
    PostureAnalyzer, PostureConfig, SensorData, PostureState,
    parse_sensor_line, draw_posture_display, ANSI_RED, ANSI_GREEN,
    ANSI_YELLOW, ANSI_CYAN, ANSI_OFF, ANSI_BOLD
)

# ============================================================================
# SENSOR DATA PROCESSING
# ============================================================================

def hex_to_short(raw_data):
    """Convert raw bytes to signed short array"""
    return list(struct.unpack("hhh", bytearray(raw_data)))

def parse_wt901_data(raw_data):
    """
    Parse WT901BLE sensor packet

    Returns:
        SensorData object or None if parsing fails
    """
    if len(raw_data) < 20 or raw_data[0] != 0x55:
        return None

    if raw_data[1] == 0x61:
        # Combined packet: accelerometer + gyroscope + angle
        acc = [hex_to_short(raw_data[2:8])[i] / 32768.0 * 16 for i in range(0, 3)]
        gyro = [hex_to_short(raw_data[8:14])[i] / 32768.0 * 2000 for i in range(0, 3)]
        angle = [hex_to_short(raw_data[14:20])[i] / 32768.0 * 180 for i in range(0, 3)]

        return SensorData(
            acc_x=acc[0], acc_y=acc[1], acc_z=acc[2],
            gyro_x=gyro[0], gyro_y=gyro[1], gyro_z=gyro[2],
            roll=angle[0], pitch=angle[1], yaw=angle[2]
        )

    elif raw_data[1] == 0x71:
        # Magnetometer packet (optional, not used for posture detection)
        if raw_data[2] == 0x3A:
            mag = hex_to_short(raw_data[4:10])
            return None  # We don't use mag data for posture

    return None

# ============================================================================
# BLUETOOTH NOTIFICATION HANDLER
# ============================================================================

class PostureNotificationDelegate(btle.DefaultDelegate):
    """Handles BLE notifications and processes sensor data"""

    def __init__(self, analyzer, config):
        btle.DefaultDelegate.__init__(self)
        self.analyzer = analyzer
        self.config = config
        self.packet_count = 0
        self.last_update_time = time.time()
        self.current_state = PostureState.UNKNOWN
        self.current_confidence = 0.0
        self.current_details = {}
        self.current_sensor_data = None

    def handleNotification(self, cHandle, data):
        """Process incoming sensor data"""
        self.packet_count += 1

        # Parse multiple packets if needed (data can contain multiple 20-byte packets)
        size = len(data)
        index = 0

        while (size - index) >= 20:
            packet = data[index:index+20]
            sensor_data = parse_wt901_data(packet)

            if sensor_data:
                # Analyze posture
                state, confidence, details = self.analyzer.analyze(sensor_data)

                # Update current state
                self.current_state = state
                self.current_confidence = confidence
                self.current_details = details
                self.current_sensor_data = sensor_data

                # Log to file if enabled
                if self.config.get('log_file'):
                    self._log_data(sensor_data, state, confidence)

                # Update display based on mode
                current_time = time.time()
                if current_time - self.last_update_time >= self.config.get('update_interval', 0.2):
                    self._update_display()
                    self.last_update_time = current_time

            index += 20

    def _log_data(self, sensor_data, state, confidence):
        """Log data to file"""
        try:
            with open(self.config['log_file'], 'a') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write("%s,%s,%.2f,%s\n" % (timestamp, state, confidence, str(sensor_data)))
        except IOError:
            pass

    def _update_display(self):
        """Update display based on configured mode"""
        if not self.current_sensor_data:
            return

        mode = self.config.get('display_mode', 'full')

        if mode == 'full':
            # Full terminal UI
            draw_posture_display(
                self.current_state,
                self.current_confidence,
                self.current_sensor_data,
                self.current_details,
                self.analyzer
            )
        elif mode == 'minimal':
            # Minimal one-line output
            color = PostureState.get_color(self.current_state)
            emoji = PostureState.get_emoji(self.current_state)
            print("\r%s%s %s (%.0f%%) %s" % (
                color, emoji, self.current_state,
                self.current_confidence * 100, ANSI_OFF
            ), end='')
            sys.stdout.flush()
        elif mode == 'json':
            # JSON output for integration
            import json
            output = {
                'timestamp': time.time(),
                'posture': self.current_state,
                'confidence': self.current_confidence,
                'sensor': {
                    'acc': [self.current_sensor_data.acc_x,
                           self.current_sensor_data.acc_y,
                           self.current_sensor_data.acc_z],
                    'gyro': [self.current_sensor_data.gyro_x,
                            self.current_sensor_data.gyro_y,
                            self.current_sensor_data.gyro_z],
                    'angle': [self.current_sensor_data.roll,
                             self.current_sensor_data.pitch,
                             self.current_sensor_data.yaw]
                }
            }
            print(json.dumps(output))
            sys.stdout.flush()

# ============================================================================
# DEVICE SCANNER
# ============================================================================

class ScanDelegate(btle.DefaultDelegate):
    """Handles device scanning"""
    def __init__(self):
        btle.DefaultDelegate.__init__(self)

def scan_for_device(device_name, timeout=5, sensitivity=-128):
    """
    Scan for BLE device by name

    Returns:
        tuple: (mac_address, address_type) or (None, None) if not found
    """
    print(ANSI_CYAN + "Scanning for '%s'..." % device_name + ANSI_OFF)

    try:
        scanner = btle.Scanner().withDelegate(ScanDelegate())
        devices = scanner.scan(timeout)

        for dev in devices:
            if not dev.connectable or dev.rssi < sensitivity:
                continue

            for (sdid, desc, value) in dev.getScanData():
                if device_name in value:
                    print(ANSI_GREEN + "Found device: %s (%s), RSSI=%d dBm" %
                          (dev.addr, dev.addrType, dev.rssi) + ANSI_OFF)
                    return dev.addr, dev.addrType

        return None, None

    except btle.BTLEException as e:
        print(ANSI_RED + "Scan failed: %s" % str(e) + ANSI_OFF)
        return None, None

# ============================================================================
# MAIN CONNECTION AND PROCESSING
# ============================================================================

def connect_and_analyze(mac_address, addr_type, config):
    """
    Connect to sensor and start real-time posture analysis

    Args:
        mac_address: Device MAC address
        addr_type: 'public' or 'random'
        config: Configuration dictionary

    Returns:
        bool: True if successful, False otherwise
    """
    print(ANSI_CYAN + "Connecting to %s (%s)..." % (mac_address, addr_type) + ANSI_OFF)

    # Create posture analyzer
    posture_config = PostureConfig()
    analyzer = PostureAnalyzer(posture_config)

    # Create notification delegate
    delegate = PostureNotificationDelegate(analyzer, config)

    try:
        # Connect to device
        p = btle.Peripheral(mac_address, addr_type)
        p.setDelegate(delegate)
        print(ANSI_GREEN + "Connected!" + ANSI_OFF)

        # Set MTU
        try:
            p.setMTU(247)
        except:
            pass

        # Find characteristics
        print("Discovering services...")
        chList = p.getCharacteristics()

        read_handle = None
        write_handle = None

        for ch in chList:
            uuid_str = str(ch.uuid)
            if '0000ffe4' in uuid_str or '0000fff1' in uuid_str:
                read_handle = ch.getHandle()
            if '0000ffe9' in uuid_str or '0000fff2' in uuid_str:
                write_handle = ch.getHandle()

        if read_handle is None:
            print(ANSI_RED + "Error: Could not find sensor characteristic" + ANSI_OFF)
            p.disconnect()
            return False

        print("Found sensor characteristic at handle 0x%02X" % read_handle)

        # Enable notifications
        print("Enabling notifications...")
        descriptors = p.getDescriptors(read_handle)
        for desc in descriptors:
            if desc.uuid == 0x2902:  # CCCD
                p.writeCharacteristic(desc.handle, bytes([1, 0]))
                print(ANSI_GREEN + "Notifications enabled!" + ANSI_OFF)
                break

        # Display mode message
        if config.get('display_mode') == 'full':
            print("\n" + ANSI_BOLD + "Starting real-time posture detection..." + ANSI_OFF)
            print("Press Ctrl+C to stop\n")
            time.sleep(1)
        elif config.get('display_mode') == 'minimal':
            print(ANSI_BOLD + "Live: " + ANSI_OFF, end='')
            sys.stdout.flush()

        # Main loop - wait for notifications
        start_time = time.time()
        last_command_time = time.time()

        while True:
            if p.waitForNotifications(1.0):
                continue

            # Send periodic command to device if write handle exists
            if write_handle and (time.time() - last_command_time) > 1.0:
                try:
                    p.writeCharacteristic(write_handle, bytes([0xff, 0xaa, 0x27, 0x3A, 0x00]))
                    last_command_time = time.time()
                except:
                    pass

    except KeyboardInterrupt:
        print("\n\n" + ANSI_YELLOW + "Stopped by user" + ANSI_OFF)

        # Print statistics
        print("\n" + ANSI_BOLD + "Session Summary:" + ANSI_OFF)
        print("  Total packets: %d" % delegate.packet_count)
        print("  Total samples: %d" % analyzer.total_samples)
        print("  Duration: %.1fs" % (time.time() - start_time))
        print("\n  Posture Distribution:")
        for posture, count in analyzer.state_counts.items():
            if count > 0:
                percentage = (count / analyzer.total_samples) * 100 if analyzer.total_samples > 0 else 0
                print("    %s: %d (%.1f%%)" % (posture, count, percentage))

        return True

    except btle.BTLEException as e:
        print(ANSI_RED + "Connection error: %s" % str(e) + ANSI_OFF)
        return False

    except Exception as e:
        print(ANSI_RED + "Unexpected error: %s" % str(e) + ANSI_OFF)
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            p.disconnect()
            print(ANSI_GREEN + "Disconnected" + ANSI_OFF)
        except:
            pass

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Live Posture Detection - WT901BLE67 IMU Sensor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo %(prog)s -n WT901BLE67                    Connect by name
  sudo %(prog)s -m c7:f7:92:82:f2:f9             Connect by MAC
  sudo %(prog)s -n WT901BLE67 --log data.csv     Save data to file
  sudo %(prog)s --minimal                        Minimal display mode
  sudo %(prog)s --json                           JSON output mode

Note: Requires sudo for Bluetooth access
        """
    )

    parser.add_argument('-n', '--name', type=str, default='WT901BLE67',
                        help='Device name to search for (default: WT901BLE67)')
    parser.add_argument('-m', '--mac', type=str, default='',
                        help='Device MAC address (skip scan if provided)')
    parser.add_argument('-t', '--type', type=str, default='',
                        help='Address type: public or random (auto-detect if not provided)')
    parser.add_argument('--timeout', type=int, default=5,
                        help='Scan timeout in seconds (default: 5)')
    parser.add_argument('--log', type=str, metavar='FILE', default='',
                        help='Log data to file')
    parser.add_argument('--minimal', action='store_true',
                        help='Minimal one-line display mode')
    parser.add_argument('--json', action='store_true',
                        help='JSON output mode (for integration)')
    parser.add_argument('--update-rate', type=float, default=0.2,
                        help='Display update interval in seconds (default: 0.2)')

    args = parser.parse_args()

    # Determine display mode
    if args.json:
        display_mode = 'json'
    elif args.minimal:
        display_mode = 'minimal'
    else:
        display_mode = 'full'

    # Build configuration
    config = {
        'display_mode': display_mode,
        'update_interval': args.update_rate,
        'log_file': args.log if args.log else None
    }

    # Print header
    if display_mode == 'full':
        print(ANSI_BOLD + "="*70 + ANSI_OFF)
        print(ANSI_BOLD + ANSI_CYAN + "  Live Posture Detection - WT901BLE67 IMU Sensor" + ANSI_OFF)
        print(ANSI_BOLD + "="*70 + ANSI_OFF)
        print()

    # Get device address
    mac_address = None
    addr_type = None

    if args.mac:
        # Use provided MAC address
        mac_address = args.mac
        addr_type = args.type if args.type else btle.ADDR_TYPE_PUBLIC
        print("Using MAC: %s (%s)" % (mac_address, addr_type))
    else:
        # Scan for device
        mac_address, addr_type = scan_for_device(args.name, args.timeout)

        if not mac_address:
            print(ANSI_RED + "Device '%s' not found" % args.name + ANSI_OFF)
            print("Try scanning manually or specify MAC with -m option")
            return 1

    # Connect and start analysis
    success = connect_and_analyze(mac_address, addr_type, config)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
