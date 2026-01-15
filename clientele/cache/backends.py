from __future__ import annotations

import collections
import threading
import typing

from clientele.cache.types import CacheBackend, CacheEntry


class MemoryBackend(CacheBackend):
    """Thread-safe in-memory LRU cache backend.

    Uses an OrderedDict for LRU eviction when the cache reaches max_size.
    Thread-safe for concurrent access using a threading.RLock.

    Args:
        max_size: Maximum number of entries to store (default: 128)
                  When exceeded, least recently used entries are evicted.
    """

    def __init__(self, max_size: int = 128):
        """Initialize the memory backend."""
        self.max_size = max_size
        self._cache: collections.OrderedDict[str, CacheEntry] = collections.OrderedDict()
        self._lock = threading.RLock()

    def _get_valid_entry(self, key: str) -> typing.Optional[CacheEntry]:
        """Get entry if exists and not expired, removing expired entries.

        Must be called within self._lock context.
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None

        return entry

    def get(self, key: str) -> typing.Optional[typing.Any]:
        """Retrieve a value from the cache (thread-safe)."""
        with self._lock:
            entry = self._get_valid_entry(key)
            if entry is None:
                return None

            # Mark as recently used
            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: typing.Any, ttl: typing.Optional[int | float] = None) -> None:
        """Store a value in the cache (thread-safe)."""
        with self._lock:
            # Remove existing entry to update position
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            entry = CacheEntry(value, ttl)
            self._cache[key] = entry

            # Evict oldest if over capacity
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Remove a value from the cache (thread-safe)."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all values from the cache (thread-safe)."""
        with self._lock:
            self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache (thread-safe)."""
        with self._lock:
            return self._get_valid_entry(key) is not None
