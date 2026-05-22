"""Tests for the aiohttp HTTP backend."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import aiohttp_backend

BASE_URL = "https://api.example.com"


def _make_mock_response(
    *,
    status: int = 200,
    body: bytes = b'{"ok": true}',
    headers: dict | None = None,
    method: str = "GET",
    url: str = "https://api.example.com/get",
) -> MagicMock:
    mock = MagicMock()
    mock.status = status
    mock._body = body
    mock.headers = headers or {"content-type": "application/json"}
    mock.method = method
    mock.url = url
    mock.read = AsyncMock(return_value=body)
    mock.closed = False
    return mock


class TestAiohttpHTTPBackend:
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
        backend.close()  # should not raise

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

    def test_convert_to_response(self):
        native = _make_mock_response(status=201, body=b"hello")
        result = aiohttp_backend.AiohttpHTTPBackend.convert_to_response(native)
        assert result.status_code == 201
        assert result.content == b"hello"
        assert result.request_method == "GET"
        assert result.request_url == "https://api.example.com/get"

    def test_convert_to_response_empty_body(self):
        native = _make_mock_response(body=b"")
        native._body = None
        result = aiohttp_backend.AiohttpHTTPBackend.convert_to_response(native)
        assert result.content == b""

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

    @pytest.mark.asyncio
    async def test_send_async_request(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(status=200, body=b'{"id": 1}')

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        backend._async_client = mock_session

        result = await backend.send_async_request("GET", "/get")

        assert result.status_code == 200
        assert result.content == b'{"id": 1}'
        mock_response.read.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_async_stream_yields_lines(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(status=200)

        lines = [b"line one\n", b"line two\n", b""]
        mock_response.content = MagicMock()
        mock_response.content.readline = AsyncMock(side_effect=lines)

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        backend._async_client = mock_session

        results = []
        async for item in backend.handle_async_stream("GET", "/stream", str, response_parser=lambda x: x):
            results.append(item)

        assert results == ["line one", "line two"]

    @pytest.mark.asyncio
    async def test_handle_async_stream_error_raises(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(status=404, body=b"not found")

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        backend._async_client = mock_session

        with pytest.raises(api_exceptions.HTTPStatusError):
            async for _ in backend.handle_async_stream("GET", "/missing", str):
                pass
