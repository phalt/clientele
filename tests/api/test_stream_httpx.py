"""Tests for streaming with real HttpxHTTPBackend using respx mocks.

This test file mirrors test_stream.py but uses the real HttpxHTTPBackend
instead of FakeHTTPBackend to ensure the httpx streaming methods are tested.
"""

from __future__ import annotations

from typing import AsyncIterator, Iterator

import httpx  # required for respx stream type compatibility
import pytest
import respx
from pydantic import BaseModel

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api.exceptions import HTTPStatusError

BASE_URL = "https://api.example.com"


class AsyncBytesStream(httpx.AsyncByteStream):
    """Async byte stream that yields pre-defined chunks, one per iteration."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk


class SyncBytesStream(httpx.SyncByteStream):
    """Sync byte stream that yields pre-defined chunks, one per iteration."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    def __iter__(self) -> Iterator[bytes]:
        yield from self._chunks


class Token(BaseModel):
    text: str


class RequestData(BaseModel):
    """Test model for POST request data."""

    prompt: str
    max_tokens: int


class TestHttpxAsyncStreaming:
    """Test async streaming with HttpxHTTPBackend using respx."""

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_async_iterator_pydantic_model(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming with Pydantic model hydration — each item arrives as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=AsyncBytesStream([b'{"text": "hello"}\n\n', b'{"text": "world"}\n\n', b'{"text": "test"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        tokens = []
        async for token in await stream_tokens():
            tokens.append(token)

        assert len(tokens) == 3
        assert all(isinstance(t, Token) for t in tokens)
        assert tokens[0].text == "hello"
        assert tokens[1].text == "world"
        assert tokens[2].text == "test"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_async_iterator_dict(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming with dict hydration — each item arrives as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=AsyncBytesStream([b'{"key": "value1"}\n\n', b'{"key": "value2"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_dicts(result: AsyncIterator[dict]) -> AsyncIterator[dict]:
            return result

        items = []
        async for item in await stream_dicts():
            items.append(item)

        assert len(items) == 2
        assert all(isinstance(i, dict) for i in items)
        assert items[0]["key"] == "value1"
        assert items[1]["key"] == "value2"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_async_iterator_str(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming with string (no parsing) — each item arrives as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=AsyncBytesStream([b"hello\n\n", b"world\n\n"]),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_text(result: AsyncIterator[str]) -> AsyncIterator[str]:
            return result

        lines = []
        async for line in await stream_text():
            lines.append(line)

        assert len(lines) == 2
        assert all(isinstance(line_item, str) for line_item in lines)
        assert lines[0] == "hello"
        assert lines[1] == "world"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_skips_empty_lines(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming skips empty lines between chunks."""
        httpx2_mock.get("/events").respond(
            200,
            stream=AsyncBytesStream([b'{"text": "first"}\n\n', b"\n\n\n\n", b'{"text": "second"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        tokens = []
        async for token in await stream_tokens():
            tokens.append(token)

        assert len(tokens) == 2
        assert tokens[0].text == "first"
        assert tokens[1].text == "second"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_error_response_raises(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming raises on error responses."""
        httpx2_mock.get("/events").respond(404, content=b"Not Found", headers={"content-type": "text/plain"})

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            async for _ in await stream_tokens():
                pass

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_post_with_data_parameter(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming POST request with data payload — each item as a separate chunk."""
        httpx2_mock.post("/generate").respond(
            200,
            stream=AsyncBytesStream(
                [b'{"text": "response1"}\n\n', b'{"text": "response2"}\n\n', b'{"text": "response3"}\n\n']
            ),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.post("/generate", streaming_response=True)
        async def generate_stream(result: AsyncIterator[Token], data: RequestData) -> AsyncIterator[Token]:
            return result

        request_data = RequestData(prompt="Hello world", max_tokens=100)
        tokens = []
        async for token in await generate_stream(data=request_data):
            tokens.append(token)

        assert len(tokens) == 3
        assert all(isinstance(t, Token) for t in tokens)
        assert tokens[0].text == "response1"
        assert tokens[1].text == "response2"
        assert tokens[2].text == "response3"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_stream_with_response_parser(self, httpx2_mock: respx.Router) -> None:
        """Test async streaming with custom response_parser — each item as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=AsyncBytesStream([b"line1,data1\n\n", b"line2,data2\n\n", b"line3,data3\n\n"]),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def custom_parser(line: str) -> dict:
            parts = line.split(",")
            return {"key": parts[0], "value": parts[1]}

        @client.get("/events", streaming_response=True, response_parser=custom_parser)
        async def stream_custom(result: AsyncIterator[dict]) -> AsyncIterator[dict]:
            return result

        items = []
        async for item in await stream_custom():
            items.append(item)

        assert len(items) == 3
        assert items[0] == {"key": "line1", "value": "data1"}
        assert items[1] == {"key": "line2", "value": "data2"}
        assert items[2] == {"key": "line3", "value": "data3"}

        await client.aclose()


class TestHttpxSyncStreaming:
    """Test sync streaming with HttpxHTTPBackend using respx."""

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_iterator_pydantic_model(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming with Pydantic model hydration — each item as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=SyncBytesStream([b'{"text": "hello"}\n\n', b'{"text": "world"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        tokens = []
        for token in stream_tokens():
            tokens.append(token)

        assert len(tokens) == 2
        assert all(isinstance(t, Token) for t in tokens)
        assert tokens[0].text == "hello"
        assert tokens[1].text == "world"

        client.close()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_iterator_dict(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming with dict hydration — each item as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=SyncBytesStream([b'{"key": "value1"}\n\n', b'{"key": "value2"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_dicts(result: Iterator[dict]) -> Iterator[dict]:
            return result

        items = []
        for item in stream_dicts():
            items.append(item)

        assert len(items) == 2
        assert all(isinstance(i, dict) for i in items)
        assert items[0]["key"] == "value1"
        assert items[1]["key"] == "value2"

        client.close()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_iterator_str(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming with string (no parsing) — each item as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=SyncBytesStream([b"hello\n\n", b"world\n\n"]),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_text(result: Iterator[str]) -> Iterator[str]:
            return result

        lines = []
        for line in stream_text():
            lines.append(line)

        assert len(lines) == 2
        assert all(isinstance(line_item, str) for line_item in lines)
        assert lines[0] == "hello"
        assert lines[1] == "world"

        client.close()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_with_response_parser(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming with custom response_parser — each item as a separate chunk."""
        httpx2_mock.get("/events").respond(
            200,
            stream=SyncBytesStream([b"a:1\n\n", b"b:2\n\n"]),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def custom_parser(line: str) -> dict:
            parts = line.split(":")
            return {"letter": parts[0], "number": int(parts[1])}

        @client.get("/events", streaming_response=True, response_parser=custom_parser)
        def stream_custom(result: Iterator[dict]) -> Iterator[dict]:
            return result

        items = []
        for item in stream_custom():
            items.append(item)

        assert len(items) == 2
        assert items[0] == {"letter": "a", "number": 1}
        assert items[1] == {"letter": "b", "number": 2}

        client.close()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_error_response_raises(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming raises on error responses."""
        httpx2_mock.get("/events").respond(404, content=b"Not Found", headers={"content-type": "text/plain"})

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_stream_sync_500_error_response_raises(self, httpx2_mock: respx.Router) -> None:
        """Test sync streaming raises on 500 error."""
        httpx2_mock.get("/events").respond(
            500, content=b"Internal Server Error", headers={"content-type": "text/plain"}
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()


class TestSSEFormatStreaming:
    """Test actual Server-Sent Events format streaming."""

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_sse_format_with_data_prefix(self, httpx2_mock: respx.Router) -> None:
        """Test streaming SSE format with 'data:' prefix — each event as a separate chunk."""
        httpx2_mock.post("/chat/stream").respond(
            200,
            stream=AsyncBytesStream(
                [
                    b'data: {"role": "assistant", "content": "Hello"}\n\n',
                    b'data: {"role": "assistant", "content": "How"}\n\n',
                    b'data: {"role": "assistant", "content": "are you?"}\n\n',
                ]
            ),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def parse_sse(line: str) -> dict | None:
            """Parse SSE format: extracts data from 'data: {json}' lines."""
            if line.startswith("data: "):
                import json

                return json.loads(line[6:])
            return None

        @client.post("/chat/stream", streaming_response=True, response_parser=parse_sse)
        async def stream_chat(result: AsyncIterator[dict | None], data: dict) -> AsyncIterator[dict | None]:
            return result

        messages = []
        async for message in await stream_chat(data={"prompt": "Hi"}):
            if message:
                messages.append(message)

        assert len(messages) == 3
        assert messages[0] == {"role": "assistant", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "How"}
        assert messages[2] == {"role": "assistant", "content": "are you?"}

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.httpx2(base_url=BASE_URL)
    async def test_sse_format_with_mixed_fields(self, httpx2_mock: respx.Router) -> None:
        """Test SSE format with data, event, id, and comment lines — each as a separate chunk."""
        httpx2_mock.get("/users/stream").respond(
            200,
            stream=AsyncBytesStream(
                [
                    b": comment line\n",
                    b"event: user-connected\n",
                    b'data: {"user": "alice"}\n\n',
                    b"id: 123\n",
                    b'data: {"user": "bob"}\n\n',
                    b"retry: 10000\n",
                    b'data: {"user": "charlie"}\n\n',
                ]
            ),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def parse_sse(line: str) -> dict | None:
            if line.startswith("data: "):
                import json

                return json.loads(line[6:])
            return None

        @client.get("/users/stream", streaming_response=True, response_parser=parse_sse)
        async def stream_users(result: AsyncIterator[dict | None]) -> AsyncIterator[dict | None]:
            return result

        users = []
        async for user in await stream_users():
            if user:
                users.append(user)

        assert len(users) == 3
        assert users[0] == {"user": "alice"}
        assert users[1] == {"user": "bob"}
        assert users[2] == {"user": "charlie"}

        await client.aclose()

    @pytest.mark.httpx2(base_url=BASE_URL)
    def test_sse_sync_format(self, httpx2_mock: respx.Router) -> None:
        """Test sync SSE format streaming — each event as a separate chunk."""
        httpx2_mock.get("/status").respond(
            200,
            stream=SyncBytesStream([b'data: {"status": "processing"}\n\n', b'data: {"status": "complete"}\n\n']),
            headers={"content-type": "text/event-stream"},
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def parse_sse(line: str) -> dict | None:
            if line.startswith("data: "):
                import json

                return json.loads(line[6:])
            return None

        @client.get("/status", streaming_response=True, response_parser=parse_sse)
        def stream_status(result: Iterator[dict | None]) -> Iterator[dict | None]:
            return result

        statuses = []
        for status in stream_status():
            if status:
                statuses.append(status)

        assert len(statuses) == 2
        assert statuses[0] == {"status": "processing"}
        assert statuses[1] == {"status": "complete"}

        client.close()
