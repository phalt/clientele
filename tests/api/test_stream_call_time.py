"""Streaming through APIClient with the real httpx2 backend over httpx2.MockTransport.

Covers behaviour introduced by the byte-chunk stream contract: the request is
sent and its status checked when the decorated function is called, lines are
split by clientele rather than httpx2, and the response is closed afterwards.
"""

from __future__ import annotations

import typing
from typing import AsyncIterator, Iterator

import httpx2
import pytest
from pydantic import BaseModel

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api.exceptions import HTTPStatusError
from clientele.http import httpx_backend

BASE_URL = "https://api.example.com"


class Token(BaseModel):
    text: str


class Recorder:
    """MockTransport handler that records requests and serves a fixed response."""

    def __init__(
        self,
        status_code: int = 200,
        *,
        content: bytes = b"",
        stream: httpx2.SyncByteStream | httpx2.AsyncByteStream | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.stream = stream
        self.headers = headers
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        if self.stream is not None:
            return httpx2.Response(self.status_code, stream=self.stream, headers=self.headers)
        return httpx2.Response(self.status_code, content=self.content, headers=self.headers)


class ClosingSyncStream(httpx2.SyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.closed = False

    def __iter__(self) -> typing.Iterator[bytes]:
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


class ClosingAsyncStream(httpx2.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.closed = False

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        for chunk in self.chunks:
            yield chunk

    async def aclose(self) -> None:
        self.closed = True


def make_client(handler: Recorder) -> api_client.APIClient:
    backend = httpx_backend.HttpxHTTPBackend(
        client_options={"base_url": BASE_URL, "transport": httpx2.MockTransport(handler)}
    )
    return api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL, http_backend=backend))


class TestSyncStreamCallTime:
    def test_request_is_sent_when_called(self):
        handler = Recorder(content=b'{"text": "a"}\n')
        client = make_client(handler)

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        tokens = stream_tokens()
        assert len(handler.requests) == 1
        assert list(tokens) == [Token(text="a")]

    @pytest.mark.parametrize("status_code", [400, 404, 500, 503])
    def test_error_status_raises_on_call_not_iteration(self, status_code: int):
        handler = Recorder(status_code, content=b"Not Found", headers={"content-type": "text/plain", "x-req": "9"})
        client = make_client(handler)

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError) as exc_info:
            stream_tokens()

        error = exc_info.value
        assert error.response.status_code == status_code
        assert error.response.content == b"Not Found"
        assert error.response.text == "Not Found"
        assert error.response.headers["x-req"] == "9"
        assert error.response.request_url == f"{BASE_URL}/events"
        assert error.reason == f"HTTP {status_code}"

    def test_error_response_is_closed(self):
        body = ClosingSyncStream([b"nope"])
        client = make_client(Recorder(500, stream=body))

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[str]) -> Iterator[str]:
            return result

        with pytest.raises(HTTPStatusError):
            stream_tokens()
        assert body.closed is True

    def test_line_separator_in_json_string_stays_one_item(self):
        body = '{"text": "before after"}\n{"text": "next"}\n'.encode()
        client = make_client(Recorder(content=body))

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        assert list(stream_tokens()) == [Token(text="before after"), Token(text="next")]

    def test_lines_split_across_chunks(self):
        body = ClosingSyncStream([b'{"te', b'xt": "a"}\r', b"\n\n", b'{"text": "b"}'])
        client = make_client(Recorder(stream=body))

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        assert list(stream_tokens()) == [Token(text="a"), Token(text="b")]

    def test_response_is_closed_when_exhausted(self):
        body = ClosingSyncStream([b"a\n", b"b\n"])
        client = make_client(Recorder(stream=body))

        @client.get("/events", streaming_response=True)
        def stream_lines(result: Iterator[str]) -> Iterator[str]:
            return result

        assert list(stream_lines()) == ["a", "b"]
        assert body.closed is True

    def test_response_is_closed_when_iteration_stops_early(self):
        body = ClosingSyncStream([b"a\n", b"b\n"])
        client = make_client(Recorder(stream=body))

        @client.get("/events", streaming_response=True)
        def stream_lines(result: Iterator[str]) -> Iterator[str]:
            return result

        lines = stream_lines()
        assert next(lines) == "a"
        assert body.closed is False
        typing.cast(typing.Generator[str, None, None], lines).close()
        assert body.closed is True


class TestAsyncStreamCallTime:
    @pytest.mark.asyncio
    async def test_request_is_sent_when_awaited(self):
        handler = Recorder(content=b'{"text": "a"}\n')
        client = make_client(handler)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        tokens = await stream_tokens()
        assert len(handler.requests) == 1
        assert [token async for token in tokens] == [Token(text="a")]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [401, 500])
    async def test_error_status_raises_on_await_not_iteration(self, status_code: int):
        client = make_client(Recorder(status_code, content=b"denied", headers={"x-req": "9"}))

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(HTTPStatusError) as exc_info:
            await stream_tokens()

        assert exc_info.value.response.status_code == status_code
        assert exc_info.value.response.text == "denied"
        assert exc_info.value.response.headers["x-req"] == "9"

    @pytest.mark.asyncio
    async def test_error_response_is_closed(self):
        body = ClosingAsyncStream([b"nope"])
        client = make_client(Recorder(500, stream=body))

        @client.get("/events", streaming_response=True)
        async def stream_lines(result: AsyncIterator[str]) -> AsyncIterator[str]:
            return result

        with pytest.raises(HTTPStatusError):
            await stream_lines()
        assert body.closed is True

    @pytest.mark.asyncio
    async def test_line_separator_in_json_string_stays_one_item(self):
        body = '{"text": "before after"}\n'.encode()
        client = make_client(Recorder(content=body))

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        assert [token async for token in await stream_tokens()] == [Token(text="before after")]

    @pytest.mark.asyncio
    async def test_response_is_closed_when_exhausted(self):
        body = ClosingAsyncStream([b"a\n", b"b\n"])
        client = make_client(Recorder(stream=body))

        @client.get("/events", streaming_response=True)
        async def stream_lines(result: AsyncIterator[str]) -> AsyncIterator[str]:
            return result

        assert [line async for line in await stream_lines()] == ["a", "b"]
        assert body.closed is True

    @pytest.mark.asyncio
    async def test_response_is_closed_when_iteration_stops_early(self):
        body = ClosingAsyncStream([b"a\n", b"b\n"])
        client = make_client(Recorder(stream=body))

        @client.get("/events", streaming_response=True)
        async def stream_lines(result: AsyncIterator[str]) -> AsyncIterator[str]:
            return result

        lines = await stream_lines()
        assert await anext(lines) == "a"
        assert body.closed is False
        await typing.cast(typing.AsyncGenerator[str, None], lines).aclose()
        assert body.closed is True
