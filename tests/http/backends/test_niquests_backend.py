"""Tests for the niquests HTTP backend."""

import json
import threading
import time
import typing

import pytest
import werkzeug

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import niquests_backend

BASE_URL = "https://api.example.com"


class SlowBody:
    """A werkzeug handler that sends one line, then waits until released before sending the next."""

    def __init__(self) -> None:
        self.released = threading.Event()

    def __call__(self, request: werkzeug.Request) -> werkzeug.Response:
        def body() -> typing.Iterator[bytes]:
            yield b"first\n"
            self.released.wait(timeout=5)
            yield b"second\n"

        return werkzeug.Response(body(), mimetype="application/x-ndjson")


RAW_BODY = b"data: one\n\ndata: two\r\n\r\n"


class TestNiquestsHTTPBackendSync:
    def test_build_client_returns_session(self):
        import niquests

        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        session = backend.build_client()
        assert isinstance(session, niquests.Session)
        backend.close()

    def test_build_client_reuse(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_client()
        s2 = backend.build_client()
        assert s1 is s2
        backend.close()

    def test_close_clears_client(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        backend.build_client()
        assert backend._sync_client is not None
        backend.close()
        assert backend._sync_client is None

    def test_close_is_idempotent(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        backend.close()
        backend.close()

    def test_from_config(self):
        config = api_config.BaseConfig(
            base_url=BASE_URL,
            headers={"X-API-Key": "secret"},
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        )
        backend = niquests_backend.NiquestsHTTPBackend.from_config(config)
        assert backend.base_url == BASE_URL
        assert backend.headers == {"X-API-Key": "secret"}
        assert backend.timeout == 30.0
        assert backend.follow_redirects is True
        assert backend.verify is False

    def test_full_url_strips_double_slash(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"

    def test_full_url_absolute_unchanged(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        assert backend._full_url("https://other.example.com/path") == "https://other.example.com/path"

    def test_send_sync_request(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("GET", "/users/1")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}
        assert result.request_method == "GET"
        assert result.request_url == f"{httpserver.url_for('').rstrip('/')}/users/1"

    def test_send_sync_request_post_with_json(self, httpserver):
        httpserver.expect_request("/items", method="POST").respond_with_json({"id": 99}, status=201)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("POST", "/items", json={"name": "foo"})
        backend.close()

        assert result.status_code == 201

    def test_send_sync_request_passes_default_headers(self, httpserver):
        httpserver.expect_request(
            "/me",
            headers={"Authorization": "Bearer token"},
        ).respond_with_json({}, status=200)

        backend = niquests_backend.NiquestsHTTPBackend(
            base_url=httpserver.url_for(""),
            headers={"Authorization": "Bearer token"},
        )
        backend.send_sync_request("GET", "/me")
        backend.close()

    def test_open_sync_stream_reports_status_headers_and_raw_chunks(self, httpserver):
        httpserver.expect_request("/stream").respond_with_data(
            RAW_BODY, status=201, content_type="text/event-stream", headers={"x-id": "7"}
        )

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        with backend.open_sync_stream("GET", "/stream") as stream_response:
            assert stream_response.status_code == 201
            assert stream_response.headers["x-id"] == "7"
            assert stream_response.headers["Content-Type"].startswith("text/event-stream")
            assert stream_response.request_method == "GET"
            assert stream_response.request_url == httpserver.url_for("/stream")
            assert b"".join(stream_response.chunks) == RAW_BODY
        backend.close()

    def test_open_sync_stream_does_not_raise_on_error_status(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        with backend.open_sync_stream("GET", "/missing") as stream_response:
            assert stream_response.status_code == 404
            assert json.loads(b"".join(stream_response.chunks)) == {"error": "not found"}
        backend.close()

    def test_open_sync_stream_yields_chunks_as_they_arrive(self, httpserver):
        slow = SlowBody()
        httpserver.expect_request("/slow").respond_with_handler(slow)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        try:
            with backend.open_sync_stream("GET", "/slow") as stream_response:
                chunks = iter(stream_response.chunks)
                started = time.monotonic()
                first = next(chunks)
                assert time.monotonic() - started < 2
                assert first.startswith(b"first\n")
                slow.released.set()
                assert first + b"".join(chunks) == b"first\nsecond\n"
        finally:
            slow.released.set()
            backend.close()

    def test_stream_error_raises_when_called(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        client = api_client.APIClient(config=api_config.BaseConfig(base_url=base_url, http_backend=backend))

        @client.get("/missing", streaming_response=True)
        def stream_lines(result: typing.Iterator[str]) -> typing.Iterator[str]:
            return result

        with pytest.raises(api_exceptions.HTTPStatusError) as exc_info:
            stream_lines()
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json() == {"error": "not found"}
        client.close()

    def test_stream_keeps_line_separator_inside_json_record(self, httpserver):
        httpserver.expect_request("/stream").respond_with_data(
            '{"text": "before\u2028after"}\n{"text": "next"}\n'.encode(), content_type="application/x-ndjson"
        )

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        client = api_client.APIClient(config=api_config.BaseConfig(base_url=base_url, http_backend=backend))

        @client.get("/stream", streaming_response=True)
        def stream_records(result: typing.Iterator[dict]) -> typing.Iterator[dict]:
            return result

        assert list(stream_records()) == [{"text": "before\u2028after"}, {"text": "next"}]
        client.close()

    def test_full_clientele_integration(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        config = api_config.BaseConfig(base_url=base_url, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        def get_user(result: dict, user_id: int) -> dict:
            return result

        result = get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        client.close()

    def test_convert_to_response_from_real_response(self, httpserver):
        httpserver.expect_request("/ping").respond_with_json({"ok": True})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("GET", "/ping")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"ok": True}
        assert result.request_method == "GET"


class TestNiquestsHTTPBackendAsync:
    def test_build_async_client_returns_async_session(self):
        import niquests

        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        session = backend.build_async_client()
        assert isinstance(session, niquests.AsyncSession)

    def test_build_async_client_reuse(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_async_client()
        s2 = backend.build_async_client()
        assert s1 is s2

    @pytest.mark.asyncio
    async def test_aclose_clears_client(self, httpserver):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        backend.build_async_client()
        assert backend._async_client is not None
        await backend.aclose()
        assert backend._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_is_idempotent(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        await backend.aclose()
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_send_async_request(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = await backend.send_async_request("GET", "/users/1")
        await backend.aclose()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_send_async_request_post(self, httpserver):
        httpserver.expect_request("/items", method="POST").respond_with_json({"id": 99}, status=201)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = await backend.send_async_request("POST", "/items", json={"name": "foo"})
        await backend.aclose()

        assert result.status_code == 201

    @pytest.mark.asyncio
    async def test_open_async_stream_reports_status_headers_and_raw_chunks(self, httpserver):
        httpserver.expect_request("/stream").respond_with_data(
            RAW_BODY, status=201, content_type="text/event-stream", headers={"x-id": "7"}
        )

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        async with backend.open_async_stream("GET", "/stream") as stream_response:
            assert stream_response.status_code == 201
            assert stream_response.headers["x-id"] == "7"
            assert stream_response.request_method == "GET"
            assert stream_response.request_url == httpserver.url_for("/stream")
            assert b"".join([chunk async for chunk in stream_response.chunks]) == RAW_BODY
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_open_async_stream_yields_chunks_as_they_arrive(self, httpserver):
        slow = SlowBody()
        httpserver.expect_request("/slow").respond_with_handler(slow)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        try:
            async with backend.open_async_stream("GET", "/slow") as stream_response:
                chunks = aiter(stream_response.chunks)
                started = time.monotonic()
                first = await anext(chunks)
                assert time.monotonic() - started < 2
                assert first.startswith(b"first\n")
                slow.released.set()
                assert first + b"".join([chunk async for chunk in chunks]) == b"first\nsecond\n"
        finally:
            slow.released.set()
            await backend.aclose()

    @pytest.mark.asyncio
    async def test_full_clientele_integration(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        config = api_config.BaseConfig(base_url=base_url, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        async def get_user(result: dict, user_id: int) -> dict:
            return result

        result = await get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        await client.aclose()

    @pytest.mark.asyncio
    async def test_open_async_stream_does_not_raise_on_error_status(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        async with backend.open_async_stream("GET", "/missing") as stream_response:
            assert stream_response.status_code == 404
            assert json.loads(b"".join([chunk async for chunk in stream_response.chunks])) == {"error": "not found"}
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_stream_error_raises_when_awaited(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        client = api_client.APIClient(config=api_config.BaseConfig(base_url=base_url, http_backend=backend))

        @client.get("/missing", streaming_response=True)
        async def stream_lines(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
            return result

        with pytest.raises(api_exceptions.HTTPStatusError) as exc_info:
            await stream_lines()
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json() == {"error": "not found"}
        await client.aclose()
