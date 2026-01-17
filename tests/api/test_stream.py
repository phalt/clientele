from __future__ import annotations

from typing import AsyncIterator, Iterator

import httpx
import pytest
import respx
from pydantic import BaseModel

from clientele.api import requests
from clientele.api.client import APIClient
from clientele.api.exceptions import HTTPStatusError


class Token(BaseModel):
    text: str


class RequestData(BaseModel):
    """Test model for POST request data."""

    prompt: str
    max_tokens: int


class TestStreamDecorators:
    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_async_iterator_pydantic_model(self):
        """Test SSE streaming with Pydantic model hydration."""

        async def mock_sse_stream():
            yield b'{"text": "hello"}\n\n'
            yield b'{"text": "world"}\n\n'
            yield b'{"text": "test"}\n\n'

        route = respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_async_iterator_dict(self):
        """Test SSE streaming with dict hydration."""

        async def mock_sse_stream():
            yield b'{"key": "value1"}\n\n'
            yield b'{"key": "value2"}\n\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_async_iterator_str(self):
        """Test SSE streaming with string (no parsing)."""

        async def mock_sse_stream():
            yield b"hello\n\n"
            yield b"world\n\n"

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    def test_sse_missing_streaming_type_raises(self):
        """Test that non-streaming result type raises error."""
        client = APIClient(base_url="http://localhost:8000")

        with pytest.raises(TypeError, match="must have a streaming result type"):

            @client.get("/events", streaming_response=True)
            async def bad_stream(*, result: Token) -> Token:  # NOT AsyncIterator!
                return result

    def test_sse_missing_inner_type_raises(self):
        """Test that AsyncIterator without inner type raises error."""
        client = APIClient(base_url="http://localhost:8000")

        with pytest.raises(TypeError, match="no inner type specified"):

            @client.get("/events", streaming_response=True)
            async def bad_stream(*, result: AsyncIterator) -> AsyncIterator:  # Missing [T]!
                return result

    def test_async_function_with_iterator_raises(self):
        """Test that async function with Iterator (not AsyncIterator) raises error."""
        client = APIClient(base_url="http://localhost:8000")

        with pytest.raises(TypeError, match="must use AsyncIterator, not Iterator"):

            @client.get("/events", streaming_response=True)
            async def bad_stream(*, result: Iterator[Token]) -> Iterator[Token]:  # Should be AsyncIterator!
                return result

    def test_sync_function_with_async_iterator_raises(self):
        """Test that sync function with AsyncIterator (not Iterator) raises error."""
        client = APIClient(base_url="http://localhost:8000")

        with pytest.raises(TypeError, match="must use Iterator, not AsyncIterator"):

            @client.get("/events", streaming_response=True)
            def bad_stream(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:  # Should be Iterator!
                return result

    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_skips_empty_lines(self):
        """Test SSE streaming skips empty lines."""

        async def mock_sse_stream():
            yield b'{"text": "first"}\n\n'
            yield b"\n"  # Empty line
            yield b"\n\n"  # More empty lines
            yield b'{"text": "second"}\n\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        tokens = []
        async for token in await stream_tokens():
            tokens.append(token)

        assert len(tokens) == 2
        assert tokens[0].text == "first"
        assert tokens[1].text == "second"

    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_error_response_raises(self):
        """Test SSE streaming raises on error responses."""
        respx.get("http://localhost:8000/events").mock(return_value=httpx.Response(404, text="Not Found"))

        client = APIClient(base_url="http://localhost:8000")

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            async for _ in await stream_tokens():
                pass

    @pytest.mark.asyncio
    @respx.mock
    async def test_sse_with_response_parameter(self):
        """Test SSE streaming with response parameter injection."""

        async def mock_sse_stream():
            yield b'{"text": "test"}\n\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        captured_response = None

        @client.get("/events", streaming_response=True)
        async def stream_with_response(
            *, result: AsyncIterator[Token], response: httpx.Response
        ) -> AsyncIterator[Token]:
            nonlocal captured_response
            captured_response = response
            return result

        tokens = []
        async for token in await stream_with_response():
            tokens.append(token)

        assert captured_response is not None
        assert captured_response.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_stream_post_with_data_parameter(self):
        """Test SSE streaming POST request with data payload."""

        async def mock_sse_stream():
            yield b'{"text": "response1"}\n\n'
            yield b'{"text": "response2"}\n\n'
            yield b'{"text": "response3"}\n\n'

        route = respx.post("http://localhost:8000/generate").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.post("/generate", streaming_response=True)
        async def generate_stream(*, data: RequestData, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        request_data = RequestData(prompt="Hello world", max_tokens=100)
        tokens = []
        async for token in await generate_stream(data=request_data):
            tokens.append(token)

        # Verify the streaming response was handled correctly
        assert len(tokens) == 3
        assert all(isinstance(t, Token) for t in tokens)
        assert tokens[0].text == "response1"
        assert tokens[1].text == "response2"
        assert tokens[2].text == "response3"

        # Verify the request was made and data was sent
        assert route.called
        assert route.calls.last.request.method == "POST"

        # Verify the data payload was sent correctly
        request_json = route.calls.last.request.content
        import json

        sent_data = json.loads(request_json)
        assert sent_data["prompt"] == "Hello world"
        assert sent_data["max_tokens"] == 100

    def test_stream_cannot_use_response_map(self):
        """Test that SSE decorators cannot use response_map."""

        async def dummy_func(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(TypeError, match="cannot use response_map"):
            requests.build_request_context("GET", "/events", dummy_func, response_map={200: Token}, streaming=True)

    @pytest.mark.asyncio
    @respx.mock
    async def test_stream_with_response_parser(self):
        """Test SSE streaming with custom response_parser."""

        async def mock_sse_stream():
            yield b"line1,data1\n\n"
            yield b"line2,data2\n\n"
            yield b"line3,data3\n\n"

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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


class TestSSESyncDecorators:
    """Test synchronous SSE streaming decorators."""

    @respx.mock
    def test_sse_sync_iterator_pydantic_model(self):
        """Test sync SSE streaming with Pydantic model hydration."""

        def mock_sse_stream():
            yield b'{"text": "hello"}\n\n'
            yield b'{"text": "world"}\n\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    @respx.mock
    def test_sse_sync_iterator_dict(self):
        """Test sync SSE streaming with dict hydration."""

        def mock_sse_stream():
            yield b'{"key": "value1"}\n\n'
            yield b'{"key": "value2"}\n\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    @respx.mock
    def test_sse_sync_iterator_str(self):
        """Test sync SSE streaming with string (no parsing)."""

        def mock_sse_stream():
            yield b"hello\n\n"
            yield b"world\n\n"

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    @respx.mock
    def test_sse_sync_with_response_parser(self):
        """Test sync SSE streaming with custom response_parser."""

        def mock_sse_stream():
            yield b"a:1\n\n"
            yield b"b:2\n\n"

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

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

    @respx.mock
    def test_sse_sync_error_response_raises(self):
        """Test sync SSE streaming raises on error responses."""
        respx.get("http://localhost:8000/events").mock(return_value=httpx.Response(404, text="Not Found"))

        client = APIClient(base_url="http://localhost:8000")

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

    @respx.mock
    def test_sse_sync_500_error_response_raises(self):
        """Test sync SSE streaming raises on 500 error."""
        respx.get("http://localhost:8000/events").mock(return_value=httpx.Response(500, text="Internal Server Error"))

        client = APIClient(base_url="http://localhost:8000")

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass
