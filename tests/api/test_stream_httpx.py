"""Tests for streaming with real HttpxHTTPBackend using respx mocks.

This test file mirrors test_stream.py but uses the real HttpxHTTPBackend
instead of FakeHTTPBackend to ensure the httpx streaming methods are tested.
"""

from __future__ import annotations

from typing import AsyncIterator, Iterator

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api.exceptions import HTTPStatusError

BASE_URL = "https://api.example.com"


class Token(BaseModel):
    text: str


class RequestData(BaseModel):
    """Test model for POST request data."""

    prompt: str
    max_tokens: int


class TestHttpxAsyncStreaming:
    """Test async streaming with HttpxHTTPBackend using respx."""

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_async_iterator_pydantic_model(self, respx_mock: MockRouter):
        """Test async streaming with Pydantic model hydration."""

        async def stream_content():
            yield b'{"text": "hello"}\n\n{"text": "world"}\n\n{"text": "test"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/events").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
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
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_async_iterator_dict(self, respx_mock: MockRouter):
        """Test async streaming with dict hydration."""

        async def stream_content():
            yield b'{"key": "value1"}\n\n{"key": "value2"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/events").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_dicts(*, result: AsyncIterator[dict]) -> AsyncIterator[dict]:
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
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_async_iterator_str(self, respx_mock: MockRouter):
        """Test async streaming with string (no parsing)."""

        async def stream_content():
            yield b"hello\n\nworld\n\n"

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/events").mock(side_effect=streaming_side_effect)
        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_text(*, result: AsyncIterator[str]) -> AsyncIterator[str]:
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
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_skips_empty_lines(self, respx_mock: MockRouter):
        """Test async streaming skips empty lines."""

        async def stream_content():
            yield b'{"text": "first"}\n\n\n\n\n\n{"text": "second"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/events").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        tokens = []
        async for token in await stream_tokens():
            tokens.append(token)

        assert len(tokens) == 2
        assert tokens[0].text == "first"
        assert tokens[1].text == "second"

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_error_response_raises(self, respx_mock: MockRouter):
        """Test async streaming raises on error responses."""
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                404,
                content=b"Not Found",
                headers={"content-type": "text/plain"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            async for _ in await stream_tokens():
                pass

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_post_with_data_parameter(self, respx_mock: MockRouter):
        """Test async streaming POST request with data payload."""

        async def stream_content():
            yield b'{"text": "response1"}\n\n{"text": "response2"}\n\n{"text": "response3"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.post("/generate").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.post("/generate", streaming_response=True)
        async def generate_stream(*, data: RequestData, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
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
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_stream_with_response_parser(self, respx_mock: MockRouter):
        """Test async streaming with custom response_parser."""

        async def stream_content():
            yield b"line1,data1\n\nline2,data2\n\nline3,data3\n\n"

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/events").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def custom_parser(line: str) -> dict:
            parts = line.split(",")
            return {"key": parts[0], "value": parts[1]}

        @client.get("/events", streaming_response=True, response_parser=custom_parser)
        async def stream_custom(*, result: AsyncIterator[dict]) -> AsyncIterator[dict]:
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

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_iterator_pydantic_model(self, respx_mock: MockRouter):
        """Test sync streaming with Pydantic model hydration."""
        stream = httpx.ByteStream(b'{"text": "hello"}\n\n{"text": "world"}\n\n')
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                200,
                stream=stream,
                headers={"content-type": "text/event-stream"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        tokens = []
        for token in stream_tokens():
            tokens.append(token)

        assert len(tokens) == 2
        assert all(isinstance(t, Token) for t in tokens)
        assert tokens[0].text == "hello"
        assert tokens[1].text == "world"

        client.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_iterator_dict(self, respx_mock: MockRouter):
        """Test sync streaming with dict hydration."""
        stream = httpx.ByteStream(b'{"key": "value1"}\n\n{"key": "value2"}\n\n')
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                200,
                stream=stream,
                headers={"content-type": "text/event-stream"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_dicts(*, result: Iterator[dict]) -> Iterator[dict]:
            return result

        items = []
        for item in stream_dicts():
            items.append(item)

        assert len(items) == 2
        assert all(isinstance(i, dict) for i in items)
        assert items[0]["key"] == "value1"
        assert items[1]["key"] == "value2"

        client.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_iterator_str(self, respx_mock: MockRouter):
        """Test sync streaming with string (no parsing)."""
        stream = httpx.ByteStream(b"hello\n\nworld\n\n")
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                200,
                stream=stream,
                headers={"content-type": "text/event-stream"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_text(*, result: Iterator[str]) -> Iterator[str]:
            return result

        lines = []
        for line in stream_text():
            lines.append(line)

        assert len(lines) == 2
        assert all(isinstance(line_item, str) for line_item in lines)
        assert lines[0] == "hello"
        assert lines[1] == "world"

        client.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_with_response_parser(self, respx_mock: MockRouter):
        """Test sync streaming with custom response_parser."""
        stream = httpx.ByteStream(b"a:1\n\nb:2\n\n")
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                200,
                stream=stream,
                headers={"content-type": "text/event-stream"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def custom_parser(line: str) -> dict:
            parts = line.split(":")
            return {"letter": parts[0], "number": int(parts[1])}

        @client.get("/events", streaming_response=True, response_parser=custom_parser)
        def stream_custom(*, result: Iterator[dict]) -> Iterator[dict]:
            return result

        items = []
        for item in stream_custom():
            items.append(item)

        assert len(items) == 2
        assert items[0] == {"letter": "a", "number": 1}
        assert items[1] == {"letter": "b", "number": 2}

        client.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_error_response_raises(self, respx_mock: MockRouter):
        """Test sync streaming raises on error responses."""
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                404,
                content=b"Not Found",
                headers={"content-type": "text/plain"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_stream_sync_500_error_response_raises(self, respx_mock: MockRouter):
        """Test sync streaming raises on 500 error."""
        respx_mock.get("/events").mock(
            return_value=httpx.Response(
                500,
                content=b"Internal Server Error",
                headers={"content-type": "text/plain"},
            )
        )

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()


class TestSSEFormatStreaming:
    """Test actual Server-Sent Events format streaming."""

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_sse_format_with_data_prefix(self, respx_mock: MockRouter):
        """Test streaming SSE format with 'data:' prefix using response_parser."""

        async def stream_sse_content():
            # Real SSE format with data: prefix
            yield b'data: {"role": "assistant", "content": "Hello"}\n\n'
            yield b'data: {"role": "assistant", "content": "How"}\n\n'
            yield b'data: {"role": "assistant", "content": "are you?"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_sse_content(), headers={"content-type": "text/event-stream"})

        respx_mock.post("/chat/stream").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        # Use the exact parse_sse from our documentation
        def parse_sse(line: str) -> dict | None:
            """Parse SSE format: extracts data from 'data: {json}' lines."""
            if line.startswith("data: "):
                import json

                json_str = line[6:]  # Remove 'data: ' prefix
                return json.loads(json_str)
            # Skip other SSE fields (event:, id:, retry:, comments)
            return None

        @client.post("/chat/stream", streaming_response=True, response_parser=parse_sse)
        async def stream_chat(*, data: dict, result: AsyncIterator[dict | None]) -> AsyncIterator[dict | None]:
            return result

        messages = []
        async for message in await stream_chat(data={"prompt": "Hi"}):
            if message:  # Skip None values
                messages.append(message)

        assert len(messages) == 3
        assert messages[0] == {"role": "assistant", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "How"}
        assert messages[2] == {"role": "assistant", "content": "are you?"}

        await client.aclose()

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_sse_format_with_mixed_fields(self, respx_mock: MockRouter):
        """Test SSE format with data, event, id, and comment lines."""

        async def stream_sse_content():
            # Mix of SSE fields - only data: lines should be parsed
            yield b": comment line\n"
            yield b"event: user-connected\n"
            yield b'data: {"user": "alice"}\n\n'
            yield b"id: 123\n"
            yield b'data: {"user": "bob"}\n\n'
            yield b"retry: 10000\n"
            yield b'data: {"user": "charlie"}\n\n'

        async def streaming_side_effect(request):
            return httpx.Response(200, stream=stream_sse_content(), headers={"content-type": "text/event-stream"})

        respx_mock.get("/users/stream").mock(side_effect=streaming_side_effect)

        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def parse_sse(line: str) -> dict | None:
            if line.startswith("data: "):
                import json

                return json.loads(line[6:])
            return None

        @client.get("/users/stream", streaming_response=True, response_parser=parse_sse)
        async def stream_users(*, result: AsyncIterator[dict | None]) -> AsyncIterator[dict | None]:
            return result

        users = []
        async for user in await stream_users():
            if user:  # Filter out None values
                users.append(user)

        # Should only get the 3 data: lines, not event:, id:, retry:, or comments
        assert len(users) == 3
        assert users[0] == {"user": "alice"}
        assert users[1] == {"user": "bob"}
        assert users[2] == {"user": "charlie"}

        await client.aclose()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_sse_sync_format(self, respx_mock: MockRouter):
        """Test sync SSE format streaming."""
        # Real SSE format
        stream = httpx.ByteStream(b'data: {"status": "processing"}\n\ndata: {"status": "complete"}\n\n')
        respx_mock.get("/status").mock(
            return_value=httpx.Response(
                200,
                stream=stream,
                headers={"content-type": "text/event-stream"},
            )
        )
        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        def parse_sse(line: str) -> dict | None:
            if line.startswith("data: "):
                import json

                return json.loads(line[6:])
            return None

        @client.get("/status", streaming_response=True, response_parser=parse_sse)
        def stream_status(*, result: Iterator[dict | None]) -> Iterator[dict | None]:
            return result

        statuses = []
        for status in stream_status():
            if status:
                statuses.append(status)

        assert len(statuses) == 2
        assert statuses[0] == {"status": "processing"}
        assert statuses[1] == {"status": "complete"}

        client.close()
