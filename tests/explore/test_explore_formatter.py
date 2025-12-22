"""Tests for clientele.explore.formatter module."""

import time
from unittest.mock import MagicMock, Mock

import pytest
from pydantic import BaseModel

from clientele.explore.formatter import ResponseFormatter
from clientele.explore.session import SessionConfig


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""

    name: str
    value: int


@pytest.fixture
def formatter():
    """Create a ResponseFormatter instance."""
    session = SessionConfig()
    return ResponseFormatter(session)


def test_format_success_with_pydantic_model(formatter):
    """Test formatting successful response with Pydantic model."""
    model = SampleModel(name="test", value=42)
    result = formatter.format_success(model, 0.123)
    
    assert "✓" in result
    assert "0.12s" in result
    assert "test" in result
    assert "42" in result


def test_format_success_with_dict(formatter):
    """Test formatting successful response with dict."""
    data = {"key": "value", "number": 123}
    result = formatter.format_success(data, 0.456)
    
    assert "✓" in result
    assert "0.46s" in result
    assert "key" in result
    assert "value" in result


def test_format_success_with_list(formatter):
    """Test formatting successful response with list."""
    data = [1, 2, 3]
    result = formatter.format_success(data, 0.001)
    
    assert "✓" in result
    assert "0.00s" in result


def test_format_success_with_none(formatter):
    """Test formatting successful response with None."""
    result = formatter.format_success(None, 0.789)
    
    assert "✓" in result
    assert "0.79s" in result
    assert "null" in result or "None" in result


def test_format_success_with_string(formatter):
    """Test formatting successful response with string."""
    result = formatter.format_success("simple string", 0.001)
    
    assert "✓" in result
    assert "simple string" in result


def test_format_error_basic(formatter):
    """Test formatting error response."""
    error = Exception("Test error message")
    result = formatter.format_error(error, 0.234)
    
    assert "✗" in result
    assert "0.23s" in result
    assert "Test error message" in result


def test_format_error_with_traceback(formatter):
    """Test formatting error response with traceback."""
    try:
        raise ValueError("Detailed error")
    except ValueError as e:
        result = formatter.format_error(e, 0.100)
    
    assert "✗" in result
    assert "Detailed error" in result


def test_format_debug_info(formatter):
    """Test formatting debug information."""
    debug_info = {
        "operation": "test_operation",
        "method": "GET",
        "base_url": "https://api.example.com",
        "args": {"param": "value"},
    }
    
    result = formatter.format_debug_info(debug_info)
    
    assert "Debug Information" in result
    assert "test_operation" in result
    assert "GET" in result
    assert "https://api.example.com" in result


def test_format_debug_info_with_error(formatter):
    """Test formatting debug information with error details."""
    debug_info = {
        "operation": "failing_op",
        "method": "POST",
        "base_url": "https://api.example.com",
        "args": {},
        "error_type": "ValidationError",
        "error_message": "Invalid data",
    }
    
    result = formatter.format_debug_info(debug_info)
    
    assert "ValidationError" in result
    assert "Invalid data" in result


def test_format_success_with_model_dump(formatter):
    """Test Pydantic model uses model_dump if available."""
    model = SampleModel(name="test", value=99)
    result = formatter.format_success(model, 0.01)
    
    # Should contain the serialized data
    assert "test" in result
    assert "99" in result
