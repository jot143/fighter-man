#!/usr/bin/env python
from __future__ import print_function
from bluepy import btle
import struct
import time
import sys
import argparse

# ANSI Colors for output
ANSI_RED = '\033[31m'
ANSI_GREEN = '\033[32m'
ANSI_YELLOW = '\033[33m'
ANSI_CYAN = '\033[36m'
ANSI_OFF = '\033[0m'

def print_header(msg):
    print("\n" + "="*70)
    print(ANSI_CYAN + msg + ANSI_OFF)
    print("="*70)

def print_success(msg):
    print(ANSI_GREEN + "[SUCCESS] " + msg + ANSI_OFF)

def print_error(msg):
    print(ANSI_RED + "[ERROR] " + msg + ANSI_OFF)

def print_warning(msg):
    print(ANSI_YELLOW + "[WARNING] " + msg + ANSI_OFF)

def print_info(msg):
    print("[INFO] " + msg)

def hex_to_short(raw_data):
    return list(struct.unpack("hhh", bytearray(raw_data)))

def parse_wt901_data(raw_data):
    """Parse WT901BLE sensor data"""
    if len(raw_data) < 20 or raw_data[0] != 0x55:
        return None

    if raw_data[1] == 0x61:
        acc = [hex_to_short(raw_data[2:8])[i] / 32768.0 * 16 for i in range(0, 3)]
        gyro = [hex_to_short(raw_data[8:14])[i] / 32768.0 * 2000 for i in range(0, 3)]
        angle = [hex_to_short(raw_data[14:20])[i] / 32768.0 * 180 for i in range(0, 3)]
        return "acc: %.2f, %.2f, %.2f | gyro: %.2f, %.2f, %.2f | angle: %.2f, %.2f, %.2f" % \
               (acc[0], acc[1], acc[2], gyro[0], gyro[1], gyro[2], angle[0], angle[1], angle[2])
    elif raw_data[1] == 0x71 and raw_data[2] == 0x3A:
        mag = hex_to_short(raw_data[4:10])
        return "mag: %d, %d, %d" % (mag[0], mag[1], mag[2])
    return None

class NotifyDelegate(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.data_count = 0

    def handleNotification(self, cHandle, data):
        self.data_count += 1
        print_info("Notification #%d from handle 0x%02X" % (self.data_count, cHandle))
        print("  Raw data length:", len(data))
        print("  Raw hex:", data.hex() if hasattr(data, 'hex') else data.encode('hex'))

        # Try to parse as WT901BLE data
        size = len(data)
        index = 0
        while (size - index) >= 20:
            parsed = parse_wt901_data(data[index:index+20])
            if parsed:
                print_success("  Parsed: " + parsed)
            index += 20

def test_scan(device_name, timeout=5):
    """Test 1: Scan for the device"""
    print_header("TEST 1: SCANNING FOR DEVICE")
    print_info("Scanning for '%s' (timeout: %ds)..." % (device_name, timeout))

    try:
        scanner = btle.Scanner()
        devices = scanner.scan(timeout)

        print_info("Found %d devices total" % len(devices))

        target_device = None
        for dev in devices:
            is_target = False
            dev_name = None

            for (adtype, desc, value) in dev.getScanData():
                if desc in ['Complete Local Name', 'Short Local Name']:
                    dev_name = value
                if device_name in value:
                    is_target = True

            if is_target or dev_name:
                marker = ANSI_GREEN + ">>> TARGET <<<" + ANSI_OFF if is_target else ""
                print("\n  Device: %s (%s) %s" % (dev.addr, dev.addrType, marker))
                print("    RSSI: %d dBm" % dev.rssi)
                print("    Connectable: %s" % dev.connectable)
                if dev_name:
                    print("    Name: %s" % dev_name)

                if is_target:
                    target_device = dev

        if target_device:
            print_success("Found target device!")
            return target_device
        else:
            print_error("Target device not found")
            return None

    except Exception as e:
        print_error("Scan failed: " + str(e))
        return None

def test_connect_public(mac):
    """Test 2: Try connecting with PUBLIC address type"""
    print_header("TEST 2: CONNECT WITH PUBLIC ADDRESS TYPE")
    print_info("MAC: %s" % mac)
    print_info("Address Type: public")

    try:
        print_info("Attempting connection (10s timeout)...")
        p = btle.Peripheral()

        # Set a connection timeout
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Connection timeout")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)

        p.connect(mac, btle.ADDR_TYPE_PUBLIC)
        signal.alarm(0)

        print_success("Connected with PUBLIC address type!")
        p.disconnect()
        return True

    except TimeoutError:
        print_error("Connection timed out (hung)")
        return False
    except btle.BTLEDisconnectError as e:
        print_error("Connection failed: " + str(e))
        return False
    except Exception as e:
        print_error("Unexpected error: " + str(e))
        return False

def test_connect_random(mac):
    """Test 3: Try connecting with RANDOM address type"""
    print_header("TEST 3: CONNECT WITH RANDOM ADDRESS TYPE")
    print_info("MAC: %s" % mac)
    print_info("Address Type: random")

    try:
        print_info("Attempting connection (10s timeout)...")
        p = btle.Peripheral()

        # Set a connection timeout
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("Connection timeout")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)

        p.connect(mac, btle.ADDR_TYPE_RANDOM)
        signal.alarm(0)

        print_success("Connected with RANDOM address type!")
        p.disconnect()
        return True

    except TimeoutError:
        print_error("Connection timed out (hung)")
        return False
    except btle.BTLEDisconnectError as e:
        print_error("Connection failed: " + str(e))
        return False
    except Exception as e:
        print_error("Unexpected error: " + str(e))
        return False

def test_full_connection(mac, addr_type):
    """Test 4: Full connection with service discovery"""
    print_header("TEST 4: FULL CONNECTION WITH SERVICE DISCOVERY")
    print_info("MAC: %s" % mac)
    print_info("Address Type: %s" % addr_type)

    try:
        print_info("Connecting...")
        p = btle.Peripheral(mac, addr_type)
        print_success("Connected!")

        # Try to set MTU
        try:
            p.setMTU(247)
            print_info("MTU set to 247")
        except Exception as e:
            print_warning("Could not set MTU: %s" % str(e))

        # Discover services
        print_info("\nDiscovering services...")
        services = p.getServices()
        service_list = list(services)
        print_info("Found %d services" % len(service_list))

        for svc in service_list:
            print("  Service: %s" % svc.uuid)
            if svc.uuid in [btle.UUID(0xFFE5), btle.UUID(0xFFF0)]:
                print_success("    -> Common WT901BLE service!")

        # Get all characteristics
        print_info("\nDiscovering characteristics...")
        chList = p.getCharacteristics()
        print_info("Found %d characteristics" % len(chList))

        read_handle = None
        write_handle = None

        print("\n  Handle | UUID                                 | Properties")
        print("  " + "-"*68)

        for ch in chList:
            uuid_str = str(ch.uuid)
            handle = ch.getHandle()
            props = ch.propertiesToString()

            print("  0x%02X   | %s | %s" % (handle, uuid_str, props))

            # Look for WT901BLE characteristics
            if '0000ffe4' in uuid_str or '0000fff1' in uuid_str:
                read_handle = handle
                print_success("         -> Potential READ/NOTIFY handle")
            if '0000ffe9' in uuid_str or '0000fff2' in uuid_str:
                write_handle = handle
                print_success("         -> Potential WRITE handle")

        p.disconnect()
        print_success("\nDisconnected successfully")

        return (read_handle, write_handle)

    except Exception as e:
        print_error("Failed: " + str(e))
        import traceback
        traceback.print_exc()
        return (None, None)

def test_notifications(mac, addr_type, read_handle, write_handle):
    """Test 5: Enable notifications and read data"""
    print_header("TEST 5: ENABLE NOTIFICATIONS AND READ DATA")
    print_info("MAC: %s" % mac)
    print_info("Address Type: %s" % addr_type)
    print_info("Read Handle: 0x%02X" % read_handle if read_handle else "Unknown")
    print_info("Write Handle: 0x%02X" % write_handle if write_handle else "Unknown")

    if not read_handle:
        print_error("No read handle available, skipping test")
        return False

    try:
        print_info("Connecting...")
        p = btle.Peripheral(mac, addr_type)
        p.setDelegate(NotifyDelegate())
        print_success("Connected!")

        # Enable notifications
        print_info("\nEnabling notifications...")
        descriptors = p.getDescriptors(read_handle)

        cccd_found = False
        for desc in descriptors:
            print("  Descriptor: UUID=%s, Handle=0x%02X" % (desc.uuid, desc.handle))
            if desc.uuid == 0x2902:  # CCCD
                print_info("  Found CCCD, writing 0x0100...")
                p.writeCharacteristic(desc.handle, bytes([1, 0]))
                cccd_found = True
                print_success("  Notifications enabled!")

        if not cccd_found:
            print_warning("CCCD not found, notifications may not work")

        # Wait for notifications
        print_info("\nWaiting for notifications (20 seconds)...")
        print_info("Press Ctrl+C to stop early")

        start = time.time()
        notification_count = 0

        try:
            while (time.time() - start) < 20:
                if p.waitForNotifications(1.0):
                    notification_count += 1
                    continue

                # Send periodic command if write handle exists
                if write_handle and (time.time() - start) > 1:
                    elapsed = int(time.time() - start)
                    if elapsed % 2 == 0:  # Every 2 seconds
                        print_info("Sending command to write handle...")
                        try:
                            p.writeCharacteristic(write_handle, bytes([0xff, 0xaa, 0x27, 0x3A, 0x00]))
                        except:
                            print_warning("Write failed")

        except KeyboardInterrupt:
            print_info("\nStopped by user")

        p.disconnect()

        if notification_count > 0:
            print_success("\nReceived %d notifications - Device is working!" % notification_count)
            return True
        else:
            print_warning("\nNo notifications received")
            return False

    except Exception as e:
        print_error("Failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='Debug BLE connection to WT901BLE67')
    parser.add_argument('-n', '--name', type=str, default='WT901BLE67',
                        help='Device name to search for')
    parser.add_argument('-m', '--mac', type=str, default='',
                        help='MAC address (skip scan if provided)')
    parser.add_argument('-t', '--type', type=str, default='',
                        help='Address type: public or random (auto-detect if not provided)')
    parser.add_argument('--skip-scan', action='store_true',
                        help='Skip scanning (requires --mac and --type)')

    args = parser.parse_args()

    print_header("BLE CONNECTION DEBUG TOOL")
    print_info("Device Name: %s" % args.name)
    if args.mac:
        print_info("Target MAC: %s" % args.mac)

    # Step 1: Scan (unless skipped)
    target_device = None
    if not args.skip_scan and not args.mac:
        target_device = test_scan(args.name, timeout=5)
        if not target_device:
            print_error("\nCannot proceed without device. Exiting.")
            return

        mac = target_device.addr
        addr_type = target_device.addrType
    else:
        if not args.mac:
            print_error("Must provide --mac when using --skip-scan")
            return
        mac = args.mac
        addr_type = args.type if args.type else btle.ADDR_TYPE_PUBLIC
        print_info("Using provided MAC: %s" % mac)
        print_info("Using address type: %s" % addr_type)

    # Step 2: Try public address type
    if addr_type == btle.ADDR_TYPE_PUBLIC or not args.skip_scan:
        public_result = test_connect_public(mac)
    else:
        public_result = False
        print_warning("Skipping public address type test")

    # Step 3: Try random address type
    if addr_type == btle.ADDR_TYPE_RANDOM or not args.skip_scan:
        random_result = test_connect_random(mac)
    else:
        random_result = False
        print_warning("Skipping random address type test")

    # Determine which address type worked
    if random_result:
        working_addr_type = btle.ADDR_TYPE_RANDOM
        print_success("\n>>> RANDOM address type works! <<<")
    elif public_result:
        working_addr_type = btle.ADDR_TYPE_PUBLIC
        print_success("\n>>> PUBLIC address type works! <<<")
    else:
        print_error("\n>>> Neither address type works! <<<")
        print_error("Possible issues:")
        print_error("  1. Device is paired/connected to another host")
        print_error("  2. Bluetooth interference")
        print_error("  3. Device is out of range or powered off")
        print_error("  4. Device requires pairing first")
        return

    # Step 4: Full connection with service discovery
    read_handle, write_handle = test_full_connection(mac, working_addr_type)

    # Step 5: Test notifications
    if read_handle:
        test_notifications(mac, working_addr_type, read_handle, write_handle)
    else:
        print_warning("\nCannot test notifications without read handle")

    # Summary
    print_header("SUMMARY")
    print_info("Device MAC: %s" % mac)
    print_info("Working Address Type: %s" % working_addr_type)
    if read_handle:
        print_info("Read/Notify Handle: 0x%02X" % read_handle)
    if write_handle:
        print_info("Write Handle: 0x%02X" % write_handle)

    print("\n" + ANSI_GREEN + "Fix for wit_ble.py:" + ANSI_OFF)
    print("  Line ~121: connectaddrtype = d.addrType")
    print("  Line ~129: p.connect(connectaddr, connectaddrtype)")
    print()

if __name__ == "__main__":
    main()
