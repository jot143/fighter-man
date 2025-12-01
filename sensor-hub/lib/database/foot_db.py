"""SQLite database for foot pressure sensor readings.

Stores foot pressure data with SQLite backup for network failures.
"""

import json
import sqlite3
from typing import Any, Dict

from .base import DatabaseBase


class FootDatabase(DatabaseBase):
    """SQLite storage for foot pressure sensor data."""

    @property
    def table_name(self) -> str:
        return "foot_readings"

    def initialize_table(self, conn: sqlite3.Connection) -> None:
        """Create the foot_readings table."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS foot_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device TEXT NOT NULL,
                foot TEXT NOT NULL,
                max_pressure REAL,
                avg_pressure REAL,
                active_count INTEGER,
                values_json TEXT,
                sent INTEGER DEFAULT 0
            )
        """)
        # Index for efficient batch fetching
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_foot_sent
            ON foot_readings(sent, id)
        """)

    def save_record(self, record: Dict[str, Any]) -> bool:
        """
        Save a foot sensor reading to the database.

        Args:
            record: Sensor data in format:
                {
                    'timestamp': ISO datetime string,
                    'device': 'LEFT_FOOT' or 'RIGHT_FOOT',
                    'data': {
                        'foot': 'LEFT' or 'RIGHT',
                        'max': float,
                        'avg': float,
                        'active_count': int,
                        'values': list of 18 floats
                    }
                }

        Returns:
            True if save successful
        """
        try:
            data = record.get("data", {})

            with self._lock:
                conn = self._get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO foot_readings
                        (timestamp, device, foot, max_pressure, avg_pressure, active_count, values_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.get("timestamp"),
                            record.get("device"),
                            data.get("foot"),
                            data.get("max"),
                            data.get("avg"),
                            data.get("active_count"),
                            json.dumps(data.get("values", [])),
                        ),
                    )
                    conn.commit()
                    return True
                finally:
                    conn.close()

        except Exception as e:
            print(f"[FootDB] Error saving record: {e}")
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
                "foot": row["foot"],
                "max": row["max_pressure"],
                "avg": row["avg_pressure"],
                "active_count": row["active_count"],
                "values": json.loads(row["values_json"]) if row["values_json"] else [],
            },
        }
