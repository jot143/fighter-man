#!/usr/bin/env python3
"""Test client that simulates Raspberry Pi sending sensor data.

Usage:
    python test_client.py [--server URL] [--duration SECONDS]

This simulates a Pi connected to sensors, sending data to the server.
"""

import argparse
import random
import time
import math
from datetime import datetime

import socketio


class SimulatedPi:
    """Simulates a Raspberry Pi sending sensor data."""

    def __init__(self, server_url: str, device_key: str = "test_pi_001"):
        self.server_url = server_url
        self.device_key = device_key
        self.sio = socketio.Client()
        self.connected = False
        self.authenticated = False

        self._setup_handlers()

    def _setup_handlers(self):
        """Set up Socket.IO event handlers."""

        @self.sio.on("connect", namespace="/iot")
        def on_connect():
            print(f"[Client] Connected to {self.server_url}")
            self.connected = True
            # Authenticate
            self.sio.emit("authenticate", {"device_key": self.device_key}, namespace="/iot")

        @self.sio.on("disconnect", namespace="/iot")
        def on_disconnect():
            print("[Client] Disconnected")
            self.connected = False
            self.authenticated = False

        @self.sio.on("auth_success", namespace="/iot")
        def on_auth_success(data):
            print(f"[Client] Authenticated: {data}")
            self.authenticated = True

        @self.sio.on("auth_error", namespace="/iot")
        def on_auth_error(data):
            print(f"[Client] Auth failed: {data}")
            self.authenticated = False

        @self.sio.on("session_started", namespace="/iot")
        def on_session_started(data):
            print(f"[Client] Session started: {data.get('session_id')}")

        @self.sio.on("session_stopped", namespace="/iot")
        def on_session_stopped(data):
            print(f"[Client] Session stopped: {data.get('session_id')}")

    def connect(self) -> bool:
        """Connect to the server."""
        try:
            self.sio.connect(self.server_url, namespaces=["/iot"], wait_timeout=10)
            time.sleep(1)  # Wait for authentication
            return self.authenticated
        except Exception as e:
            print(f"[Client] Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from server."""
        self.sio.disconnect()

    def generate_foot_data(self, foot: str = "LEFT") -> dict:
        """Generate simulated foot pressure data."""
        # Simulate walking pattern
        t = time.time()
        base_pressure = 50 + 30 * math.sin(t * 2)  # Oscillating pressure

        values = []
        for i in range(18):
            # Add variation per sensor
            noise = random.uniform(-10, 10)
            value = max(0, base_pressure + noise + random.uniform(0, 20))
            values.append(round(value, 1))

        return {
            "timestamp": datetime.now().isoformat(),
            "device": f"{foot}_FOOT",
            "data": {
                "foot": foot,
                "max": max(values),
                "avg": sum(values) / len(values),
                "active_count": sum(1 for v in values if v > 10),
                "values": values,
            },
        }

    def generate_accel_data(self) -> dict:
        """Generate simulated accelerometer data."""
        t = time.time()

        # Simulate walking motion
        acc_x = 0.1 * math.sin(t * 4) + random.uniform(-0.05, 0.05)
        acc_y = 0.2 * math.cos(t * 4) + random.uniform(-0.05, 0.05)
        acc_z = 9.8 + 0.3 * math.sin(t * 8) + random.uniform(-0.1, 0.1)

        gyro_x = 5 * math.sin(t * 2) + random.uniform(-1, 1)
        gyro_y = 3 * math.cos(t * 2) + random.uniform(-1, 1)
        gyro_z = random.uniform(-2, 2)

        roll = 5 * math.sin(t) + random.uniform(-1, 1)
        pitch = 3 * math.cos(t * 0.5) + random.uniform(-1, 1)
        yaw = (t * 10) % 360  # Slowly rotating

        return {
            "timestamp": datetime.now().isoformat(),
            "device": "ACCELEROMETER",
            "data": {
                "acc": {
                    "x": round(acc_x, 3),
                    "y": round(acc_y, 3),
                    "z": round(acc_z, 3),
                },
                "gyro": {
                    "x": round(gyro_x, 2),
                    "y": round(gyro_y, 2),
                    "z": round(gyro_z, 2),
                },
                "angle": {
                    "roll": round(roll, 2),
                    "pitch": round(pitch, 2),
                    "yaw": round(yaw, 2),
                },
            },
        }

    def send_foot_data(self, foot: str = "LEFT"):
        """Send foot pressure data."""
        data = self.generate_foot_data(foot)
        self.sio.emit("foot_pressure_data", data, namespace="/iot")
        return data

    def send_accel_data(self):
        """Send accelerometer data."""
        data = self.generate_accel_data()
        self.sio.emit("accelerometer_data", data, namespace="/iot")
        return data

    def run_simulation(self, duration: float = 10.0, foot_hz: float = 10, accel_hz: float = 20):
        """
        Run sensor simulation for specified duration.

        Args:
            duration: Duration in seconds
            foot_hz: Foot sensor frequency
            accel_hz: Accelerometer frequency
        """
        print(f"\n[Simulation] Starting {duration}s simulation")
        print(f"[Simulation] Foot: {foot_hz}Hz, Accel: {accel_hz}Hz")

        foot_interval = 1.0 / foot_hz
        accel_interval = 1.0 / accel_hz

        start_time = time.time()
        last_foot_time = 0
        last_accel_time = 0
        foot_count = 0
        accel_count = 0

        try:
            while (time.time() - start_time) < duration:
                current_time = time.time()

                # Send foot data
                if (current_time - last_foot_time) >= foot_interval:
                    self.send_foot_data("LEFT")
                    foot_count += 1
                    last_foot_time = current_time

                # Send accel data
                if (current_time - last_accel_time) >= accel_interval:
                    self.send_accel_data()
                    accel_count += 1
                    last_accel_time = current_time

                # Small sleep to prevent CPU spinning
                time.sleep(0.001)

        except KeyboardInterrupt:
            print("\n[Simulation] Interrupted")

        elapsed = time.time() - start_time
        print(f"\n[Simulation] Complete!")
        print(f"[Simulation] Duration: {elapsed:.1f}s")
        print(f"[Simulation] Foot readings sent: {foot_count}")
        print(f"[Simulation] Accel readings sent: {accel_count}")


def main():
    parser = argparse.ArgumentParser(description="Simulate Pi sending sensor data")
    parser.add_argument("--server", default="http://localhost:4100", help="Server URL")
    parser.add_argument("--duration", type=float, default=10, help="Duration in seconds")
    parser.add_argument("--device-key", default="firefighter_pi_001", help="Device key")
    args = parser.parse_args()

    print("=" * 50)
    print("Simulated Pi Test Client")
    print("=" * 50)
    print(f"Server: {args.server}")
    print(f"Device Key: {args.device_key}")
    print(f"Duration: {args.duration}s")
    print("=" * 50)

    pi = SimulatedPi(args.server, args.device_key)

    if not pi.connect():
        print("[Error] Failed to connect/authenticate")
        return 1

    try:
        pi.run_simulation(duration=args.duration)
    finally:
        pi.disconnect()

    print("\n[Done] Test client finished")
    return 0


if __name__ == "__main__":
    exit(main())
