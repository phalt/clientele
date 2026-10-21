"""Tests for the requests HTTP backend."""

import json
import time
import typing

import pytest
import responses as responses_lib

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import requests_backend

BASE_URL = "https://api.example.com"


class TestRequestsHTTPBackend:
    def test_build_client_applies_headers_and_verify(self):
        backend = requests_backend.RequestsHTTPBackend(
            base_url=BASE_URL,
            headers={"Authorization": "Bearer token"},
            verify=False,
        )
        session = backend.build_client()
        assert "Authorization" in session.headers
        assert session.verify is False
        backend.close()

    def test_client_reuse(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_client()
        s2 = backend.build_client()
        assert s1 is s2
        backend.close()

    def test_close_clears_client(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        backend.build_client()
        assert backend._sync_client is not None
        backend.close()
        assert backend._sync_client is None

    def test_close_is_idempotent(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        backend.close()
        backend.close()

    @pytest.mark.asyncio
    async def test_aclose_is_noop(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        await backend.aclose()

    def test_build_async_client_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.build_async_client()

    @pytest.mark.asyncio
    async def test_send_async_request_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            await backend.send_async_request("GET", "/get")

    def test_open_async_stream_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.open_async_stream("GET", "/stream")

    def test_from_config(self):
        config = api_config.BaseConfig(
            base_url=BASE_URL,
            headers={"X-API-Key": "secret"},
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        )
        backend = requests_backend.RequestsHTTPBackend.from_config(config)
        assert backend.base_url == BASE_URL
        assert backend.headers == {"X-API-Key": "secret"}
        assert backend.timeout == 30.0
        assert backend.follow_redirects is True
        assert backend.verify is False

    def test_full_url_strips_double_slash(self):
        backend = requests_backend.RequestsHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"

    def test_full_url_absolute_unchanged(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        assert backend._full_url("https://other.example.com/path") == "https://other.example.com/path"

    @responses_lib.activate
    def test_send_sync_request(self):
        responses_lib.get(f"{BASE_URL}/users/1", json={"id": 1, "name": "Alice"}, status=200)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        result = backend.send_sync_request("GET", "/users/1")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}
        assert result.request_method == "GET"
        assert result.request_url == f"{BASE_URL}/users/1"

    @responses_lib.activate
    def test_send_sync_request_post_with_json(self):
        responses_lib.post(f"{BASE_URL}/items", json={"id": 99}, status=201)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        result = backend.send_sync_request("POST", "/items", json={"name": "foo"})
        backend.close()

        assert result.status_code == 201
        body = responses_lib.calls[0].request.body
        assert body is not None
        assert json.loads(body) == {"name": "foo"}

    @responses_lib.activate
    def test_send_sync_request_passes_default_headers(self):
        responses_lib.get(f"{BASE_URL}/me", json={}, status=200)

        backend = requests_backend.RequestsHTTPBackend(
            base_url=BASE_URL,
            headers={"Authorization": "Bearer token"},
        )
        backend.send_sync_request("GET", "/me")
        backend.close()

        sent = responses_lib.calls[0].request
        assert sent.headers is not None
        assert "Bearer token" in sent.headers.get("Authorization", "")

    @responses_lib.activate
    def test_open_sync_stream_reports_status_headers_and_raw_chunks(self):
        body = b"data: one\n\ndata: two\r\n\r\n"
        responses_lib.get(
            f"{BASE_URL}/stream",
            body=body,
            status=201,
            headers={"x-id": "7"},
            content_type="text/event-stream",
            stream=True,
        )

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with backend.open_sync_stream("GET", "/stream", params={"q": "1"}) as stream_response:
            assert stream_response.status_code == 201
            assert stream_response.headers["x-id"] == "7"
            assert stream_response.headers["Content-Type"] == "text/event-stream"
            assert stream_response.request_method == "GET"
            assert stream_response.request_url == f"{BASE_URL}/stream?q=1"
            assert b"".join(stream_response.chunks) == body
        backend.close()

    @responses_lib.activate
    def test_open_sync_stream_does_not_raise_on_error_status(self):
        responses_lib.get(f"{BASE_URL}/missing", json={"error": "not found"}, status=404)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with backend.open_sync_stream("GET", "/missing") as stream_response:
            assert stream_response.status_code == 404
            assert json.loads(b"".join(stream_response.chunks)) == {"error": "not found"}
        backend.close()

    @responses_lib.activate
    def test_open_sync_stream_closes_response_on_exit(self, monkeypatch: pytest.MonkeyPatch):
        import requests

        closed: list[requests.Response] = []
        original_close = requests.Response.close

        def recording_close(self: requests.Response) -> None:
            closed.append(self)
            original_close(self)

        monkeypatch.setattr(requests.Response, "close", recording_close)
        responses_lib.get(f"{BASE_URL}/stream", body=b"a\nb\n", stream=True)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with backend.open_sync_stream("GET", "/stream") as stream_response:
            next(iter(stream_response.chunks))
            assert closed == []
        assert len(closed) == 1
        backend.close()

    def test_open_sync_stream_yields_chunks_as_they_arrive(self, httpserver):
        """The first chunk must be readable while the server is still holding back the second."""
        import threading

        import werkzeug

        released = threading.Event()

        def handler(request: werkzeug.Request) -> werkzeug.Response:
            def body() -> typing.Iterator[bytes]:
                yield b"first\n"
                released.wait(timeout=5)
                yield b"second\n"

            return werkzeug.Response(body(), mimetype="application/x-ndjson")

        httpserver.expect_request("/slow").respond_with_handler(handler)
        backend = requests_backend.RequestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        try:
            with backend.open_sync_stream("GET", "/slow") as stream_response:
                chunks = iter(stream_response.chunks)
                started = time.monotonic()
                first = next(chunks)
                assert time.monotonic() - started < 2
                assert first.startswith(b"first\n")
                released.set()
                assert (first + b"".join(chunks)) == b"first\nsecond\n"
        finally:
            released.set()
            backend.close()

    def test_open_sync_stream_decodes_content_encoding(self, httpserver):
        import gzip

        body = b"".join(f'{{"n": {index}}}\n'.encode() for index in range(200))
        httpserver.expect_request("/gzip").respond_with_data(
            gzip.compress(body), content_type="application/x-ndjson", headers={"Content-Encoding": "gzip"}
        )
        backend = requests_backend.RequestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        with backend.open_sync_stream("GET", "/gzip") as stream_response:
            assert b"".join(stream_response.chunks) == body
        backend.close()

    def test_open_sync_stream_read_timeout_raises_requests_error(self, httpserver):
        import threading

        import requests
        import werkzeug

        released = threading.Event()

        def handler(request: werkzeug.Request) -> werkzeug.Response:
            def body() -> typing.Iterator[bytes]:
                yield b"first\n"
                released.wait(timeout=5)
                yield b"second\n"

            return werkzeug.Response(body(), mimetype="application/x-ndjson")

        httpserver.expect_request("/quiet").respond_with_handler(handler)
        backend = requests_backend.RequestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"), timeout=0.5)
        try:
            with backend.open_sync_stream("GET", "/quiet") as stream_response:
                chunks = iter(stream_response.chunks)
                next(chunks)
                with pytest.raises(requests.exceptions.ConnectionError):
                    next(chunks)
        finally:
            released.set()
            backend.close()

    def test_open_sync_stream_without_read1_falls_back_to_iter_content(self, httpserver, monkeypatch):
        """urllib3 releases before 2.3 have no HTTPResponse.read1."""
        import urllib3.response

        monkeypatch.delattr(urllib3.response.HTTPResponse, "read1")
        monkeypatch.delattr(urllib3.response.BaseHTTPResponse, "read1", raising=False)
        httpserver.expect_request("/stream").respond_with_data(b"a\n\nb\n", content_type="text/event-stream")
        backend = requests_backend.RequestsHTTPBackend(base_url=httpserver.url_for("").rstrip("/"))
        with backend.open_sync_stream("GET", "/stream") as stream_response:
            assert b"".join(stream_response.chunks) == b"a\n\nb\n"
        backend.close()

    @responses_lib.activate
    def test_stream_error_raises_when_called(self):
        responses_lib.get(f"{BASE_URL}/missing", json={"error": "not found"}, status=404)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        client = api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL, http_backend=backend))

        @client.get("/missing", streaming_response=True)
        def stream_lines(result: typing.Iterator[str]) -> typing.Iterator[str]:
            return result

        with pytest.raises(api_exceptions.HTTPStatusError) as exc_info:
            stream_lines()
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json() == {"error": "not found"}
        client.close()

    @responses_lib.activate
    def test_stream_keeps_line_separator_inside_json_record(self):
        body = '{"text": "before\u2028after"}\n{"text": "next"}\n'.encode()
        responses_lib.get(f"{BASE_URL}/stream", body=body, stream=True)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        client = api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL, http_backend=backend))

        @client.get("/stream", streaming_response=True)
        def stream_records(result: typing.Iterator[dict]) -> typing.Iterator[dict]:
            return result

        assert list(stream_records()) == [{"text": "before\u2028after"}, {"text": "next"}]
        client.close()

    @responses_lib.activate
    def test_full_clientele_integration(self):
        responses_lib.get(f"{BASE_URL}/users/1", json={"id": 1, "name": "Alice"}, status=200)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        config = api_config.BaseConfig(base_url=BASE_URL, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        def get_user(result: dict, user_id: int) -> dict:
            return result

        result = get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        client.close()

    def test_convert_to_response(self):
        import requests

        req = requests.PreparedRequest()
        req.method = "GET"
        req.url = "https://api.example.com/get"

        native = requests.Response()
        native.status_code = 201
        native._content = b"hello"
        native.encoding = "utf-8"
        native.request = req

        result = requests_backend.RequestsHTTPBackend.convert_to_response(native)
        assert result.status_code == 201
        assert result.content == b"hello"
        assert result.text == "hello"
        assert result.request_method == "GET"
        assert result.request_url == "https://api.example.com/get"
