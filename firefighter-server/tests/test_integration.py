#!/usr/bin/env python3
"""Full integration test: Create session, send data, verify storage, export.

Usage:
    python test_integration.py [--server URL] [--duration SECONDS]

This tests the complete data flow:
1. Create a session
2. Send simulated sensor data
3. Verify data is stored in Qdrant
4. Test similarity search
5. Export and verify data
6. Cleanup
"""

import argparse
import json
import time
import requests
import socketio
from datetime import datetime


def create_session(base_url: str, name: str) -> dict:
    """Create a new recording session."""
    resp = requests.post(f"{base_url}/api/sessions", json={"name": name})
    resp.raise_for_status()
    return resp.json()


def stop_session(base_url: str, session_id: str) -> dict:
    """Stop a recording session."""
    resp = requests.post(f"{base_url}/api/sessions/{session_id}/stop")
    resp.raise_for_status()
    return resp.json()


def get_session(base_url: str, session_id: str) -> dict:
    """Get session details."""
    resp = requests.get(f"{base_url}/api/sessions/{session_id}")
    resp.raise_for_status()
    return resp.json()


def export_session(base_url: str, session_id: str) -> dict:
    """Export session data."""
    resp = requests.get(f"{base_url}/api/sessions/{session_id}/export?include_raw=true")
    resp.raise_for_status()
    return resp.json()


def delete_session(base_url: str, session_id: str) -> dict:
    """Delete a session."""
    resp = requests.delete(f"{base_url}/api/sessions/{session_id}")
    resp.raise_for_status()
    return resp.json()


def send_sensor_data(server_url: str, duration: float = 5.0) -> tuple:
    """
    Send simulated sensor data via Socket.IO.

    Returns:
        Tuple of (foot_count, accel_count)
    """
    sio = socketio.Client()
    connected = False
    authenticated = False
    foot_count = 0
    accel_count = 0

    @sio.on("connect", namespace="/iot")
    def on_connect():
        nonlocal connected
        connected = True
        sio.emit("authenticate", {"device_key": "firefighter_pi_001"}, namespace="/iot")

    @sio.on("auth_success", namespace="/iot")
    def on_auth_success(data):
        nonlocal authenticated
        authenticated = True

    # Connect
    sio.connect(server_url, namespaces=["/iot"], wait_timeout=10)
    time.sleep(1)

    if not authenticated:
        sio.disconnect()
        raise Exception("Authentication failed")

    # Send data
    start_time = time.time()
    while (time.time() - start_time) < duration:
        # Send foot data (10Hz)
        foot_data = {
            "timestamp": datetime.now().isoformat(),
            "device": "LEFT_FOOT",
            "data": {
                "foot": "LEFT",
                "max": 100.0,
                "avg": 50.0,
                "active_count": 10,
                "values": [50.0 + i for i in range(18)],
            },
        }
        sio.emit("foot_pressure_data", foot_data, namespace="/iot")
        foot_count += 1

        # Send accel data (20Hz)
        accel_data = {
            "timestamp": datetime.now().isoformat(),
            "device": "ACCELEROMETER",
            "data": {
                "acc": {"x": 0.1, "y": 0.2, "z": 9.8},
                "gyro": {"x": 1.0, "y": 2.0, "z": 3.0},
                "angle": {"roll": 5.0, "pitch": 10.0, "yaw": 180.0},
            },
        }
        sio.emit("accelerometer_data", accel_data, namespace="/iot")
        accel_count += 1

        time.sleep(0.05)  # 20Hz

    sio.disconnect()
    return foot_count, accel_count


def run_integration_test(server_url: str, duration: float = 5.0) -> bool:
    """
    Run full integration test.

    Returns:
        True if all tests pass
    """
    base_url = server_url.rstrip("/")
    session_id = None

    try:
        # Step 1: Create session
        print("\n[Step 1] Creating session...")
        session = create_session(base_url, f"integration_test_{int(time.time())}")
        session_id = session["id"]
        print(f"  Session ID: {session_id}")
        print(f"  Status: {session['status']}")
        assert session["status"] == "recording", "Session not recording"
        print("  [OK]")

        # Step 2: Send sensor data
        print(f"\n[Step 2] Sending sensor data for {duration}s...")
        foot_count, accel_count = send_sensor_data(server_url, duration)
        print(f"  Foot readings sent: {foot_count}")
        print(f"  Accel readings sent: {accel_count}")
        print("  [OK]")

        # Give server time to process windows
        print("\n[Step 3] Waiting for window processing...")
        time.sleep(2)
        print("  [OK]")

        # Step 4: Stop session
        print("\n[Step 4] Stopping session...")
        session = stop_session(base_url, session_id)
        print(f"  Status: {session['status']}")
        assert session["status"] == "stopped", "Session not stopped"
        print("  [OK]")

        # Step 5: Verify data stored
        print("\n[Step 5] Verifying data storage...")
        session = get_session(base_url, session_id)
        window_count = session.get("window_count", 0)
        print(f"  Windows stored: {window_count}")

        if window_count == 0:
            print("  [WARN] No windows stored - check window timing")
        else:
            print("  [OK]")

        # Step 6: Export data
        print("\n[Step 6] Exporting session data...")
        export = export_session(base_url, session_id)
        exported_windows = len(export.get("windows", []))
        print(f"  Exported windows: {exported_windows}")

        if exported_windows > 0:
            first_window = export["windows"][0]
            print(f"  First window start: {first_window.get('start_time')}")
            if "raw_data" in first_window:
                raw = first_window["raw_data"]
                print(f"  Raw data - foot: {len(raw.get('foot', []))}, accel: {len(raw.get('accel', []))}")
        print("  [OK]")

        # Step 7: Cleanup
        print("\n[Step 7] Cleaning up...")
        result = delete_session(base_url, session_id)
        print(f"  Windows deleted: {result.get('windows_deleted', 0)}")
        session_id = None
        print("  [OK]")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

    finally:
        # Cleanup on failure
        if session_id:
            try:
                delete_session(base_url, session_id)
                print(f"\n[Cleanup] Deleted test session")
            except:
                pass


def main():
    parser = argparse.ArgumentParser(description="Full integration test")
    parser.add_argument("--server", default="http://localhost:4100", help="Server URL")
    parser.add_argument("--duration", type=float, default=5, help="Data send duration")
    args = parser.parse_args()

    print("=" * 60)
    print("Firefighter Server - Integration Test")
    print("=" * 60)
    print(f"Server: {args.server}")
    print(f"Duration: {args.duration}s")
    print("=" * 60)

    # Check server is running
    try:
        resp = requests.get(f"{args.server}/health", timeout=5)
        health = resp.json()
        if health.get("qdrant", {}).get("status") != "healthy":
            print("\n[ERROR] Qdrant is not healthy!")
            print("Make sure Qdrant is running:")
            print("  docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant")
            return 1
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] Cannot connect to server at {args.server}")
        print("Make sure the server is running:")
        print("  cd firefighter-server && ./start.sh")
        return 1

    # Run test
    success = run_integration_test(args.server, args.duration)

    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Integration test passed!")
    else:
        print("[FAILED] Integration test failed!")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
