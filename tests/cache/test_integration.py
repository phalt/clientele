from __future__ import annotations

import time

import pytest
from httpx import Response
from respx import MockRouter

from clientele import api, cache

BASE_URL = "https://pokeapi.co/api/v2"


class TestCachingContract:
    @pytest.mark.respx(base_url=BASE_URL)
    def test_basic_get_request_caching(self, respx_mock: MockRouter):
        """
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

        result1 = get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

        result2 = get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

    @pytest.mark.respx(base_url=BASE_URL)
    def test_different_parameters_different_cache(self, respx_mock: MockRouter):
        """
        Given: A cached GET endpoint
        When: Called with different parameters
        Then: Each unique parameter combination makes its own HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))
        respx_mock.get("/pokemon/1").mock(return_value=Response(json={"name": "bulbasaur"}, status_code=200))

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        get_pokemon(id=25)
        get_pokemon(id=1)
        get_pokemon(id=25)

        assert len(respx_mock.calls) == 2

    @pytest.mark.respx(base_url=BASE_URL)
    def test_cache_expiration(self, respx_mock: MockRouter):
        """
        Given: A cached endpoint with TTL=1 second
        When: Called, wait >1 second, call again
        Then: Second call makes new HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))

        @cache.memoize(ttl=1, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        get_pokemon(id=25)
        assert len(respx_mock.calls) == 1

        time.sleep(1.1)

        get_pokemon(id=25)
        assert len(respx_mock.calls) == 2

    @pytest.mark.respx(base_url="https://api.example.com", assert_all_called=False)
    def test_custom_cache_key(self, respx_mock: MockRouter):
        """
        Given: A cached endpoint with custom key function
        When: Custom key returns same value for different parameters
        Then: Those calls share the same cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")

        respx_mock.get("/users/1?version=1").mock(return_value=Response(json={"name": "Alice"}, status_code=200))
        respx_mock.get("/users/1?version=2").mock(return_value=Response(json={"name": "Alice v2"}, status_code=200))

        @cache.memoize(ttl=300, key=lambda id, version: f"user:{id}")
        @client.get("/users/{id}")
        def get_user(id: int, version: int, result: dict) -> dict:
            return result

        result1 = get_user(id=1, version=1)
        result2 = get_user(id=1, version=2)

        assert len(respx_mock.calls) == 1
        assert result1 == result2

    @pytest.mark.respx(base_url=BASE_URL)
    def test_caching_can_be_disabled(self, respx_mock: MockRouter):
        """
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

        get_pokemon(id=25)
        get_pokemon(id=25)

        assert len(respx_mock.calls) == 2

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_async_function_caching(self, respx_mock: MockRouter):
        """
        Given: A cached async GET endpoint
        When: Called twice with await
        Then: Second call returns cached result
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        respx_mock.get("/pokemon/25").mock(return_value=Response(json={"name": "pikachu"}, status_code=200))

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        async def get_pokemon(id: int, result: dict) -> dict:
            return result

        result1 = await get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

        result2 = await get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}
        assert len(respx_mock.calls) == 1

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_query_parameters_in_cache_key(self, respx_mock: MockRouter):
        """
        Given: A GET endpoint with query parameters
        When: Called with different query params
        Then: Each unique combination has its own cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")
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

        search(search_term="python", limit=10)
        search(search_term="python", limit=20)
        search(search_term="java", limit=10)
        search(search_term="python", limit=10)

        assert len(respx_mock.calls) == 3

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_none_results_not_cached(self, respx_mock: MockRouter):
        """
        Given: A cached endpoint that returns None
        When: Called multiple times
        Then: Each call executes (None not cached)
        """
        client = api.APIClient(base_url="https://api.example.com")

        respx_mock.get("/maybe-exists/999").mock(return_value=Response(json={}, status_code=200))

        call_count = [0]

        @cache.memoize(ttl=300)
        @client.get("/maybe-exists/{id}")
        def get_item(id: int, result: dict) -> dict | None:
            call_count[0] += 1
            return None

        result1 = get_item(id=999)
        result2 = get_item(id=999)

        assert result1 is None
        assert result2 is None

        assert call_count[0] == 2

    @pytest.mark.respx(base_url="https://api.example.com")
    def test_custom_backend(self, respx_mock: MockRouter):
        """
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

        get_item(id=1)  # Cache: [1]
        get_item(id=2)  # Cache: [1, 2]
        get_item(id=3)  # Cache: [2, 3] (evicts 1)

        get_item(id=1)  # Cache: [3, 1] (evicts 2)

        get_item(id=3)  # Cache: [1, 3] (moves 3 to end)

        assert len(respx_mock.calls) == 4
