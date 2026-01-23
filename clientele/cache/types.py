from __future__ import annotations

import abc
import time
import typing


class CacheBackend(abc.ABC):
    """Protocol for cache backend implementations.

    All cache backends must implement these methods.
    Thread-safe implementations are required for concurrent usage.
    """

    @abc.abstractmethod
    def get(self, key: str) -> typing.Optional[typing.Any]:
        """Retrieve a value from the cache.

        Args:
            key: The cache key

        Returns:
            The cached value if found and not expired, None otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, key: str, value: typing.Any, ttl: typing.Optional[int | float] = None) -> None:
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


class CacheEntry:
    """Represents a cached entry with expiration.

    Internal class used by cache backends to track value lifetime.
    """

    def __init__(self, value: typing.Any, ttl: typing.Optional[int | float] = None):
        """Initialize a cache entry.

        Args:
            value: The value to cache
            ttl: Time-to-live in seconds (None = no expiration)
        """
        self._value = value
        self._created_at = time.time()
        self._expires_at = None if ttl is None else (self._created_at + ttl)

    def is_expired(self) -> bool:
        """Check if this entry has expired.

        Returns:
            True if past expiration time, False otherwise (or if no expiration)
        """
        if self._expires_at is None:
            return False
        return time.time() > self._expires_at

    @property
    def value(self) -> typing.Any:
        """Get the cached value."""
        return self._value
