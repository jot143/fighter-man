#!/usr/bin/env python3
"""Entry point for foot pressure data sender.

Run this as a separate process to transmit buffered foot data to the server.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from lib.config import SocketConfig, SenderConfig
from lib.socket_client import init_client
from senders.foot_sender import create_foot_sender


def main():
    """Start the foot data sender."""
    print("=" * 60)
    print("Foot Pressure Data Sender")
    print("=" * 60)

    # Load configuration
    socket_config = SocketConfig.from_env()
    sender_config = SenderConfig.foot_from_env()

    print(f"Socket.IO Server: {socket_config.server_url}")
    print(f"Database: {sender_config.db_file}")
    print(f"Polling Interval: {sender_config.polling_interval}s")
    print("=" * 60)

    # Initialize Socket.IO client if enabled
    socket_client = None
    if socket_config.enabled:
        socket_client = init_client(
            socket_config.server_url,
            socket_config.device_key,
            socket_config.namespace,
        )
        if socket_client.connect():
            print("[Socket.IO] Connected successfully")
        else:
            print("[Socket.IO] Connection failed, using HTTP fallback")

    # Create and run sender
    sender = create_foot_sender(socket_client, sender_config)
    sender.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down foot sender...")
        sys.exit(0)
