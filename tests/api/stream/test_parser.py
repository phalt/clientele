"""Tests for clientele.api.stream.parser module."""

import json
import typing

import httpx
import pytest
from pydantic import BaseModel

from clientele.api.stream import parser
from clientele.http import httpx_backend as http_httpx


class Token(BaseModel):
    text: str
    id: int


class SampleTypedDict(typing.TypedDict):
    name: str
    value: int


class TestParseSSEStream:
    @pytest.mark.asyncio
    async def test_parse_sse_stream_with_string_type(self):
        """Test parsing SSE stream with string inner type."""

        async def mock_response():
            yield b"hello\n"
            yield b"world\n"
            yield b"test\n"

        response = httpx.Response(200, content=mock_response())
        # Read all content from streaming response
        await response.aread()
        generic_response = http_httpx.HttpxHTTPBackend.convert_to_response(response)

        items = []
        async for item in parser.parse_sse_stream(generic_response, str):
            items.append(item)

        assert len(items) == 3
        assert items[0] == "hello"
        assert items[1] == "world"
        assert items[2] == "test"

    @pytest.mark.asyncio
    async def test_parse_sse_stream_with_dict_type(self):
        """Test parsing SSE stream with dict inner type."""

        async def mock_response():
            yield b'{"key": "value1"}\n'
            yield b'{"key": "value2"}\n'

        response = httpx.Response(200, content=mock_response())
        await response.aread()
        generic_response = http_httpx.HttpxHTTPBackend.convert_to_response(response)

        items = []
        async for item in parser.parse_sse_stream(generic_response, dict):
            items.append(item)

        assert len(items) == 2
        assert items[0] == {"key": "value1"}
        assert items[1] == {"key": "value2"}

    @pytest.mark.asyncio
    async def test_parse_sse_stream_with_pydantic_model(self):
        """Test parsing SSE stream with Pydantic model inner type."""

        async def mock_response():
            yield b'{"text": "hello", "id": 1}\n'
            yield b'{"text": "world", "id": 2}\n'

        response = httpx.Response(200, content=mock_response())
        await response.aread()
        generic_response = http_httpx.HttpxHTTPBackend.convert_to_response(response)

        items = []
        async for item in parser.parse_sse_stream(generic_response, Token):
            items.append(item)

        assert len(items) == 2
        assert isinstance(items[0], Token)
        assert items[0].text == "hello"
        assert items[0].id == 1
        assert isinstance(items[1], Token)
        assert items[1].text == "world"
        assert items[1].id == 2

    @pytest.mark.asyncio
    async def test_parse_sse_stream_skips_empty_lines(self):
        """Test that empty lines are skipped in SSE stream."""

        async def mock_response():
            yield b"line1\n"
            yield b"\n"  # Empty line
            yield b""  # Another empty line
            yield b"line2\n"

        response = httpx.Response(200, content=mock_response())
        await response.aread()
        generic_response = http_httpx.HttpxHTTPBackend.convert_to_response(response)

        items = []
        async for item in parser.parse_sse_stream(generic_response, str):
            items.append(item)

        assert len(items) == 2
        assert items[0] == "line1"
        assert items[1] == "line2"


class TestHydrateContent:
    def test_hydrate_content_string_type(self):
        """Test hydrating content as string."""
        content = "hello world"
        result = parser.hydrate_content(content, str)
        assert result == "hello world"

    def test_hydrate_content_dict_type(self):
        """Test hydrating content as dict."""
        content = '{"name": "test", "value": 42}'
        result = parser.hydrate_content(content, dict)
        assert result == {"name": "test", "value": 42}

    def test_hydrate_content_pydantic_model_v2(self):
        """Test hydrating content as Pydantic model (v2 with model_validate)."""
        content = '{"text": "hello", "id": 123}'
        result = parser.hydrate_content(content, Token)
        assert isinstance(result, Token)
        assert result.text == "hello"
        assert result.id == 123

    def test_hydrate_content_typeddict(self):
        """Test hydrating content as TypedDict."""
        content = '{"name": "test", "value": 42}'
        result = parser.hydrate_content(content, SampleTypedDict)
        assert result == {"name": "test", "value": 42}

    def test_hydrate_content_typeddict_invalid_raises(self):
        """Test that non-dict content for TypedDict raises TypeError."""
        content = '["not", "a", "dict"]'
        with pytest.raises(TypeError, match="Expected dict for TypedDict"):
            parser.hydrate_content(content, SampleTypedDict)

    def test_hydrate_content_default_json_parsing(self):
        """Test default JSON parsing for unknown types."""
        content = '{"unknown": "type"}'
        result = parser.hydrate_content(content, object)
        assert result == {"unknown": "type"}

    def test_hydrate_content_default_fallback_to_string(self):
        """Test fallback to string for non-JSON content."""
        content = "not json at all"
        result = parser.hydrate_content(content, object)
        assert result == "not json at all"

    def test_hydrate_content_invalid_json_for_dict(self):
        """Test that invalid JSON for dict raises JSONDecodeError."""
        content = "not valid json"
        with pytest.raises(json.JSONDecodeError):
            parser.hydrate_content(content, dict)

    def test_hydrate_content_invalid_json_for_pydantic(self):
        """Test that invalid JSON for Pydantic model raises JSONDecodeError."""
        content = "not valid json"
        with pytest.raises(json.JSONDecodeError):
            parser.hydrate_content(content, Token)

    def test_hydrate_content_empty_string_for_string_type(self):
        """Test hydrating empty string as string type."""
        content = ""
        result = parser.hydrate_content(content, str)
        assert result == ""

    def test_hydrate_content_numeric_json(self):
        """Test hydrating numeric JSON with default type."""
        content = "42"
        result = parser.hydrate_content(content, object)
        assert result == 42

    def test_hydrate_content_array_json(self):
        """Test hydrating array JSON with default type."""
        content = '["item1", "item2"]'
        result = parser.hydrate_content(content, object)
        assert result == ["item1", "item2"]

    def test_hydrate_content_boolean_json(self):
        """Test hydrating boolean JSON with default type."""
        content = "true"
        result = parser.hydrate_content(content, object)
        assert result is True

    def test_hydrate_content_null_json(self):
        """Test hydrating null JSON with default type."""
        content = "null"
        result = parser.hydrate_content(content, object)
        assert result is None
