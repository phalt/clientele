from __future__ import annotations

import abc
from typing import Any, Optional, Protocol, runtime_checkable

import pydantic
import pydantic_settings

from clientele.http import backends as http_backends


@runtime_checkable
class Logger(Protocol):
    """Protocol for logger implementations.

    Compatible with Python's standard logging.Logger interface.
    Users can pass any logging.getLogger() instance or custom logger
    that implements these methods.
    """

    def debug(self, msg: Any, *args: Any) -> None: ...
    def info(self, msg: Any, *args: Any) -> None: ...
    def warning(self, msg: Any, *args: Any) -> None: ...
    def error(self, msg: Any, *args: Any) -> None: ...


class CacheBackend(abc.ABC):
    """Protocol for cache backend implementations.

    All cache backends must implement these methods.
    Thread-safe implementations are required for concurrent usage.

    Defined here, rather than in clientele.cache, because BaseConfig accepts one.
    clientele.cache re-exports it.
    """

    @abc.abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value if found and not expired, None otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int | float] = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache (must be picklable for some backends)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Remove a value from the cache.

        Args:
            key: The cache key to remove
        """
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self) -> None:
        """Clear all values from the cache."""
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists and is not expired, False otherwise
        """
        raise NotImplementedError


class BaseConfig(pydantic_settings.BaseSettings):
    """
    Runtime configuration for clientele clients.

    Values can be set via:
    1. Environment variables (see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage)
    2. Direct instantiation with keyword arguments
    3. .env file (if python-dotenv is installed)

    Example:
        # From environment variables
        export API_BASE_URL="https://api.example.com"
        export BEARER_TOKEN="my-secret-token"
        config = Config()

        # Direct instantiation
        config = Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token",
            timeout=10.0
        )
    """

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    base_url: str = "http://localhost"
    headers: dict[str, str] = pydantic.Field(default_factory=dict)
    timeout: float | None = 5.0
    follow_redirects: bool = False
    verify: bool | str = True
    http2: bool = False
    # Cache configuration
    cache_backend: CacheBackend | None = None
    # HTTP backend configuration
    http_backend: http_backends.HTTPBackend | None = None
    # Logging configuration
    logger: Logger | None = None


def get_default_config(base_url: str) -> BaseConfig:
    """
    Create a default configuration instance.

    Returns a BaseConfig with sensible defaults suitable for most use cases.
    Users can override specific values by passing keyword arguments to Client
    or by providing their own Config instance.
    """
    return BaseConfig(
        base_url=base_url,
        headers={},
        timeout=5.0,
        follow_redirects=False,
        verify=True,
        http2=False,
        cache_backend=None,
        http_backend=None,
        logger=None,
    )
