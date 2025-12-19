"""Configuration management for firefighter-server."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ServerConfig:
    """Flask server configuration."""
    host: str = "0.0.0.0"
    port: int = 4100
    debug: bool = True
    secret_key: str = "dev-secret-key"

    @classmethod
    def from_env(cls) -> "ServerConfig":
        return cls(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "4100")),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            secret_key=os.getenv("SECRET_KEY", "dev-secret-key"),
        )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""
    host: str = "localhost"
    port: int = 6333
    collection: str = "sensor_windows"
    vector_dimension: int = 270
    window_size_ms: int = 500

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection=os.getenv("QDRANT_COLLECTION", "sensor_windows"),
            vector_dimension=int(os.getenv("VECTOR_DIMENSION", "270")),
            window_size_ms=int(os.getenv("WINDOW_SIZE_MS", "500")),
        )


@dataclass
class PostgresConfig:
    """PostgreSQL database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "firefighter"
    user: str = "firefighter_user"
    password: str = "dev_password"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "firefighter"),
            user=os.getenv("POSTGRES_USER", "firefighter_user"),
            password=os.getenv("POSTGRES_PASSWORD", "dev_password"),
            pool_size=int(os.getenv("POSTGRES_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("POSTGRES_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("POSTGRES_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("POSTGRES_POOL_RECYCLE", "3600")),
            echo=os.getenv("POSTGRES_ECHO", "false").lower() == "true",
        )

    @property
    def connection_url(self) -> str:
        """Get SQLAlchemy connection URL."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class AuthConfig:
    """Device authentication configuration."""
    allowed_device_keys: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "AuthConfig":
        keys_str = os.getenv("ALLOWED_DEVICE_KEYS", "")
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        return cls(allowed_device_keys=keys)

    def is_valid_device(self, device_key: str) -> bool:
        """Check if device key is authorized."""
        if not self.allowed_device_keys:
            return True  # No restrictions if list is empty
        return device_key in self.allowed_device_keys


@dataclass
class Config:
    """Main configuration container."""
    server: ServerConfig
    qdrant: QdrantConfig
    postgres: PostgresConfig
    auth: AuthConfig

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            server=ServerConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            postgres=PostgresConfig.from_env(),
            auth=AuthConfig.from_env(),
        )
