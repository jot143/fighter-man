#!/usr/bin/env python3
"""
Realistic Activity Simulation Client

Generates realistic sensor data for validated activities based on archived script thresholds.
Sends data to firefighter-server via Socket.IO for frontend testing.

Usage:
    python realistic_activity_client.py --activity Standing --duration 30
    python realistic_activity_client.py --activity Sitting --no-auto-session
"""

import argparse
import time
import math
import random
from datetime import datetime
from typing import Dict

import socketio

# Activity choices (validated from archived script)
ACTIVITIES = ["Standing", "Sitting", "Bent_Forward", "Lying_Down", "Jumping"]


class ActivityGenerator:
    """Generate realistic sensor data for validated activities."""

    def __init__(self, activity: str):
        self.activity = activity
        self.start_time = time.time()

    def generate_foot_data(self, foot: str = "LEFT") -> dict:
        """Generate realistic foot pressure data for the selected activity."""
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - self.start_time

        # Generate 18 sensor values based on activity
        if self.activity == "Standing":
            # Standing: Full weight distribution, moderate pressure
            base_pressure = random.uniform(100, 200)
            values = [
                round(base_pressure + random.uniform(-20, 20), 1)
                for _ in range(18)
            ]

        elif self.activity == "Sitting":
            # Sitting: Minimal foot pressure, weight on seat
            base_pressure = random.uniform(0, 80)
            values = [
                round(max(0, base_pressure + random.uniform(-10, 10)), 1)
                for _ in range(18)
            ]
            # Some sensors may be near zero
            for i in range(0, 18, 3):
                values[i] = round(random.uniform(0, 30), 1)

        elif self.activity == "Bent_Forward":
            # Bent forward: Similar to standing but may shift weight
            base_pressure = random.uniform(120, 220)
            values = [
                round(base_pressure + random.uniform(-30, 30), 1)
                for _ in range(18)
            ]
            # More weight on toes (first half of sensors)
            for i in range(9):
                values[i] = round(values[i] * 1.2, 1)

        elif self.activity == "Lying_Down":
            # Lying down: Very minimal foot pressure
            values = [
                round(random.uniform(0, 50), 1)
                for _ in range(18)
            ]

        elif self.activity == "Jumping":
            # Jumping: Oscillating between high pressure (landing) and low (airborne)
            # Simulate jump cycle: ~1 jump per second
            jump_phase = math.sin(elapsed * 2 * math.pi)  # -1 to 1

            if jump_phase > 0.5:
                # Landing phase - high pressure
                base_pressure = random.uniform(400, 800)
            elif jump_phase < -0.5:
                # Airborne - very low pressure
                base_pressure = random.uniform(0, 50)
            else:
                # Transition phases
                base_pressure = random.uniform(100, 300)

            values = [
                round(max(0, base_pressure + random.uniform(-50, 50)), 1)
                for _ in range(18)
            ]

        return {
            "timestamp": timestamp,
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
        """Generate realistic accelerometer data for the selected activity.

        IMPORTANT: Y-axis is VERTICAL (not Z-axis) based on archived script.
        When standing upright: acc.y ≈ 1.0g
        """
        timestamp = datetime.now().isoformat()
        elapsed = time.time() - self.start_time

        if self.activity == "Standing":
            # Standing: Y-axis shows gravity, minimal X/Z, low pitch/roll
            acc_x = random.uniform(-0.3, 0.3)
            acc_y = random.uniform(0.9, 1.1)  # Gravity on Y-axis
            acc_z = random.uniform(-0.3, 0.3)

            gyro_x = random.uniform(-30, 30)
            gyro_y = random.uniform(-30, 30)
            gyro_z = random.uniform(-30, 30)

            pitch = random.uniform(-10, 10)
            roll = random.uniform(-10, 10)
            yaw = random.uniform(0, 360)

        elif self.activity == "Sitting":
            # Sitting: Lower Y-axis (weight on seat), moderate pitch
            acc_x = random.uniform(-1.0, 1.0)
            acc_y = random.uniform(0.6, 0.85)  # Lower than standing
            acc_z = random.uniform(-1.0, 1.0)

            gyro_x = random.uniform(-15, 15)
            gyro_y = random.uniform(-15, 15)
            gyro_z = random.uniform(-15, 15)

            pitch = random.uniform(20, 40)  # Moderate forward pitch
            roll = random.uniform(-25, 25)
            yaw = random.uniform(0, 360)

        elif self.activity == "Bent_Forward":
            # Bent forward: Low Y-axis, high pitch angle
            acc_x = random.uniform(-0.8, 0.8)
            acc_y = random.uniform(0.2, 0.65)  # Low Y from forward bend
            acc_z = random.uniform(-0.8, 0.8)

            gyro_x = random.uniform(-40, 40)
            gyro_y = random.uniform(-40, 40)
            gyro_z = random.uniform(-40, 40)

            pitch = random.uniform(40, 80)  # High forward pitch
            roll = random.uniform(-25, 25)
            yaw = random.uniform(0, 360)

        elif self.activity == "Lying_Down":
            # Lying down: Y-axis near 0, gravity on X or Z
            acc_x = random.choice([random.uniform(0.85, 1.05), random.uniform(-1.05, -0.85)])
            acc_y = random.uniform(-0.25, 0.25)  # Near zero when horizontal
            acc_z = random.uniform(-0.3, 0.3)

            gyro_x = random.uniform(-20, 20)
            gyro_y = random.uniform(-20, 20)
            gyro_z = random.uniform(-20, 20)

            pitch = random.choice([random.uniform(-95, -75), random.uniform(75, 95)])
            roll = random.choice([random.uniform(-95, -75), random.uniform(75, 95)])
            yaw = random.uniform(0, 360)

        elif self.activity == "Jumping":
            # Jumping: Rapid Y-axis oscillation, high gyro activity
            jump_phase = math.sin(elapsed * 2 * math.pi)  # Jump cycle

            if jump_phase > 0.6:
                # Push-off / landing - high Y acceleration
                acc_y = random.uniform(1.25, 1.45)
            elif jump_phase < -0.4:
                # Airborne - low Y acceleration
                acc_y = random.uniform(0.4, 0.65)
            else:
                # Transition
                acc_y = random.uniform(0.8, 1.2)

            acc_x = random.uniform(-1.5, 1.5)
            acc_z = random.uniform(-1.5, 1.5)

            gyro_x = random.uniform(-120, 120)
            gyro_y = random.uniform(-120, 120)
            gyro_z = random.uniform(-120, 120)

            pitch = random.uniform(-20, 20)
            roll = random.uniform(-20, 20)
            yaw = random.uniform(0, 360)

        return {
            "timestamp": timestamp,
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
                    "pitch": round(pitch, 2),
                    "roll": round(roll, 2),
                    "yaw": round(yaw, 2),
                },
            },
        }


class SimulatedPi:
    """Simulates a Raspberry Pi sending sensor data."""

    def __init__(self, server_url: str, device_key: str, activity: str):
        self.server_url = server_url
        self.device_key = device_key
        self.activity = activity
        self.sio = socketio.Client()
        self.connected = False
        self.authenticated = False
        self.generator = ActivityGenerator(activity)

        # Setup event handlers
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

    def send_foot_data(self, foot: str = "LEFT"):
        """Send foot pressure data."""
        data = self.generator.generate_foot_data(foot)
        self.sio.emit("foot_pressure_data", data, namespace="/iot")
        return data

    def send_accel_data(self):
        """Send accelerometer data."""
        data = self.generator.generate_accel_data()
        self.sio.emit("accelerometer_data", data, namespace="/iot")
        return data

    def run_simulation(self, duration: float = None, foot_hz: float = 2, accel_hz: float = 5):
        """
        Run realistic sensor simulation for the selected activity.

        Args:
            duration: Duration in seconds (None for continuous)
            foot_hz: Foot sensor frequency (default: 2Hz)
            accel_hz: Accelerometer frequency (default: 5Hz)
        """
        duration_str = f"{duration}s" if duration else "continuous (Ctrl+C to stop)"
        print(f"\n[Simulation] Starting {duration_str} simulation")
        print(f"[Simulation] Activity: {self.activity}")
        print(f"[Simulation] Foot: {foot_hz}Hz, Accel: {accel_hz}Hz")
        print(f"[Simulation] Source: Validated thresholds from archived/accelerator/blue/analyze.py\n")

        foot_interval = 1.0 / foot_hz
        accel_interval = 1.0 / accel_hz

        start_time = time.time()
        last_foot_time = 0
        last_accel_time = 0
        foot_count = 0
        accel_count = 0

        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_time

                # Check duration
                if duration and elapsed >= duration:
                    break

                # Send foot data for both feet
                if (current_time - last_foot_time) >= foot_interval:
                    self.send_foot_data("LEFT")
                    foot_count += 1
                    last_foot_time = current_time

                # Send accel data
                if (current_time - last_accel_time) >= accel_interval:
                    self.send_accel_data()
                    accel_count += 1
                    last_accel_time = current_time

                # Progress update every 5 seconds
                if int(elapsed) % 5 == 0 and elapsed > 0 and elapsed < elapsed + 0.1:
                    print(f"[Progress] {int(elapsed)}s elapsed | Foot: {foot_count} | Accel: {accel_count} | Activity: {self.activity}")

                # Small sleep to prevent CPU spinning
                time.sleep(0.001)

        except KeyboardInterrupt:
            print("\n[Simulation] Interrupted")

        elapsed = time.time() - start_time
        print(f"\n[Simulation] Complete!")
        print(f"[Simulation] Duration: {elapsed:.1f}s")
        print(f"[Simulation] Foot readings sent: {foot_count}")
        print(f"[Simulation] Accel readings sent: {accel_count}")
        print(f"[Simulation] Activity simulated: {self.activity}")


def main():
    parser = argparse.ArgumentParser(
        description='Simulated Pi client sending realistic activity sensor data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send realistic sitting data for 30 seconds
  python realistic_activity_client.py --activity Sitting --duration 30

  # Send standing data continuously (Ctrl+C to stop)
  python realistic_activity_client.py --activity Standing

  # Send jumping data without auto session management
  python realistic_activity_client.py --activity Jumping --no-auto-session

Validated Activities:
  - Standing     : Upright stable posture (acc.y ≈ 1.0g)
  - Sitting      : Seated with moderate pitch (acc.y ≈ 0.6-0.85g)
  - Bent_Forward : Forward bend (acc.y < 0.7g, pitch > 30°)
  - Lying_Down   : Horizontal orientation (acc.y ≈ 0g)
  - Jumping      : Rapid Y-axis spikes (acc.y: 0.4-1.45g oscillating)

Note: Thresholds based on archived/accelerator/blue/analyze.py
      Y-axis is VERTICAL when standing (not Z-axis)
        """
    )

    parser.add_argument(
        '--activity',
        type=str,
        required=True,
        choices=ACTIVITIES,
        help='Activity to simulate (validated activities only)'
    )

    parser.add_argument(
        '--server',
        type=str,
        default='http://localhost:4100',
        help='Server URL (default: http://localhost:4100)'
    )

    parser.add_argument(
        '--device-key',
        type=str,
        default='firefighter_pi_001',
        help='Device key for this simulated Pi (default: firefighter_pi_001)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='Duration in seconds (default: continuous until Ctrl+C)'
    )

    parser.add_argument(
        '--no-auto-session',
        action='store_true',
        help='Disable automatic session start/end (send data only)'
    )

    parser.add_argument(
        '--foot-hz',
        type=float,
        default=2,
        help='Foot sensor frequency in Hz (default: 2)'
    )

    parser.add_argument(
        '--accel-hz',
        type=float,
        default=5,
        help='Accelerometer frequency in Hz (default: 5)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("  Realistic Activity Simulation Client")
    print("=" * 70)
    print(f"  Activity: {args.activity}")
    print(f"  Server: {args.server}")
    print(f"  Device Key: {args.device_key}")
    print("=" * 70)

    # Create simulated Pi
    sim = SimulatedPi(
        server_url=args.server,
        device_key=args.device_key,
        activity=args.activity
    )

    if not sim.connect():
        print("[Error] Failed to connect/authenticate")
        return 1

    try:
        sim.run_simulation(
            duration=args.duration,
            foot_hz=args.foot_hz,
            accel_hz=args.accel_hz
        )
    finally:
        sim.disconnect()

    print("\n[Done] Test client finished")
    return 0


if __name__ == '__main__':
    exit(main())
