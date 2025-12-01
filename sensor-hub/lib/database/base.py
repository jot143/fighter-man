"""Abstract base class for SQLite database operations.

Provides common functionality for storing and retrieving sensor data.
Adapted from ssd-pi-engine/c3/lib/database/base.py
"""

import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class DatabaseBase(ABC):
    """Abstract base class for SQLite sensor data storage."""

    def __init__(self, db_file: str):
        """
        Initialize database connection.

        Args:
            db_file: Path to SQLite database file
        """
        self.db_file = db_file
        self._lock = threading.Lock()

        # Ensure directory exists
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database and create table if needed."""
        with self._lock:
            conn = sqlite3.connect(self.db_file)
            try:
                self.initialize_table(conn)
                conn.commit()
            finally:
                conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    @abstractmethod
    def initialize_table(self, conn: sqlite3.Connection) -> None:
        """
        Create the database table.

        Args:
            conn: SQLite connection
        """
        pass

    @abstractmethod
    def save_record(self, record: Dict[str, Any]) -> bool:
        """
        Save a sensor reading to the database.

        Args:
            record: Sensor data dictionary

        Returns:
            True if save successful
        """
        pass

    @abstractmethod
    def transform_for_send(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Transform a database row to the format needed for Socket.IO transmission.

        Args:
            row: Database row

        Returns:
            Transformed data dictionary
        """
        pass

    def fetch_batch(self, limit: int = 100) -> List[sqlite3.Row]:
        """
        Fetch a batch of unsent records.

        Args:
            limit: Maximum number of records to fetch

        Returns:
            List of database rows
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    f"SELECT * FROM {self.table_name} WHERE sent = 0 ORDER BY id LIMIT ?",
                    (limit,),
                )
                return cursor.fetchall()
            finally:
                conn.close()

    def mark_sent(self, record_ids: List[int]) -> bool:
        """
        Mark records as sent.

        Args:
            record_ids: List of record IDs to mark

        Returns:
            True if successful
        """
        if not record_ids:
            return True

        with self._lock:
            conn = self._get_connection()
            try:
                placeholders = ",".join("?" * len(record_ids))
                conn.execute(
                    f"UPDATE {self.table_name} SET sent = 1 WHERE id IN ({placeholders})",
                    record_ids,
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"[Database] Error marking records as sent: {e}")
                return False
            finally:
                conn.close()

    def delete_sent(self, older_than_hours: int = 24) -> int:
        """
        Delete old sent records.

        Args:
            older_than_hours: Delete records older than this many hours

        Returns:
            Number of records deleted
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE sent = 1
                    AND datetime(timestamp) < datetime('now', ?)
                    """,
                    (f"-{older_than_hours} hours",),
                )
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                print(f"[Database] Error deleting old records: {e}")
                return 0
            finally:
                conn.close()

    def count_unsent(self) -> int:
        """
        Count unsent records.

        Returns:
            Number of unsent records
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(
                    f"SELECT COUNT(*) FROM {self.table_name} WHERE sent = 0"
                )
                return cursor.fetchone()[0]
            finally:
                conn.close()

    def count_total(self) -> int:
        """
        Count total records.

        Returns:
            Total number of records
        """
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                return cursor.fetchone()[0]
            finally:
                conn.close()

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Return the table name for this database."""
        pass
