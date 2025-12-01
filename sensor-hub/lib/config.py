"""Configuration management for sensor-hub.

Provides type-safe configuration classes with environment variable loading.
Adapted from ssd-pi-engine/c3/lib/config.py
"""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SocketConfig:
    """Socket.IO connection configuration."""
    server_url: str
    device_key: str
    enabled: bool = True
    namespace: str = "/iot"

    @classmethod
    def from_env(cls) -> "SocketConfig":
        """Load Socket.IO configuration from environment variables."""
        return cls(
            server_url=os.getenv("SOCKETIO_SERVER_URL", "http://localhost:4100"),
            device_key=os.getenv("SOCKETIO_DEVICE_KEY", "sensor_hub_001"),
            enabled=os.getenv("SOCKETIO_ENABLED", "true").lower() == "true",
            namespace=os.getenv("SOCKETIO_NAMESPACE", "/iot"),
        )


@dataclass
class DatabaseConfig:
    """SQLite database configuration."""
    foot_db_file: str
    accel_db_file: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database configuration from environment variables."""
        return cls(
            foot_db_file=os.getenv("DB_FOOT_FILE", "./database/foot.db"),
            accel_db_file=os.getenv("DB_ACCEL_FILE", "./database/accel.db"),
        )


@dataclass
class SenderConfig:
    """Data sender configuration."""
    db_file: str
    webhook_urls: List[str]
    socket_event: str
    max_records: int = 100
    polling_interval: int = 30
    retry_backoff_base: int = 60
    max_backoff: int = 3600

    @classmethod
    def foot_from_env(cls) -> "SenderConfig":
        """Load foot sender configuration from environment variables."""
        webhook_str = os.getenv("WEBHOOK_FOOT_URLS", "")
        webhook_urls = [url.strip() for url in webhook_str.split(",") if url.strip()]

        return cls(
            db_file=os.getenv("DB_FOOT_FILE", "./database/foot.db"),
            webhook_urls=webhook_urls,
            socket_event="foot_pressure_data",
            max_records=int(os.getenv("SENDER_MAX_RECORDS", "100")),
            polling_interval=int(os.getenv("SENDER_POLLING_INTERVAL", "30")),
            retry_backoff_base=int(os.getenv("SENDER_RETRY_BACKOFF_BASE", "60")),
            max_backoff=int(os.getenv("SENDER_MAX_BACKOFF", "3600")),
        )

    @classmethod
    def accel_from_env(cls) -> "SenderConfig":
        """Load accelerometer sender configuration from environment variables."""
        webhook_str = os.getenv("WEBHOOK_ACCEL_URLS", "")
        webhook_urls = [url.strip() for url in webhook_str.split(",") if url.strip()]

        return cls(
            db_file=os.getenv("DB_ACCEL_FILE", "./database/accel.db"),
            webhook_urls=webhook_urls,
            socket_event="accelerometer_data",
            max_records=int(os.getenv("SENDER_MAX_RECORDS", "100")),
            polling_interval=int(os.getenv("SENDER_POLLING_INTERVAL", "30")),
            retry_backoff_base=int(os.getenv("SENDER_RETRY_BACKOFF_BASE", "60")),
            max_backoff=int(os.getenv("SENDER_MAX_BACKOFF", "3600")),
        )


@dataclass
class BLEConfig:
    """BLE sensor configuration."""
    left_foot_mac: Optional[str]
    right_foot_mac: Optional[str]
    accelerometer_mac: Optional[str]
    foot_throttle: int = 2
    accel_throttle: int = 5
    connection_retries: int = 3

    @classmethod
    def from_env(cls) -> "BLEConfig":
        """Load BLE configuration from environment variables."""
        left_mac = os.getenv("LEFT_FOOT_MAC")
        right_mac = os.getenv("RIGHT_FOOT_MAC")
        accel_mac = os.getenv("ACCELEROMETER_MAC")

        # Validate MAC addresses (None if placeholder)
        if left_mac and "XX:XX" in left_mac.upper():
            left_mac = None
        if right_mac and "XX:XX" in right_mac.upper():
            right_mac = None
        if accel_mac and "XX:XX" in accel_mac.upper():
            accel_mac = None

        return cls(
            left_foot_mac=left_mac,
            right_foot_mac=right_mac,
            accelerometer_mac=accel_mac,
            foot_throttle=int(os.getenv("FOOT_THROTTLE", "2")),
            accel_throttle=int(os.getenv("ACCEL_THROTTLE", "5")),
            connection_retries=int(os.getenv("CONNECTION_RETRIES", "3")),
        )


@dataclass
class Config:
    """Main configuration container."""
    socket: SocketConfig
    database: DatabaseConfig
    ble: BLEConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load all configuration from environment variables."""
        return cls(
            socket=SocketConfig.from_env(),
            database=DatabaseConfig.from_env(),
            ble=BLEConfig.from_env(),
        )
