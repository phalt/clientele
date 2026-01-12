"""Integration tests that serve as usage contracts for the cache module.

These tests demonstrate the expected behavior and serve as living documentation.
"""

import time

import pytest
from httpx import Response
from respx import MockRouter

from clientele import api, cache

BASE_URL = "https://pokeapi.co/api/v2"


class TestCachingContract:
    """Contract tests defining expected caching behavior."""

    @pytest.mark.respx(base_url=BASE_URL)
    def test_basic_get_request_caching(self, respx_mock: MockRouter):
        """
        CONTRACT: GET requests with same parameters return cached results.

        Given: A cached GET endpoint
        When: Called twice with same parameters
        Then: Second call returns cached result without making HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)

        mocked_response = {"name": "pikachu"}
        respx_mock.get("/pokemon/25").mock(return_value=Response(json=mocked_response, status_code=200))

        @cache.memoize(ttl=300)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        # First call - should make HTTP request
        result1 = get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

        # Second call - should return from cache (no new HTTP request)
        result2 = get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1  # Still only 1 call

    @pytest.mark.respx(base_url=BASE_URL)
    def test_different_parameters_different_cache(self, respx_mock: MockRouter):
        """
        CONTRACT: Different parameters create different cache entries.

        Given: A cached GET endpoint
        When: Called with different parameters
        Then: Each unique parameter combination makes its own HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        # Use isolated cache backend
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))
        respx_mock.get("/pokemon/1").mock(return_value=Response(json={"name": "bulbasaur"}, status_code=200))

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        # Call with id=25
        get_pokemon(id=25)

        # Call with id=1 - should make new request
        get_pokemon(id=1)

        # Call with id=25 again - should use cache
        get_pokemon(id=25)

        # Should have made exactly 2 HTTP requests (not 3)
        assert len(respx_mock.calls) == 2

    @pytest.mark.respx(base_url=BASE_URL)
    def test_cache_expiration(self, respx_mock: MockRouter):
        """
        CONTRACT: Cache entries expire after TTL.

        Given: A cached endpoint with TTL=1 second
        When: Called, wait >1 second, call again
        Then: Second call makes new HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        # Use isolated cache backend
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))

        @cache.memoize(ttl=1, backend=isolated_cache)  # 1 second TTL
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        # First call
        get_pokemon(id=25)
        assert len(respx_mock.calls) == 1

        # Wait for cache to expire
        time.sleep(1.1)

        # Second call - cache expired, should make new request
        get_pokemon(id=25)
        assert len(respx_mock.calls) == 2

    @pytest.mark.respx(base_url="https://api.example.com", assert_all_called=False)
    def test_custom_cache_key(self, respx_mock: MockRouter):
        """
        CONTRACT: Custom key function determines cache identity.

        Given: A cached endpoint with custom key function
        When: Custom key returns same value for different parameters
        Then: Those calls share the same cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")

        respx_mock.get("/users/1?version=1").mock(return_value=Response(json={"name": "Alice"}, status_code=200))
        respx_mock.get("/users/1?version=2").mock(return_value=Response(json={"name": "Alice v2"}, status_code=200))

        # Custom key ignores version parameter
        @cache.memoize(ttl=300, key=lambda id, version: f"user:{id}")
        @client.get("/users/{id}")
        def get_user(id: int, version: int, result: dict) -> dict:
            return result

        # Call with different versions
        result1 = get_user(id=1, version=1)
        result2 = get_user(id=1, version=2)  # Different version, same key

        # Should only make one request (shared cache key)
        assert len(respx_mock.calls) == 1
        # Both results should be the same (from cache)
        assert result1 == result2

    @pytest.mark.respx(base_url=BASE_URL)
    def test_caching_can_be_disabled(self, respx_mock: MockRouter):
        """
        CONTRACT: enabled=False disables caching without removing decorator.

        Given: A cached endpoint with enabled=False
        When: Called multiple times
        Then: Each call makes HTTP request (no caching)
        """
        client = api.APIClient(base_url=BASE_URL)

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))

        @cache.memoize(ttl=300, enabled=False)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        # Call twice
        get_pokemon(id=25)
        get_pokemon(id=25)

        # Should make two requests (caching disabled)
        assert len(respx_mock.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_async_function_caching(self, respx_mock: MockRouter):
        """
        CONTRACT: Async functions are cached correctly.

        Given: A cached async GET endpoint
        When: Called twice with await
        Then: Second call returns cached result
        """
        client = api.APIClient(base_url=BASE_URL)
        # Use isolated cache backend
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        async def get_pokemon(id: int, result: dict) -> dict:
            return result

        # First call
        result1 = await get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

        # Second call - should use cache
        result2 = await get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1  # Still only 1 call

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_query_parameters_in_cache_key(self, respx_mock: MockRouter):
        """
        CONTRACT: Query parameters are part of cache key.

        Given: A GET endpoint with query parameters
        When: Called with different query params
        Then: Each unique combination has its own cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")
        # Use isolated cache backend
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/search?search_term=python&limit=10").mock(
            return_value=Response(json={"results": ["result1"]}, status_code=200)
        )
        respx_mock.get("/search?search_term=python&limit=20").mock(
            return_value=Response(json={"results": ["result2"]}, status_code=200)
        )
        respx_mock.get("/search?search_term=java&limit=10").mock(
            return_value=Response(json={"results": ["result3"]}, status_code=200)
        )

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/search")
        def search(search_term: str, limit: int, result: dict) -> dict:
            return result

        # Different combinations
        search(search_term="python", limit=10)
        search(search_term="python", limit=20)  # Different limit
        search(search_term="java", limit=10)  # Different query
        search(search_term="python", limit=10)  # Same as first - cache hit

        # Should make 3 requests (not 4)
        assert len(respx_mock.calls) == 3

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_none_results_not_cached(self, respx_mock: MockRouter):
        """
        CONTRACT: None results are not cached.

        Given: A cached endpoint that returns None
        When: Called multiple times
        Then: Each call executes (None not cached)
        """
        client = api.APIClient(base_url="https://api.example.com")

        # Return empty dict instead of None to avoid API exceptions
        respx_mock.get("/maybe-exists/999").mock(return_value=Response(json={}, status_code=200))

        call_count = [0]

        @cache.memoize(ttl=300)
        @client.get("/maybe-exists/{id}")
        def get_item(id: int, result: dict) -> dict | None:
            call_count[0] += 1
            return None  # Return None despite getting data

        # Call twice
        result1 = get_item(id=999)
        result2 = get_item(id=999)

        # Both should return None
        assert result1 is None
        assert result2 is None
        # Both calls should execute (None not cached)
        assert call_count[0] == 2

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_custom_backend(self, respx_mock: MockRouter):
        """
        CONTRACT: Custom backend is respected.

        Given: A cached endpoint with custom backend
        When: Backend is configured with max_size=2
        Then: LRU eviction happens after 2 entries
        """
        client = api.APIClient(base_url="https://api.example.com")
        small_cache = cache.MemoryBackend(max_size=2)

        respx_mock.get("/items/1").mock(return_value=Response(json={"item": "data1"}, status_code=200))
        respx_mock.get("/items/2").mock(return_value=Response(json={"item": "data2"}, status_code=200))
        respx_mock.get("/items/3").mock(return_value=Response(json={"item": "data3"}, status_code=200))

        @cache.memoize(ttl=300, backend=small_cache)
        @client.get("/items/{id}")
        def get_item(id: int, result: dict) -> dict:
            return result

        # Add 3 items to cache (max_size=2)
        get_item(id=1)  # Cache: [1]
        get_item(id=2)  # Cache: [1, 2]
        get_item(id=3)  # Cache: [2, 3] (evicts 1)

        # Call id=1 again - should make new request (was evicted)
        get_item(id=1)  # Cache: [3, 1] (evicts 2)

        # Call id=3 again - should use cache (still present)
        get_item(id=3)  # Cache: [1, 3] (moves 3 to end)

        # Total requests: 4 (id=1, id=2, id=3, id=1 again)
        # id=3 second call uses cache
        assert len(respx_mock.calls) == 4
