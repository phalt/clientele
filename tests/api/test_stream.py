from __future__ import annotations

from typing import AsyncIterator, Iterator

import pytest
from pydantic import BaseModel

from clientele.api import requests
from clientele.api.client import APIClient
from clientele.api.exceptions import HTTPStatusError
from clientele.testing import ResponseFactory, configure_client_for_testing


class Token(BaseModel):
    text: str


class RequestData(BaseModel):
    """Test model for POST request data."""

    prompt: str
    max_tokens: int


class TestStreamDecorators:
    @pytest.mark.asyncio
    async def test_stream_async_iterator_pydantic_model(self):
        """Test streaming with Pydantic model hydration (SSE-like format with \\n\\n delimiters)."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b'{"text": "hello"}\n\n{"text": "world"}\n\n{"text": "test"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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
    async def test_stream_async_iterator_dict(self):
        """Test streaming with dict hydration."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b'{"key": "value1"}\n\n{"key": "value2"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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
    async def test_stream_async_iterator_str(self):
        """Test streaming with string (no parsing)."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b"hello\n\nworld\n\n",
                headers={"content-type": "text/event-stream"},
            ),
        )

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

    def test_stream_missing_streaming_type_raises(self):
        """Test that non-streaming result type raises error."""
        client = APIClient(base_url="http://localhost:8000")

        with pytest.raises(TypeError, match="must have a streaming result type"):

            @client.get("/events", streaming_response=True)
            async def bad_stream(*, result: Token) -> Token:  # NOT AsyncIterator!
                return result

    def test_stream_missing_inner_type_raises(self):
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
    async def test_stream_skips_empty_lines(self):
        """Test streaming skips empty lines."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b'{"text": "first"}\n\n\n\n\n\n{"text": "second"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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
    async def test_stream_error_response_raises(self):
        """Test streaming raises on error responses."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.not_found(
                data=b"Not Found",
                headers={"content-type": "text/plain"},
            ),
        )

        @client.get("/events", streaming_response=True)
        async def stream_tokens(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            async for _ in await stream_tokens():
                pass

        await client.aclose()

    @pytest.mark.asyncio
    async def test_stream_post_with_data_parameter(self):
        """Test streaming POST request with data payload."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/generate",
            response_obj=ResponseFactory.ok(
                data=b'{"text": "response1"}\n\n{"text": "response2"}\n\n{"text": "response3"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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

        await client.aclose()

    def test_stream_cannot_use_response_map(self):
        """Test that decorators cannot use response_map."""

        async def dummy_func(*, result: AsyncIterator[Token]) -> AsyncIterator[Token]:
            return result

        with pytest.raises(TypeError, match="cannot use response_map"):
            requests.build_request_context("GET", "/events", dummy_func, response_map={200: Token}, streaming=True)

    @pytest.mark.asyncio
    async def test_stream_with_response_parser(self):
        """Test streaming with custom response_parser."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b"line1,data1\n\nline2,data2\n\nline3,data3\n\n",
                headers={"content-type": "text/event-stream"},
            ),
        )

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


class TestStreamingSyncDecorators:
    """Test synchronous streaming decorators."""

    def test_stream_sync_iterator_pydantic_model(self):
        """Test sync streaming with Pydantic model hydration."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b'{"text": "hello"}\n\n{"text": "world"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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

    def test_stream_sync_iterator_dict(self):
        """Test sync streaming with dict hydration."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b'{"key": "value1"}\n\n{"key": "value2"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        )

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

    def test_stream_sync_iterator_str(self):
        """Test sync streaming with string (no parsing)."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b"hello\n\nworld\n\n",
                headers={"content-type": "text/event-stream"},
            ),
        )

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

    def test_stream_sync_with_response_parser(self):
        """Test sync streaming with custom response_parser."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.ok(
                data=b"a:1\n\nb:2\n\n",
                headers={"content-type": "text/event-stream"},
            ),
        )

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

    def test_stream_sync_error_response_raises(self):
        """Test sync streaming raises on error responses."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.not_found(
                data=b"Not Found",
                headers={"content-type": "text/plain"},
            ),
        )

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()

    def test_stream_sync_500_error_response_raises(self):
        """Test sync streaming raises on 500 error."""
        client = APIClient(base_url="http://localhost:8000")

        fake_backend = configure_client_for_testing(client)
        fake_backend.queue_response(
            path="/events",
            response_obj=ResponseFactory.internal_server_error(
                data=b"Internal Server Error",
                headers={"content-type": "text/plain"},
            ),
        )

        @client.get("/events", streaming_response=True)
        def stream_tokens(*, result: Iterator[Token]) -> Iterator[Token]:
            return result

        with pytest.raises(HTTPStatusError):
            for _ in stream_tokens():
                pass

        client.close()
