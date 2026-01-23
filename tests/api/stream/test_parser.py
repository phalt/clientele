"""Tests for clientele.api.stream.parser module."""

import json
import typing

import pytest
from pydantic import BaseModel

from clientele.api.stream import parser


class Token(BaseModel):
    text: str
    id: int


class SampleTypedDict(typing.TypedDict):
    name: str
    value: int


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
