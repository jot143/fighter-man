"""Base class for data senders with Socket.IO + HTTP fallback.

Implements the "broadcast immediately, retry on failure" pattern from ssd-pi-engine.
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from lib.database.base import DatabaseBase
from lib.socket_client import SocketIOClient
from lib.config import SenderConfig


class DataSenderBase(ABC):
    """Base class for background data transmission with retry logic."""

    def __init__(
        self,
        database: DatabaseBase,
        socket_client: Optional[SocketIOClient],
        config: SenderConfig,
    ):
        """
        Initialize data sender.

        Args:
            database: Database instance for fetching records
            socket_client: Socket.IO client for real-time transmission
            config: Sender configuration
        """
        self.database = database
        self.socket_client = socket_client
        self.config = config

        self._consecutive_failures = 0
        self._last_success_time = time.time()

    @abstractmethod
    def get_socket_event_name(self) -> str:
        """Return the Socket.IO event name for this sender."""
        pass

    def _send_via_socket(self, records: List[Dict[str, Any]]) -> bool:
        """
        Send records via Socket.IO.

        Args:
            records: List of transformed records

        Returns:
            True if all records sent successfully
        """
        if not self.socket_client or not self.socket_client.connected:
            return False

        event_name = self.get_socket_event_name()
        success_count = 0

        for record in records:
            if self.socket_client.emit(event_name, record):
                success_count += 1

        return success_count == len(records)

    def _send_via_http(self, records: List[Dict[str, Any]]) -> bool:
        """
        Send records via HTTP webhook (fallback).

        Args:
            records: List of transformed records

        Returns:
            True if at least one webhook succeeded
        """
        if not self.config.webhook_urls:
            return False

        for url in self.config.webhook_urls:
            try:
                response = requests.post(
                    url,
                    json={"records": records},
                    timeout=10,
                )
                if response.status_code in (200, 201, 202):
                    return True
            except Exception as e:
                print(f"[Sender] HTTP fallback to {url} failed: {e}")

        return False

    def send_batch(self, records: List[Dict[str, Any]]) -> bool:
        """
        Send a batch of records (Socket.IO first, HTTP fallback).

        Args:
            records: List of transformed records

        Returns:
            True if send successful via any method
        """
        if not records:
            return True

        # Try Socket.IO first
        if self._send_via_socket(records):
            return True

        # Fallback to HTTP
        return self._send_via_http(records)

    def _calculate_backoff(self) -> float:
        """
        Calculate exponential backoff delay.

        Returns:
            Delay in seconds
        """
        delay = self.config.retry_backoff_base * (2 ** self._consecutive_failures)
        return min(delay, self.config.max_backoff)

    def process_batch(self) -> bool:
        """
        Fetch, transform, send, and mark records.

        Returns:
            True if batch processed successfully
        """
        # Fetch unsent records
        rows = self.database.fetch_batch(self.config.max_records)

        if not rows:
            return True

        # Transform records
        records = []
        record_ids = []

        for row in rows:
            try:
                transformed = self.database.transform_for_send(row)
                records.append(transformed)
                record_ids.append(row["id"])
            except Exception as e:
                print(f"[Sender] Transform error: {e}")

        if not records:
            return True

        # Send batch
        if self.send_batch(records):
            # Mark as sent
            self.database.mark_sent(record_ids)
            self._consecutive_failures = 0
            self._last_success_time = time.time()
            print(f"[Sender] Sent {len(records)} records via {self.get_socket_event_name()}")
            return True
        else:
            self._consecutive_failures += 1
            print(f"[Sender] Failed to send batch (attempt {self._consecutive_failures})")
            return False

    def run_forever(self) -> None:
        """
        Run the sender loop indefinitely.

        Polls database at configured interval, with exponential backoff on failures.
        """
        print(f"[Sender] Starting {self.get_socket_event_name()} sender")
        print(f"[Sender] Polling interval: {self.config.polling_interval}s")

        while True:
            try:
                success = self.process_batch()

                if success:
                    # Normal polling interval
                    time.sleep(self.config.polling_interval)
                else:
                    # Backoff on failure
                    backoff = self._calculate_backoff()
                    print(f"[Sender] Backing off for {backoff}s")
                    time.sleep(backoff)

                # Periodic cleanup of old sent records
                deleted = self.database.delete_sent(older_than_hours=24)
                if deleted > 0:
                    print(f"[Sender] Cleaned up {deleted} old records")

            except KeyboardInterrupt:
                print(f"[Sender] Stopping {self.get_socket_event_name()} sender")
                break
            except Exception as e:
                print(f"[Sender] Unexpected error: {e}")
                time.sleep(self.config.polling_interval)
