"""SQLite database for accelerometer sensor readings.

Stores IMU data with SQLite backup for network failures.
"""

import sqlite3
from typing import Any, Dict

from .base import DatabaseBase


class AccelDatabase(DatabaseBase):
    """SQLite storage for accelerometer (IMU) sensor data."""

    @property
    def table_name(self) -> str:
        return "accel_readings"

    def initialize_table(self, conn: sqlite3.Connection) -> None:
        """Create the accel_readings table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accel_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device TEXT NOT NULL,
                acc_x REAL,
                acc_y REAL,
                acc_z REAL,
                gyro_x REAL,
                gyro_y REAL,
                gyro_z REAL,
                roll REAL,
                pitch REAL,
                yaw REAL,
                sent INTEGER DEFAULT 0
            )
        """)
        # Index for efficient batch fetching
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_accel_sent
            ON accel_readings(sent, id)
        """)

    def save_record(self, record: Dict[str, Any]) -> bool:
        """
        Save an accelerometer reading to the database.

        Args:
            record: Sensor data in format:
                {
                    'timestamp': ISO datetime string,
                    'device': 'ACCELEROMETER',
                    'data': {
                        'acc': {'x': float, 'y': float, 'z': float},
                        'gyro': {'x': float, 'y': float, 'z': float},
                        'angle': {'roll': float, 'pitch': float, 'yaw': float}
                    }
                }

        Returns:
            True if save successful
        """
        try:
            data = record.get("data", {})
            acc = data.get("acc", {})
            gyro = data.get("gyro", {})
            angle = data.get("angle", {})

            with self._lock:
                conn = self._get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO accel_readings
                        (timestamp, device, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, roll, pitch, yaw)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.get("timestamp"),
                            record.get("device"),
                            acc.get("x"),
                            acc.get("y"),
                            acc.get("z"),
                            gyro.get("x"),
                            gyro.get("y"),
                            gyro.get("z"),
                            angle.get("roll"),
                            angle.get("pitch"),
                            angle.get("yaw"),
                        ),
                    )
                    conn.commit()
                    return True
                finally:
                    conn.close()

        except Exception as e:
            print(f"[AccelDB] Error saving record: {e}")
            return False

    def transform_for_send(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Transform a database row to Socket.IO transmission format.

        Args:
            row: Database row

        Returns:
            Data dictionary for Socket.IO event
        """
        return {
            "timestamp": row["timestamp"],
            "device": row["device"],
            "data": {
                "acc": {
                    "x": row["acc_x"],
                    "y": row["acc_y"],
                    "z": row["acc_z"],
                },
                "gyro": {
                    "x": row["gyro_x"],
                    "y": row["gyro_y"],
                    "z": row["gyro_z"],
                },
                "angle": {
                    "roll": row["roll"],
                    "pitch": row["pitch"],
                    "yaw": row["yaw"],
                },
            },
        }
