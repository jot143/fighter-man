"""Foot pressure data sender.

Background process that transmits foot sensor data from SQLite to server.
"""

from typing import Optional

from lib.database.foot_db import FootDatabase
from lib.socket_client import SocketIOClient
from lib.config import SenderConfig
from .base import DataSenderBase


class FootSender(DataSenderBase):
    """Sender for foot pressure sensor data."""

    def get_socket_event_name(self) -> str:
        return "foot_pressure_data"


def create_foot_sender(
    socket_client: Optional[SocketIOClient] = None,
    config: Optional[SenderConfig] = None,
) -> FootSender:
    """
    Create a foot data sender with default configuration.

    Args:
        socket_client: Optional Socket.IO client
        config: Optional sender configuration

    Returns:
        Configured FootSender instance
    """
    if config is None:
        config = SenderConfig.foot_from_env()

    database = FootDatabase(config.db_file)

    return FootSender(database, socket_client, config)
