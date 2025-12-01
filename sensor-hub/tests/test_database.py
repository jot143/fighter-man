#!/usr/bin/env python3
"""Test database operations for sensor-hub."""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.database.foot_db import FootDatabase
from lib.database.accel_db import AccelDatabase


def test_foot_database():
    """Test foot sensor database operations."""
    print("\n" + "=" * 50)
    print("Testing FootDatabase")
    print("=" * 50)

    # Create temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = FootDatabase(db_path)
        print(f"[OK] Created database: {db_path}")

        # Test save
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "device": "LEFT_FOOT",
            "data": {
                "foot": "LEFT",
                "max": 150.5,
                "avg": 75.2,
                "active_count": 12,
                "values": [10.0] * 18,
            },
        }

        result = db.save_record(test_record)
        assert result, "Failed to save record"
        print("[OK] Saved foot record")

        # Test count
        count = db.count_unsent()
        assert count == 1, f"Expected 1 unsent, got {count}"
        print(f"[OK] Count unsent: {count}")

        # Test fetch
        rows = db.fetch_batch(10)
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        print(f"[OK] Fetched batch: {len(rows)} rows")

        # Test transform
        transformed = db.transform_for_send(rows[0])
        assert transformed["device"] == "LEFT_FOOT"
        assert transformed["data"]["foot"] == "LEFT"
        print(f"[OK] Transform works: {transformed['device']}")

        # Test mark sent
        db.mark_sent([rows[0]["id"]])
        count = db.count_unsent()
        assert count == 0, f"Expected 0 unsent after mark, got {count}"
        print("[OK] Mark sent works")

        print("\n[PASS] All FootDatabase tests passed!")

    finally:
        os.unlink(db_path)


def test_accel_database():
    """Test accelerometer database operations."""
    print("\n" + "=" * 50)
    print("Testing AccelDatabase")
    print("=" * 50)

    # Create temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = AccelDatabase(db_path)
        print(f"[OK] Created database: {db_path}")

        # Test save
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "device": "ACCELEROMETER",
            "data": {
                "acc": {"x": 0.1, "y": -0.2, "z": 9.8},
                "gyro": {"x": 1.5, "y": -2.3, "z": 0.5},
                "angle": {"roll": 5.2, "pitch": -3.1, "yaw": 180.0},
            },
        }

        result = db.save_record(test_record)
        assert result, "Failed to save record"
        print("[OK] Saved accel record")

        # Test count
        count = db.count_unsent()
        assert count == 1, f"Expected 1 unsent, got {count}"
        print(f"[OK] Count unsent: {count}")

        # Test fetch
        rows = db.fetch_batch(10)
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        print(f"[OK] Fetched batch: {len(rows)} rows")

        # Test transform
        transformed = db.transform_for_send(rows[0])
        assert transformed["device"] == "ACCELEROMETER"
        assert "acc" in transformed["data"]
        assert "gyro" in transformed["data"]
        assert "angle" in transformed["data"]
        print(f"[OK] Transform works: {transformed['device']}")

        # Test mark sent
        db.mark_sent([rows[0]["id"]])
        count = db.count_unsent()
        assert count == 0, f"Expected 0 unsent after mark, got {count}"
        print("[OK] Mark sent works")

        print("\n[PASS] All AccelDatabase tests passed!")

    finally:
        os.unlink(db_path)


def main():
    """Run all database tests."""
    print("=" * 50)
    print("Sensor-Hub Database Tests")
    print("=" * 50)

    try:
        test_foot_database()
        test_accel_database()

        print("\n" + "=" * 50)
        print("[SUCCESS] All database tests passed!")
        print("=" * 50)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
