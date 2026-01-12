"""

This module provides simple TTL-based caching for HTTP GET requests.

Only use caching for idempotent operations (GET requests).
Do NOT cache POST/PUT/PATCH/DELETE as they modify state.

Basic usage:
-----------
    from clientele import api, cache

    client = api.APIClient(base_url="https://api.example.com")

    @cache.memoize(ttl=300)  # Cache for 5 minutes
    @client.get("/users/{id}")
    def get_user(id: int, result: dict) -> dict:
        return result

    # First call - makes HTTP request
    user = get_user(id=123)

    # Second call within 5 minutes - returns from cache
    user = get_user(id=123)  # No HTTP request

Custom cache keys:
-----------------
    @cache.memoize(ttl=600, key=lambda id: f"user:{id}")
    @client.get("/users/{id}")
    def get_user(id: int, result: dict) -> dict:
        return result

Custom backend:
--------------
    # Use a larger in-memory cache
    big_cache = cache.MemoryBackend(max_size=1000)

    @cache.memoize(ttl=300, backend=big_cache)
    @client.get("/products/{id}")
    def get_product(id: int, result: dict) -> dict:
        return result

Conditional caching:
-------------------
    import os
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true") == "true"

    @cache.memoize(ttl=300, enabled=ENABLE_CACHE)
    @client.get("/data")
    def get_data(result: dict) -> dict:
        return result
"""

from clientele.cache.backends import MemoryBackend
from clientele.cache.decorator import (
    memoize,
)
from clientele.cache.types import CacheBackend, CacheEntry

__all__ = [
    "memoize",
    "MemoryBackend",
    "CacheBackend",
    "CacheEntry",
]
