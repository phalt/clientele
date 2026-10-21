"""Tests for HttpxHTTPBackend.open_sync_stream / open_async_stream.

Uses httpx2.MockTransport directly so the raw byte stream, status and headers
reach the backend exactly as the server sent them.
"""

from __future__ import annotations

import typing

import httpx2
import pytest

from clientele.http import backends, httpx_backend

BASE_URL = "https://api.example.com"


class RecordingSyncStream(httpx2.SyncByteStream):
    """Sync body that records how far it has been read and whether it was closed."""

    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.sent: list[bytes] = []
        self.closed = False

    def __iter__(self) -> typing.Iterator[bytes]:
        for chunk in self.chunks:
            self.sent.append(chunk)
            yield chunk

    def close(self) -> None:
        self.closed = True


class RecordingAsyncStream(httpx2.AsyncByteStream):
    """Async body that records how far it has been read and whether it was closed."""

    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.sent: list[bytes] = []
        self.closed = False

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        for chunk in self.chunks:
            self.sent.append(chunk)
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


def make_backend(
    status_code: int = 200,
    *,
    stream: httpx2.SyncByteStream | httpx2.AsyncByteStream | None = None,
    content: bytes = b"",
    headers: dict[str, str] | None = None,
    requests: list[httpx2.Request] | None = None,
) -> httpx_backend.HttpxHTTPBackend:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if requests is not None:
            requests.append(request)
        if stream is not None:
            return httpx2.Response(status_code, stream=stream, headers=headers)
        return httpx2.Response(status_code, content=content, headers=headers)

    return httpx_backend.HttpxHTTPBackend(
        client_options={"base_url": BASE_URL, "transport": httpx2.MockTransport(handler)}
    )


class TestOpenSyncStream:
    def test_reports_status_headers_and_request(self):
        backend = make_backend(201, content=b"x", headers={"content-type": "text/event-stream", "x-id": "7"})

        with backend.open_sync_stream("POST", "/events", params={"q": "1"}) as stream_response:
            assert isinstance(stream_response, backends.StreamResponse)
            assert stream_response.status_code == 201
            assert stream_response.headers["content-type"] == "text/event-stream"
            assert stream_response.headers["x-id"] == "7"
            assert stream_response.request_method == "POST"
            assert stream_response.request_url == f"{BASE_URL}/events?q=1"

    def test_chunks_are_raw_bytes_including_blank_lines(self):
        body = [b"data: a\n", b"\n", b"data: b\r\n\r\n"]
        backend = make_backend(stream=RecordingSyncStream(body))

        with backend.open_sync_stream("GET", "/events") as stream_response:
            assert b"".join(stream_response.chunks) == b"".join(body)

    def test_does_not_raise_on_error_status(self):
        backend = make_backend(404, content=b"Not Found")

        with backend.open_sync_stream("GET", "/missing") as stream_response:
            assert stream_response.status_code == 404
            assert b"".join(stream_response.chunks) == b"Not Found"

    def test_body_is_not_read_until_iterated(self):
        body = RecordingSyncStream([b"one\n", b"two\n"])
        backend = make_backend(stream=body)

        with backend.open_sync_stream("GET", "/events") as stream_response:
            assert body.sent == []
            assert next(iter(stream_response.chunks)) == b"one\n"
            assert body.sent == [b"one\n"]

    def test_response_is_closed_on_exit(self):
        body = RecordingSyncStream([b"one\n", b"two\n"])
        backend = make_backend(stream=body)

        with backend.open_sync_stream("GET", "/events") as stream_response:
            next(iter(stream_response.chunks))
            assert body.closed is False
        assert body.closed is True

    def test_passes_request_kwargs(self):
        requests: list[httpx2.Request] = []
        backend = make_backend(requests=requests)

        with backend.open_sync_stream("POST", "/events", headers={"x-a": "b"}, json={"k": 1}):
            pass

        assert requests[0].headers["x-a"] == "b"
        assert requests[0].content == b'{"k":1}'


class TestOpenAsyncStream:
    @pytest.mark.asyncio
    async def test_reports_status_headers_and_request(self):
        backend = make_backend(201, content=b"x", headers={"x-id": "7"})

        async with backend.open_async_stream("GET", "/events") as stream_response:
            assert isinstance(stream_response, backends.AsyncStreamResponse)
            assert stream_response.status_code == 201
            assert stream_response.headers["x-id"] == "7"
            assert stream_response.request_method == "GET"
            assert stream_response.request_url == f"{BASE_URL}/events"

    @pytest.mark.asyncio
    async def test_chunks_are_raw_bytes_including_blank_lines(self):
        body = [b"data: a\n", b"\n", b"data: b\r\n\r\n"]
        backend = make_backend(stream=RecordingAsyncStream(body))

        async with backend.open_async_stream("GET", "/events") as stream_response:
            assert b"".join([chunk async for chunk in stream_response.chunks]) == b"".join(body)

    @pytest.mark.asyncio
    async def test_does_not_raise_on_error_status(self):
        backend = make_backend(500, content=b"boom")

        async with backend.open_async_stream("GET", "/events") as stream_response:
            assert stream_response.status_code == 500
            assert b"".join([chunk async for chunk in stream_response.chunks]) == b"boom"

    @pytest.mark.asyncio
    async def test_body_is_not_read_until_iterated(self):
        body = RecordingAsyncStream([b"one\n", b"two\n"])
        backend = make_backend(stream=body)

        async with backend.open_async_stream("GET", "/events") as stream_response:
            assert body.sent == []
            assert await anext(aiter(stream_response.chunks)) == b"one\n"
            assert body.sent == [b"one\n"]

    @pytest.mark.asyncio
    async def test_response_is_closed_on_exit(self):
        body = RecordingAsyncStream([b"one\n", b"two\n"])
        backend = make_backend(stream=body)

        async with backend.open_async_stream("GET", "/events") as stream_response:
            await anext(aiter(stream_response.chunks))
            assert body.closed is False
        assert body.closed is True


class TestStreamResponseToResponse:
    def test_builds_buffered_response(self):
        stream_response = backends.StreamResponse(
            status_code=404,
            headers={"content-type": "text/plain; charset=utf-8"},
            request_method="GET",
            request_url=f"{BASE_URL}/x",
            chunks=iter(()),
        )

        response = stream_response.to_response(b"Not Found")

        assert response.status_code == 404
        assert response.headers == {"content-type": "text/plain; charset=utf-8"}
        assert response.content == b"Not Found"
        assert response.text == "Not Found"
        assert response.request_method == "GET"
        assert response.request_url == f"{BASE_URL}/x"

    def test_text_uses_declared_charset(self):
        stream_response = backends.AsyncStreamResponse(
            status_code=500,
            headers={"Content-Type": "text/plain; charset=latin-1"},
            request_method="GET",
            request_url="",
            chunks=typing.cast(typing.AsyncIterator[bytes], None),
        )

        assert stream_response.to_response("café".encode("latin-1")).text == "café"

    def test_undecodable_text_is_replaced_not_raised(self):
        stream_response = backends.StreamResponse(
            status_code=500, headers={}, request_method="GET", request_url="", chunks=iter(())
        )

        assert stream_response.to_response(b"\xffok").text == "�ok"
