"""Tests for clientele.api.stream.decorators module."""

import typing

import httpx
import pytest
import respx
from pydantic import BaseModel

from clientele.api import APIClient
from clientele.api.stream import StreamDecorators


class Token(BaseModel):
    text: str


class TestStreamDecoratorsInit:
    def test_stream_decorators_init(self):
        """Test StreamDecorators initialization."""
        client = APIClient(base_url="http://localhost:8000")
        stream_deco = StreamDecorators(client)
        assert stream_deco._client is client


class TestStreamDecoratorsGetMethod:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_decorator_async(self):
        """Test GET decorator with async function."""

        async def mock_sse_stream():
            yield b'{"text": "hello"}\n'
            yield b'{"text": "world"}\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        async def stream_tokens(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        items = []
        async for item in await stream_tokens():
            items.append(item)

        assert len(items) == 2
        assert items[0].text == "hello"
        assert items[1].text == "world"

    @respx.mock
    def test_get_decorator_sync(self):
        """Test GET decorator with sync function."""

        def mock_sse_stream():
            yield b'{"text": "hello"}\n'
            yield b'{"text": "world"}\n'

        respx.get("http://localhost:8000/events").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        def stream_tokens(*, result: typing.Iterator[Token]) -> typing.Iterator[Token]:
            return result

        items = []
        for item in stream_tokens():
            items.append(item)

        assert len(items) == 2
        assert items[0].text == "hello"
        assert items[1].text == "world"


class TestStreamDecoratorsPostMethod:
    @pytest.mark.asyncio
    @respx.mock
    async def test_post_decorator_async(self):
        """Test POST decorator with async function."""

        async def mock_sse_stream():
            yield b'{"text": "response"}\n'

        respx.post("http://localhost:8000/generate").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.post("/generate")
        async def generate(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        items = []
        async for item in await generate():
            items.append(item)

        assert len(items) == 1
        assert items[0].text == "response"

    @respx.mock
    def test_post_decorator_sync(self):
        """Test POST decorator with sync function."""

        def mock_sse_stream():
            yield b'{"text": "response"}\n'

        respx.post("http://localhost:8000/generate").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.post("/generate")
        def generate(*, result: typing.Iterator[Token]) -> typing.Iterator[Token]:
            return result

        items = []
        for item in generate():
            items.append(item)

        assert len(items) == 1
        assert items[0].text == "response"


class TestStreamDecoratorsPatchMethod:
    @pytest.mark.asyncio
    @respx.mock
    async def test_patch_decorator_async(self):
        """Test PATCH decorator with async function."""

        async def mock_sse_stream():
            yield b'{"text": "patched"}\n'

        respx.patch("http://localhost:8000/update").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.patch("/update")
        async def update(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        items = []
        async for item in await update():
            items.append(item)

        assert len(items) == 1
        assert items[0].text == "patched"


class TestStreamDecoratorsPutMethod:
    @pytest.mark.asyncio
    @respx.mock
    async def test_put_decorator_async(self):
        """Test PUT decorator with async function."""

        async def mock_sse_stream():
            yield b'{"text": "updated"}\n'

        respx.put("http://localhost:8000/replace").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.put("/replace")
        async def replace(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        items = []
        async for item in await replace():
            items.append(item)

        assert len(items) == 1
        assert items[0].text == "updated"


class TestStreamDecoratorsDeleteMethod:
    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_decorator_async(self):
        """Test DELETE decorator with async function."""

        async def mock_sse_stream():
            yield b'{"text": "deleted"}\n'

        respx.delete("http://localhost:8000/remove").mock(
            return_value=httpx.Response(200, content=mock_sse_stream(), headers={"content-type": "text/event-stream"})
        )

        client = APIClient(base_url="http://localhost:8000")

        @client.stream.delete("/remove")
        async def remove(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        items = []
        async for item in await remove():
            items.append(item)

        assert len(items) == 1
        assert items[0].text == "deleted"


class TestStreamDecoratorsSignaturePreservation:
    def test_async_wrapper_preserves_signature(self):
        """Test that async wrapper preserves function signature."""
        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        async def stream_tokens(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            """Stream tokens from events endpoint."""
            return result

        # Check signature is preserved
        import inspect

        sig = inspect.signature(stream_tokens)
        assert "result" in sig.parameters
        assert sig.parameters["result"].annotation == typing.AsyncIterator[Token]

    def test_sync_wrapper_preserves_signature(self):
        """Test that sync wrapper preserves function signature."""
        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        def stream_tokens(*, result: typing.Iterator[Token]) -> typing.Iterator[Token]:
            """Stream tokens from events endpoint."""
            return result

        # Check signature is preserved
        import inspect

        sig = inspect.signature(stream_tokens)
        assert "result" in sig.parameters
        assert sig.parameters["result"].annotation == typing.Iterator[Token]

    def test_async_wrapper_preserves_function_name(self):
        """Test that async wrapper preserves function name."""
        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        async def my_custom_stream_name(*, result: typing.AsyncIterator[Token]) -> typing.AsyncIterator[Token]:
            return result

        assert my_custom_stream_name.__name__ == "my_custom_stream_name"

    def test_sync_wrapper_preserves_function_name(self):
        """Test that sync wrapper preserves function name."""
        client = APIClient(base_url="http://localhost:8000")

        @client.stream.get("/events")
        def my_custom_stream_name(*, result: typing.Iterator[Token]) -> typing.Iterator[Token]:
            return result

        assert my_custom_stream_name.__name__ == "my_custom_stream_name"
