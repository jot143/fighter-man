"""Socket.IO client for real-time data transmission.

Handles connection management, auto-reconnection, and device authentication.
Adapted from ssd-pi-engine/c3/lib/socket_client.py
"""

import socketio
import time
from typing import Any, Callable, Optional


class SocketIOClient:
    """Socket.IO client with auto-reconnection and device authentication."""

    def __init__(
        self,
        server_url: str,
        device_key: str,
        namespace: str = "/iot",
        reconnect_delay: float = 5.0,
        max_reconnect_delay: float = 60.0,
    ):
        """
        Initialize Socket.IO client.

        Args:
            server_url: Server URL (e.g., "http://localhost:4100")
            device_key: Device identifier for authentication
            namespace: Socket.IO namespace (default: "/iot")
            reconnect_delay: Initial delay between reconnect attempts
            max_reconnect_delay: Maximum delay between reconnect attempts
        """
        self.server_url = server_url
        self.device_key = device_key
        self.namespace = namespace
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay

        self._connected = False
        self._authenticated = False
        self._reconnect_handlers: list[Callable] = []
        self._current_delay = reconnect_delay

        # Create Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite
            reconnection_delay=reconnect_delay,
            reconnection_delay_max=max_reconnect_delay,
            logger=False,
            engineio_logger=False,
        )

        # Register event handlers
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        @self.sio.on("connect", namespace=self.namespace)
        def on_connect():
            print(f"[SocketIO] Connected to {self.server_url}")
            self._connected = True
            self._current_delay = self.reconnect_delay
            # Authenticate on connection
            self._authenticate()

        @self.sio.on("disconnect", namespace=self.namespace)
        def on_disconnect():
            print("[SocketIO] Disconnected from server")
            self._connected = False
            self._authenticated = False

        @self.sio.on("auth_success", namespace=self.namespace)
        def on_auth_success(data):
            print(f"[SocketIO] Authenticated as: {data.get('device_key', self.device_key)}")
            self._authenticated = True
            # Notify reconnect handlers
            for handler in self._reconnect_handlers:
                try:
                    handler()
                except Exception as e:
                    print(f"[SocketIO] Reconnect handler error: {e}")

        @self.sio.on("auth_error", namespace=self.namespace)
        def on_auth_error(data):
            print(f"[SocketIO] Authentication failed: {data.get('message', 'Unknown error')}")
            self._authenticated = False

        @self.sio.on("connect_error", namespace=self.namespace)
        def on_connect_error(data):
            print(f"[SocketIO] Connection error: {data}")

    def _authenticate(self) -> None:
        """Send authentication message to server."""
        try:
            self.sio.emit(
                "authenticate",
                {"device_key": self.device_key},
                namespace=self.namespace,
            )
        except Exception as e:
            print(f"[SocketIO] Authentication emit error: {e}")

    def connect(self) -> bool:
        """
        Connect to the Socket.IO server.

        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            return True

        try:
            self.sio.connect(
                self.server_url,
                namespaces=[self.namespace],
                wait_timeout=10,
            )
            return True
        except Exception as e:
            print(f"[SocketIO] Connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the server."""
        try:
            self.sio.disconnect()
        except Exception:
            pass
        self._connected = False
        self._authenticated = False

    def emit(self, event: str, data: Any) -> bool:
        """
        Emit an event to the server.

        Args:
            event: Event name
            data: Data to send

        Returns:
            True if emit successful, False otherwise
        """
        if not self._connected:
            return False

        try:
            self.sio.emit(event, data, namespace=self.namespace)
            return True
        except Exception as e:
            print(f"[SocketIO] Emit error for {event}: {e}")
            return False

    def emit_with_ack(self, event: str, data: Any, timeout: float = 5.0) -> Optional[Any]:
        """
        Emit an event and wait for acknowledgment.

        Args:
            event: Event name
            data: Data to send
            timeout: Timeout in seconds

        Returns:
            Server response or None if failed/timeout
        """
        if not self._connected:
            return None

        try:
            response = self.sio.call(
                event,
                data,
                namespace=self.namespace,
                timeout=timeout,
            )
            return response
        except Exception as e:
            print(f"[SocketIO] Emit with ack error for {event}: {e}")
            return None

    def register_reconnect_handler(self, callback: Callable) -> None:
        """
        Register a callback to be called after successful reconnection.

        Args:
            callback: Function to call after reconnection
        """
        self._reconnect_handlers.append(callback)

    def wait(self) -> None:
        """Wait for the client to disconnect (blocking)."""
        self.sio.wait()

    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self._connected

    @property
    def authenticated(self) -> bool:
        """Check if authenticated with server."""
        return self._authenticated


# Singleton instance for global use
_client: Optional[SocketIOClient] = None


def get_client() -> Optional[SocketIOClient]:
    """Get the global Socket.IO client instance."""
    return _client


def init_client(
    server_url: str,
    device_key: str,
    namespace: str = "/iot",
) -> SocketIOClient:
    """
    Initialize the global Socket.IO client.

    Args:
        server_url: Server URL
        device_key: Device identifier
        namespace: Socket.IO namespace

    Returns:
        Initialized SocketIOClient instance
    """
    global _client
    _client = SocketIOClient(server_url, device_key, namespace)
    return _client
