from __future__ import annotations

import time
import typing

# CacheBackend is defined in clientele.api.config, because BaseConfig accepts one.
from clientele.api.config import CacheBackend

__all__ = [
    "CacheBackend",
    "CacheEntry",
]


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
