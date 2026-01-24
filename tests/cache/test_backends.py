from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from clientele.cache.backends import MemoryBackend
from clientele.cache.types import CacheEntry
from clientele.testing import ResponseFactory, configure_client_for_testing
from tests.cache.fixtures import FakeCacheBackend

BASE_URL = "http://localhost"


class TestCacheEntry:
    def test_cache_entry_no_expiration(self):
        """Cache entry without TTL should never expire."""
        entry = CacheEntry(value="test_value", ttl=None)
        assert entry.value == "test_value"
        assert not entry.is_expired()

        # Even after some time, it should not expire
        time.sleep(0.1)
        assert not entry.is_expired()

    def test_cache_entry_with_ttl(self):
        """Cache entry with TTL should expire after specified time."""
        entry = CacheEntry(value="test_value", ttl=1)
        assert entry.value == "test_value"
        assert not entry.is_expired()

        # Wait for expiration
        time.sleep(1.1)
        assert entry.is_expired()


class TestMemoryBackend:
    """Tests for MemoryBackend."""

    def test_memory_backend_basic_set_and_get(self):
        """Basic set and get operations should work."""
        backend = MemoryBackend()
        backend.set("key1", "value1")

        assert backend.get("key1") == "value1"

    def test_memory_backend_get_nonexistent_key(self):
        """Getting a non-existent key should return None."""
        backend = MemoryBackend()
        assert backend.get("nonexistent") is None

    def test_memory_backend_ttl_expiration(self):
        """Values should expire after TTL."""
        backend = MemoryBackend()
        backend.set("key1", "value1", ttl=1)

        # Should exist initially
        assert backend.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should return None after expiration
        assert backend.get("key1") is None

    def test_memory_backend_lru_eviction(self):
        """LRU eviction should work when max_size is exceeded."""
        backend = MemoryBackend(max_size=3)

        # Add 3 items (at capacity)
        backend.set("key1", "value1")
        backend.set("key2", "value2")
        backend.set("key3", "value3")

        # All should be present
        assert backend.get("key1") == "value1"
        assert backend.get("key2") == "value2"
        assert backend.get("key3") == "value3"

        # Add a 4th item - should evict key1 (least recently used)
        backend.set("key4", "value4")

        # key1 should be evicted
        assert backend.get("key1") is None
        assert backend.get("key2") == "value2"
        assert backend.get("key3") == "value3"
        assert backend.get("key4") == "value4"

    def test_memory_backend_lru_access_updates_order(self):
        """Accessing a key should mark it as recently used."""
        backend = MemoryBackend(max_size=3)

        backend.set("key1", "value1")
        backend.set("key2", "value2")
        backend.set("key3", "value3")

        # Access key1 to mark it as recently used
        assert backend.get("key1") == "value1"

        # Add key4 - should evict key2 (now least recently used)
        backend.set("key4", "value4")

        # key1 should still exist, key2 should be evicted
        assert backend.get("key1") == "value1"
        assert backend.get("key2") is None
        assert backend.get("key3") == "value3"
        assert backend.get("key4") == "value4"

    def test_memory_backend_delete(self):
        """Delete should remove a key from cache."""
        backend = MemoryBackend()
        backend.set("key1", "value1")

        assert backend.get("key1") == "value1"

        backend.delete("key1")
        assert backend.get("key1") is None

    def test_memory_backend_delete_nonexistent(self):
        """Deleting a non-existent key should not raise an error."""
        backend = MemoryBackend()
        backend.delete("nonexistent")  # Should not raise

    def test_memory_backend_clear(self):
        """Clear should remove all entries."""
        backend = MemoryBackend()
        backend.set("key1", "value1")
        backend.set("key2", "value2")
        backend.set("key3", "value3")

        backend.clear()

        assert backend.get("key1") is None
        assert backend.get("key2") is None
        assert backend.get("key3") is None

    def test_memory_backend_exists(self):
        """Exists should return True for existing keys."""
        backend = MemoryBackend()
        backend.set("key1", "value1")

        assert backend.exists("key1")
        assert not backend.exists("key2")

    def test_memory_backend_exists_removes_expired(self):
        """Exists should remove expired entries and return False."""
        backend = MemoryBackend()
        backend.set("key1", "value1", ttl=1)

        # Should exist initially
        assert backend.exists("key1")

        # Wait for expiration
        time.sleep(1.1)

        # Should not exist after expiration
        assert not backend.exists("key1")

        # Key should be removed from cache
        assert backend.get("key1") is None

    def test_memory_backend_get_expired_entry_returns_none(self):
        """Getting an expired entry should return None and remove it."""
        backend = MemoryBackend()
        backend.set("key1", "value1", ttl=1)

        # Wait for expiration
        time.sleep(1.1)

        # Should return None
        assert backend.get("key1") is None

        # Entry should be removed from internal cache
        assert not backend.exists("key1")

    def test_memory_backend_update_existing_key(self):
        """Updating an existing key should replace the value and reset position."""
        backend = MemoryBackend(max_size=3)

        backend.set("key1", "value1")
        backend.set("key2", "value2")
        backend.set("key3", "value3")

        # Update key1 (moves it to end)
        backend.set("key1", "updated_value1")

        # Add key4 - should evict key2 (now least recently used)
        backend.set("key4", "value4")

        # key1 should exist with new value, key2 should be evicted
        assert backend.get("key1") == "updated_value1"
        assert backend.get("key2") is None
        assert backend.get("key3") == "value3"
        assert backend.get("key4") == "value4"

    def test_memory_backend_thread_safety(self):
        """Backend should be thread-safe for concurrent access."""
        backend = MemoryBackend(max_size=100)
        num_threads = 10
        ops_per_thread = 100

        def worker(thread_id):
            """Perform operations in a thread."""
            for i in range(ops_per_thread):
                key = f"key_{thread_id}_{i}"
                value = f"value_{thread_id}_{i}"

                backend.set(key, value)
                retrieved = backend.get(key)
                assert retrieved == value or retrieved is None  # May be evicted

        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            for future in futures:
                future.result()

    def test_memory_backend_different_value_types(self):
        """Backend should handle different value types."""
        backend = MemoryBackend()

        # Test various types
        backend.set("string", "hello")
        backend.set("int", 42)
        backend.set("float", 3.14)
        backend.set("list", [1, 2, 3])
        backend.set("dict", {"key": "value"})
        backend.set("none", None)

        assert backend.get("string") == "hello"
        assert backend.get("int") == 42
        assert backend.get("float") == 3.14
        assert backend.get("list") == [1, 2, 3]
        assert backend.get("dict") == {"key": "value"}
        assert backend.get("none") is None

    def test_memory_backend_zero_ttl(self):
        """Zero TTL should expire immediately."""
        backend = MemoryBackend()
        backend.set("key1", "value1", ttl=0)

        # Should expire immediately
        time.sleep(0.01)
        assert backend.get("key1") is None


class TestConfigBackend:
    """Tests for custom backend configuration in BaseConfig."""

    def test_custom_backend_via_config(self):
        """Custom backend set in BaseConfig should be used by memoize decorator."""
        from clientele import api, cache

        custom_backend = FakeCacheBackend()
        # Create APIClient with custom backend in config
        client = api.APIClient(
            config=api.BaseConfig(
                base_url=BASE_URL,
                cache_backend=custom_backend,
            ),
        )

        fake_http_backend = configure_client_for_testing(client)
        return_json = {"data": "value"}
        fake_http_backend.queue_response(
            path="/test/1",
            response_obj=ResponseFactory.ok(
                data=return_json,
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300)
        @client.get("/test/{id}")
        def get_item(id: int, *, result: dict) -> dict:
            return result

        response1 = get_item(1)
        assert response1 == return_json

        assert custom_backend.store == {"GET:/test/{id}:id=1": {"data": "value"}}

        client.close()
