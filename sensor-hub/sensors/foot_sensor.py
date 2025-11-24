"""Foot pressure sensor BLE interface using bleak."""

import asyncio
import json
from datetime import datetime
from bleak import BleakClient, BleakScanner
from .parsers import parse_foot_data


# BLE UUIDs for foot pressure sensors
SERVICE_UUID = "0000FFF0-0000-1000-8000-00805F9B34FB"
NOTIFY_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"
WRITE_UUID = "0000FFF2-0000-1000-8000-00805F9B34FB"


class FootSensor:
    """BLE interface for foot pressure sensor."""

    def __init__(self, mac_address, device_name, data_callback=None):
        """
        Initialize foot sensor.

        Args:
            mac_address: BLE MAC address
            device_name: Identifier (e.g., 'LEFT_FOOT', 'RIGHT_FOOT')
            data_callback: Optional async function to call with parsed data
        """
        self.mac = mac_address
        self.name = device_name
        self.data_callback = data_callback
        self.client = None
        self.running = False
        self.data_buffer = ""

    def _notification_handler(self, sender, raw_data):
        """Handle incoming BLE notifications (text protocol with newline delimiters)."""
        try:
            chunk = raw_data.decode('utf-8')
            self.data_buffer += chunk

            # Process all complete lines
            while '\n' in self.data_buffer:
                line, self.data_buffer = self.data_buffer.split('\n', 1)
                line = line.strip()

                if line:
                    result = parse_foot_data(line)
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

                # Wait for connection to stabilize
                await asyncio.sleep(0.5)

                print(f"[{self.name}] Connected to {self.mac}")
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
        """Start receiving pressure data."""
        if not self.client or not self.client.is_connected:
            print(f"[{self.name}] Not connected")
            return False

        try:
            # Enable notifications FIRST, before sending begin command
            await self.client.start_notify(NOTIFY_UUID, self._notification_handler)

            # Wait for notification setup to complete
            await asyncio.sleep(0.5)

            # Now send begin command to start data collection
            await self.client.write_gatt_char(WRITE_UUID, b'begin', response=True)

            print(f"[{self.name}] Monitoring started")
            self.running = True
            return True

        except Exception as e:
            print(f"[{self.name}] Start monitoring failed: {e}")
            # Try to clean up
            try:
                await self.client.stop_notify(NOTIFY_UUID)
            except:
                pass
            return False

    async def stop_monitoring(self):
        """Stop receiving data and disconnect."""
        if not self.client or not self.client.is_connected:
            return

        try:
            self.running = False

            # Send end command
            await self.client.write_gatt_char(WRITE_UUID, b'end', response=True)

            # Stop notifications
            await self.client.stop_notify(NOTIFY_UUID)

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
            print(f"[{self.name}] Exiting - connection failed")
            return

        if not await self.start_monitoring():
            print(f"[{self.name}] Exiting - monitoring start failed")
            await self.stop_monitoring()
            return

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
