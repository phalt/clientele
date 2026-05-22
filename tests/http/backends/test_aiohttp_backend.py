"""Tests for the aiohttp HTTP backend."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aioresponses import aioresponses

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import aiohttp_backend

BASE_URL = "https://api.example.com"


class TestAiohttpHTTPBackend:
    # --- Sync-not-supported ---

    def test_build_client_raises(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.build_client()

    def test_send_sync_request_raises(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.send_sync_request("GET", "/get")

    def test_handle_sync_stream_raises(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            list(backend.handle_sync_stream("GET", "/stream", str))

    def test_close_is_noop(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        backend.close()

    # --- Client lifecycle ---

    @pytest.mark.asyncio
    async def test_build_async_client_returns_session(self):
        import aiohttp

        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        session = backend.build_async_client()
        assert isinstance(session, aiohttp.ClientSession)
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_build_async_client_reuse(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_async_client()
        s2 = backend.build_async_client()
        assert s1 is s2
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_build_async_client_recreates_when_closed(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        session = backend.build_async_client()
        await session.close()
        s2 = backend.build_async_client()
        assert s2 is not session
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_aclose_closes_session(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        backend._async_client = mock_session

        await backend.aclose()

        mock_session.close.assert_called_once()
        assert backend._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_skips_already_closed(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        mock_session = MagicMock()
        mock_session.closed = True
        mock_session.close = AsyncMock()
        backend._async_client = mock_session

        await backend.aclose()

        mock_session.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_aclose_is_idempotent(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        await backend.aclose()
        await backend.aclose()

    # --- Config / URL helpers ---

    def test_from_config(self):
        config = api_config.BaseConfig(
            base_url=BASE_URL,
            headers={"X-API-Key": "secret"},
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        )
        backend = aiohttp_backend.AiohttpHTTPBackend.from_config(config)
        assert backend.base_url == BASE_URL
        assert backend.headers == {"X-API-Key": "secret"}
        assert backend.follow_redirects is True
        assert backend._ssl is False

    def test_full_url_strips_double_slash(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"

    def test_full_url_absolute_unchanged(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        assert backend._full_url("https://other.example.com/path") == "https://other.example.com/path"

    def test_ssl_none_when_verify_true(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL, verify=True)
        assert backend._ssl is None

    def test_ssl_false_when_verify_false(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL, verify=False)
        assert backend._ssl is False

    # --- convert_to_response ---

    @pytest.mark.asyncio
    async def test_convert_to_response(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/get", body=b"hello", status=201)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            session = backend.build_async_client()
            async with session.request("GET", f"{BASE_URL}/get") as resp:
                await resp.read()
                result = aiohttp_backend.AiohttpHTTPBackend.convert_to_response(resp)
            await backend.aclose()

        assert result.status_code == 201
        assert result.content == b"hello"
        assert result.request_method == "GET"
        assert result.request_url == f"{BASE_URL}/get"

    @pytest.mark.asyncio
    async def test_convert_to_response_empty_body(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/empty", body=b"", status=200)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            session = backend.build_async_client()
            async with session.request("GET", f"{BASE_URL}/empty") as resp:
                await resp.read()
                result = aiohttp_backend.AiohttpHTTPBackend.convert_to_response(resp)
            await backend.aclose()

        assert result.content == b""

    # --- Async request/streaming ---

    @pytest.mark.asyncio
    async def test_send_async_request(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/users/1", payload={"id": 1, "name": "Alice"}, status=200)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            result = await backend.send_async_request("GET", "/users/1")
            await backend.aclose()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}
        assert result.request_method == "GET"
        assert result.request_url == f"{BASE_URL}/users/1"

    @pytest.mark.asyncio
    async def test_send_async_request_post(self):
        with aioresponses() as m:
            m.post(f"{BASE_URL}/items", payload={"id": 99}, status=201)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            result = await backend.send_async_request("POST", "/items", json={"name": "foo"})
            await backend.aclose()

        assert result.status_code == 201

    @pytest.mark.asyncio
    async def test_handle_async_stream_yields_lines(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/stream", body=b"line one\nline two\nline three\n", status=200)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            results = []
            async for item in backend.handle_async_stream("GET", "/stream", str, response_parser=lambda x: x):
                results.append(item)
            await backend.aclose()

        assert results == ["line one", "line two", "line three"]

    @pytest.mark.asyncio
    async def test_full_clientele_integration(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/users/1", payload={"id": 1, "name": "Alice"}, status=200)

            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            config = api_config.BaseConfig(base_url=BASE_URL, http_backend=backend)
            client = api_client.APIClient(config=config)

            @client.get("/users/{user_id}")
            async def get_user(result: dict, user_id: int) -> dict:
                return result

            result = await get_user(1)
            assert result == {"id": 1, "name": "Alice"}
            await client.aclose()

    @pytest.mark.asyncio
    async def test_handle_async_stream_error_raises(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/missing", payload={"error": "not found"}, status=404)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            with pytest.raises(api_exceptions.HTTPStatusError):
                async for _ in backend.handle_async_stream("GET", "/missing", str):
                    pass
            await backend.aclose()
