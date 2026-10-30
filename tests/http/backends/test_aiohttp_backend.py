"""Tests for the aiohttp HTTP backend."""

import asyncio
import json
import threading
import time
import typing
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
import werkzeug
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

    def test_open_sync_stream_raises(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.open_sync_stream("GET", "/stream")

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

    def test_stream_timeout_limits_connecting_and_each_read(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL, timeout=2.0)
        assert backend.stream_timeout == aiohttp.ClientTimeout(total=None, connect=2.0, sock_read=2.0)

    def test_stream_timeout_none_means_no_limit(self):
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL, timeout=None)
        assert backend.stream_timeout == aiohttp.ClientTimeout(total=None, connect=None, sock_read=None)

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
    async def test_open_async_stream_reports_status_headers_and_raw_chunks(self):
        body = b"data: one\n\ndata: two\r\n\r\n"
        with aioresponses() as m:
            m.get(f"{BASE_URL}/stream", body=body, status=201, headers={"x-id": "7"})
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            async with backend.open_async_stream("GET", "/stream") as stream_response:
                assert stream_response.status_code == 201
                assert stream_response.headers["x-id"] == "7"
                assert stream_response.request_method == "GET"
                assert stream_response.request_url == f"{BASE_URL}/stream"
                assert b"".join([chunk async for chunk in stream_response.chunks]) == body
            await backend.aclose()

    @pytest.mark.asyncio
    async def test_open_async_stream_does_not_raise_on_error_status(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/missing", payload={"error": "not found"}, status=404)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            async with backend.open_async_stream("GET", "/missing") as stream_response:
                assert stream_response.status_code == 404
                body = b"".join([chunk async for chunk in stream_response.chunks])
                assert json.loads(body) == {"error": "not found"}
            await backend.aclose()

    @pytest.mark.asyncio
    async def test_stream_error_raises_when_awaited(self):
        with aioresponses() as m:
            m.get(f"{BASE_URL}/missing", payload={"error": "not found"}, status=404)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            client = api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL, http_backend=backend))

            @client.get("/missing", streaming_response=True)
            async def stream_lines(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
                return result

            with pytest.raises(api_exceptions.HTTPStatusError) as exc_info:
                await stream_lines()
            assert exc_info.value.response.status_code == 404
            assert exc_info.value.response.json() == {"error": "not found"}
            await client.aclose()

    @pytest.mark.asyncio
    async def test_stream_keeps_line_separator_inside_json_record(self):
        body = '{"text": "before\u2028after"}\n{"text": "next"}\n'.encode()
        with aioresponses() as m:
            m.get(f"{BASE_URL}/stream", body=body, status=200)
            backend = aiohttp_backend.AiohttpHTTPBackend(base_url=BASE_URL)
            client = api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL, http_backend=backend))

            @client.get("/stream", streaming_response=True)
            async def stream_records(result: typing.AsyncIterator[dict]) -> typing.AsyncIterator[dict]:
                return result

            assert [record async for record in await stream_records()] == [
                {"text": "before\u2028after"},
                {"text": "next"},
            ]
            await client.aclose()

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


def paced_handler(lines: int, every: float, released: threading.Event | None = None):
    """A werkzeug handler that sends `lines` short lines, `every` seconds apart.

    With `released`, it sends one line and then waits for the event before the rest.
    """

    def handler(request: werkzeug.Request) -> werkzeug.Response:
        def body() -> typing.Iterator[bytes]:
            for index in range(lines):
                yield f"line {index}\n".encode()
                if released is not None:
                    released.wait(timeout=5)
                else:
                    time.sleep(every)

        return werkzeug.Response(body(), mimetype="application/x-ndjson")

    return handler


class TestAiohttpStreamingOverSocket:
    """Real-socket stream behaviour: incremental delivery and read (not total) timeouts."""

    @pytest.mark.asyncio
    async def test_chunks_arrive_as_sent(self, httpserver):
        released = threading.Event()
        httpserver.expect_request("/slow").respond_with_handler(paced_handler(2, 0, released))
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        try:
            async with backend.open_async_stream("GET", "/slow") as stream_response:
                chunks = aiter(stream_response.chunks)
                started = time.monotonic()
                first = await anext(chunks)
                assert time.monotonic() - started < 2
                assert first.startswith(b"line 0\n")
                released.set()
                assert first + b"".join([chunk async for chunk in chunks]) == b"line 0\nline 1\n"
        finally:
            released.set()
            await backend.aclose()

    @pytest.mark.asyncio
    async def test_stream_longer_than_timeout_completes_while_data_flows(self, httpserver):
        """6 lines 0.25 s apart take about 1.5 s, three times the 0.5 s timeout."""
        httpserver.expect_request("/long").respond_with_handler(paced_handler(6, 0.25))
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=httpserver.url_for("").rstrip("/"), timeout=0.5)
        started = time.monotonic()
        async with backend.open_async_stream("GET", "/long") as stream_response:
            body = b"".join([chunk async for chunk in stream_response.chunks])
        assert time.monotonic() - started > 1.0
        assert body.count(b"\n") == 6
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_quiet_stream_times_out(self, httpserver):
        released = threading.Event()
        httpserver.expect_request("/quiet").respond_with_handler(paced_handler(2, 0, released))
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=httpserver.url_for("").rstrip("/"), timeout=0.5)
        try:
            async with backend.open_async_stream("GET", "/quiet") as stream_response:
                chunks = aiter(stream_response.chunks)
                await anext(chunks)
                with pytest.raises((asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
                    await anext(chunks)
        finally:
            released.set()
            await backend.aclose()

    @pytest.mark.asyncio
    async def test_non_stream_requests_keep_total_timeout(self, httpserver):
        """Only streams switch to a read timeout: a buffered request whose data keeps flowing
        (6 lines 0.25 s apart) still fails once the 0.5 s total timeout passes."""
        httpserver.expect_request("/long").respond_with_handler(paced_handler(6, 0.25))
        backend = aiohttp_backend.AiohttpHTTPBackend(base_url=httpserver.url_for("").rstrip("/"), timeout=0.5)
        with pytest.raises((asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
            await backend.send_async_request("GET", "/long")
        await backend.aclose()
