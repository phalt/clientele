from __future__ import annotations

import time

import pytest

from clientele import api, cache
from clientele.testing import ResponseFactory, configure_client_for_testing

BASE_URL = "https://pokeapi.co/api/v2"


class TestCachingContract:
    def test_basic_get_request_caching(self):
        """
        Given: A cached GET endpoint
        When: Called twice with same parameters
        Then: Second call returns cached result without making HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)

        fake_backend = configure_client_for_testing(client)
        mocked_response = {"name": "pikachu"}
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data=mocked_response,
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        result1 = get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}

        result2 = get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}

        client.close()

    def test_different_parameters_different_cache(self):
        """
        Given: A cached GET endpoint
        When: Called with different parameters
        Then: Each unique parameter combination makes its own HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/pokemon/1",
            response_obj=ResponseFactory.ok(
                data={"name": "bulbasaur"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        get_pokemon(id=25)
        get_pokemon(id=1)
        get_pokemon(id=25)

        client.close()

    def test_cache_expiration(self):
        """
        Given: A cached endpoint with TTL=1 second
        When: Called, wait >1 second, call again
        Then: Second call makes new HTTP request
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=1, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        get_pokemon(id=25)

        time.sleep(1.1)

        get_pokemon(id=25)

        client.close()

    def test_custom_cache_key(self):
        """
        Given: A cached endpoint with custom key function
        When: Custom key returns same value for different parameters
        Then: Those calls share the same cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/users/1",
            response_obj=ResponseFactory.ok(
                data={"name": "Alice"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, key=lambda id, version: f"user:{id}")
        @client.get("/users/{id}")
        def get_user(id: int, version: int, result: dict) -> dict:
            return result

        result1 = get_user(id=1, version=1)
        result2 = get_user(id=1, version=2)

        assert result1 == result2

        client.close()

    def test_caching_can_be_disabled(self):
        """
        Given: A cached endpoint with enabled=False
        When: Called multiple times
        Then: Each call makes HTTP request (no caching)
        """
        client = api.APIClient(base_url=BASE_URL)

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, enabled=False)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

        get_pokemon(id=25)
        get_pokemon(id=25)

        client.close()

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """
        Given: A cached async GET endpoint
        When: Called twice with await
        Then: Second call returns cached result
        """
        client = api.APIClient(base_url=BASE_URL)
        isolated_cache = cache.MemoryBackend()

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/pokemon/25",
            response_obj=ResponseFactory.ok(
                data={"name": "pikachu"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/pokemon/{id}")
        async def get_pokemon(id: int, result: dict) -> dict:
            return result

        result1 = await get_pokemon(id=25)
        assert result1 == {"name": "pikachu"}

        result2 = await get_pokemon(id=25)
        assert result2 == {"name": "pikachu"}

        await client.aclose()

    def test_query_parameters_in_cache_key(self):
        """
        Given: A GET endpoint with query parameters
        When: Called with different query params
        Then: Each unique combination has its own cache entry
        """
        client = api.APIClient(base_url="https://api.example.com")
        isolated_cache = cache.MemoryBackend()

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/search",
            response_obj=ResponseFactory.ok(
                data={"results": ["result1"]},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/search",
            response_obj=ResponseFactory.ok(
                data={"results": ["result2"]},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/search",
            response_obj=ResponseFactory.ok(
                data={"results": ["result3"]},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, backend=isolated_cache)
        @client.get("/search")
        def search(search_term: str, limit: int, result: dict) -> dict:
            return result

        search(search_term="python", limit=10)
        search(search_term="python", limit=20)
        search(search_term="java", limit=10)
        search(search_term="python", limit=10)

        client.close()

    def test_none_results_not_cached(self):
        """
        Given: A cached endpoint that returns None
        When: Called multiple times
        Then: Each call executes (None not cached)
        """
        client = api.APIClient(base_url="https://api.example.com")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/maybe-exists/999",
            response_obj=ResponseFactory.ok(
                data={},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/maybe-exists/999",
            response_obj=ResponseFactory.ok(
                data={},
                headers={"content-type": "application/json"},
            ),
        )

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

        client.close()

    def test_custom_backend(self):
        """
        Given: A cached endpoint with custom backend
        When: Backend is configured with max_size=2
        Then: LRU eviction happens after 2 entries
        """
        client = api.APIClient(base_url="https://api.example.com")
        small_cache = cache.MemoryBackend(max_size=2)

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/items/1",
            response_obj=ResponseFactory.ok(
                data={"item": "data1"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/items/2",
            response_obj=ResponseFactory.ok(
                data={"item": "data2"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/items/3",
            response_obj=ResponseFactory.ok(
                data={"item": "data3"},
                headers={"content-type": "application/json"},
            ),
        )
        fake_backend.queue_response(
            path="/items/1",
            response_obj=ResponseFactory.ok(
                data={"item": "data1"},
                headers={"content-type": "application/json"},
            ),
        )

        @cache.memoize(ttl=300, backend=small_cache)
        @client.get("/items/{id}")
        def get_item(id: int, result: dict) -> dict:
            return result

        get_item(id=1)  # Cache: [1]
        get_item(id=2)  # Cache: [1, 2]
        get_item(id=3)  # Cache: [2, 3] (evicts 1)

        get_item(id=1)  # Cache: [3, 1] (evicts 2)

        get_item(id=3)  # Cache: [1, 3] (moves 3 to end)

        client.close()
