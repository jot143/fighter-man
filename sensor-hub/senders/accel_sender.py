"""Accelerometer data sender.

Background process that transmits accelerometer data from SQLite to server.
"""

from typing import Optional

from lib.database.accel_db import AccelDatabase
from lib.socket_client import SocketIOClient
from lib.config import SenderConfig
from .base import DataSenderBase


class AccelSender(DataSenderBase):
    """Sender for accelerometer (IMU) sensor data."""

    def get_socket_event_name(self) -> str:
        return "accelerometer_data"


def create_accel_sender(
    socket_client: Optional[SocketIOClient] = None,
    config: Optional[SenderConfig] = None,
) -> AccelSender:
    """
    Create an accelerometer data sender with default configuration.

    Args:
        socket_client: Optional Socket.IO client
        config: Optional sender configuration

    Returns:
        Configured AccelSender instance
    """
    if config is None:
        config = SenderConfig.accel_from_env()

    database = AccelDatabase(config.db_file)

    return AccelSender(database, socket_client, config)
