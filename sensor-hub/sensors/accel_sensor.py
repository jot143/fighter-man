"""Accelerometer IMU sensor BLE interface using bleak (WT901BLE67)."""

import asyncio
import json
from datetime import datetime
from bleak import BleakClient, BleakScanner
from .parsers import parse_accel_data


# BLE UUIDs for WT901BLE67 accelerometer (two possible UUID patterns)
NOTIFY_UUID_1 = "0000ffe4-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID_2 = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_UUID_1 = "0000ffe9-0000-1000-8000-00805f9b34fb"
WRITE_UUID_2 = "0000fff2-0000-1000-8000-00805f9b34fb"


class AccelSensor:
    """BLE interface for WT901BLE67 IMU accelerometer sensor."""

    def __init__(self, mac_address, device_name="ACCELEROMETER", data_callback=None, throttle=5):
        """
        Initialize accelerometer sensor.

        Args:
            mac_address: BLE MAC address
            device_name: Identifier (default: 'ACCELEROMETER')
            data_callback: Optional async function to call with parsed data
            throttle: Process every Nth packet (default: 5, reduces 100Hz -> 20Hz)
        """
        self.mac = mac_address
        self.name = device_name
        self.data_callback = data_callback
        self.client = None
        self.running = False
        self.notify_uuid = None
        self.write_uuid = None
        self.packet_buffer = bytearray()
        self.throttle = throttle
        self.packet_count = 0

    def _notification_handler(self, sender, raw_data):
        """Handle incoming BLE notifications (binary 20-byte packets with throttling)."""
        try:
            # Accumulate data
            self.packet_buffer.extend(raw_data)

            # Process all complete 20-byte packets
            while len(self.packet_buffer) >= 20:
                packet = bytes(self.packet_buffer[:20])
                self.packet_buffer = self.packet_buffer[20:]

                # Throttle: only process every Nth packet
                self.packet_count += 1
                if self.packet_count % self.throttle != 0:
                    continue

                result = parse_accel_data(packet)
                if result:
                    output = {
                        'timestamp': datetime.now().isoformat(),
                        'device': self.name,
                        'data': result
                    }

                    # Call callback if provided
                    if self.data_callback:
                        asyncio.create_task(self.data_callback(output))
                    else:
                        print(json.dumps(output))

        except Exception as e:
            print(f"[{self.name}] Notification error: {e}")

    async def _discover_uuids(self):
        """Discover which UUID pattern this device uses."""
        try:
            # Use services property instead of deprecated get_services()
            services = self.client.services

            for service in services:
                for char in service.characteristics:
                    uuid_str = str(char.uuid).lower()

                    # Check for notify UUID
                    if 'ffe4' in uuid_str or 'fff1' in uuid_str:
                        if 'read' in char.properties or 'notify' in char.properties:
                            self.notify_uuid = char.uuid
                            print(f"[{self.name}] Found notify UUID: {char.uuid}")

                    # Check for write UUID
                    if 'ffe9' in uuid_str or 'fff2' in uuid_str:
                        if 'write' in char.properties:
                            self.write_uuid = char.uuid
                            print(f"[{self.name}] Found write UUID: {char.uuid}")

            if not self.notify_uuid:
                print(f"[{self.name}] Warning: Notify UUID not found, trying default")
                self.notify_uuid = NOTIFY_UUID_1

            return bool(self.notify_uuid)

        except Exception as e:
            print(f"[{self.name}] UUID discovery error: {e}")
            # Fallback to default UUIDs
            self.notify_uuid = NOTIFY_UUID_1
            self.write_uuid = WRITE_UUID_1
            return True

    async def connect(self, max_retries=3):
        """
        Establish BLE connection with device scanning and retries.

        Args:
            max_retries: Maximum number of connection attempts (default: 3)

        Returns:
            bool: True if connected successfully, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[{self.name}] Scanning for device {self.mac} (attempt {attempt}/{max_retries})...")

                # Scan for device with timeout
                device = await BleakScanner.find_device_by_address(
                    self.mac,
                    timeout=10.0
                )

                if not device:
                    print(f"[{self.name}] Device not found during scan")
                    if attempt < max_retries:
                        print(f"[{self.name}] Retrying in 3 seconds...")
                        await asyncio.sleep(3)
                        continue
                    else:
                        print(f"[{self.name}] Failed after {max_retries} attempts")
                        return False

                print(f"[{self.name}] Device found, connecting...")

                # Connect to device
                self.client = BleakClient(device, timeout=15.0)
                await self.client.connect()
                print(f"[{self.name}] Connected to {self.mac}")

                # Discover correct UUIDs for this device
                await self._discover_uuids()

                return True

            except Exception as e:
                print(f"[{self.name}] Connection attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    print(f"[{self.name}] Retrying in 3 seconds...")
                    await asyncio.sleep(3)
                else:
                    print(f"[{self.name}] All connection attempts failed")
                    return False

        return False

    async def start_monitoring(self):
        """Start receiving IMU data."""
        if not self.client or not self.client.is_connected:
            print(f"[{self.name}] Not connected")
            return

        try:
            # Enable notifications
            await self.client.start_notify(self.notify_uuid, self._notification_handler)

            print(f"[{self.name}] Monitoring started")
            self.running = True

            # Start periodic keep-alive task
            asyncio.create_task(self._keep_alive())

        except Exception as e:
            print(f"[{self.name}] Start monitoring failed: {e}")

    async def _keep_alive(self):
        """Send periodic keep-alive commands (device-specific protocol)."""
        keep_alive_cmd = bytes([0xff, 0xaa, 0x27, 0x3A, 0x00])

        while self.running and self.client and self.client.is_connected:
            try:
                if self.write_uuid:
                    await self.client.write_gatt_char(self.write_uuid, keep_alive_cmd, response=False)
                await asyncio.sleep(1.0)
            except Exception:
                break

    async def stop_monitoring(self):
        """Stop receiving data and disconnect."""
        if not self.client or not self.client.is_connected:
            return

        try:
            self.running = False

            # Stop notifications
            if self.notify_uuid:
                await self.client.stop_notify(self.notify_uuid)

            # Disconnect
            await self.client.disconnect()

            print(f"[{self.name}] Stopped and disconnected")

        except Exception as e:
            print(f"[{self.name}] Stop error: {e}")

    async def monitor_loop(self, duration=None):
        """
        Main monitoring loop.

        Args:
            duration: Optional duration in seconds (None = run indefinitely)
        """
        if not await self.connect():
            return

        await self.start_monitoring()

        try:
            start_time = asyncio.get_event_loop().time()

            while self.running and self.client.is_connected:
                if duration and (asyncio.get_event_loop().time() - start_time) >= duration:
                    break
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass
        finally:
            await self.stop_monitoring()
