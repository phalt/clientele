"""Tests for the ResponseFormatter class."""

from unittest.mock import Mock

from pydantic import BaseModel
from rich.console import Console

from clientele.explore.executor import ExecutionResult
from clientele.explore.formatter import ResponseFormatter


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""

    id: int
    name: str


def test_formatter_initialization_default():
    """Test formatter initializes with default console."""
    formatter = ResponseFormatter()
    assert formatter.console is not None
    assert isinstance(formatter.console, Console)


def test_formatter_initialization_custom_console():
    """Test formatter initializes with custom console."""
    custom_console = Mock(spec=Console)
    formatter = ResponseFormatter(console=custom_console)
    assert formatter.console is custom_console


def test_format_success_with_pydantic_model(capsys):
    """Test formatting a successful result with Pydantic model."""
    formatter = ResponseFormatter()
    model_response = SampleModel(id=1, name="Test")
    result = ExecutionResult(
        success=True,
        response=model_response,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_dict(capsys):
    """Test formatting a successful result with dictionary."""
    formatter = ResponseFormatter()
    dict_response = {"id": 1, "name": "Test"}
    result = ExecutionResult(
        success=True,
        response=dict_response,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_list_of_models(capsys):
    """Test formatting a successful result with list of Pydantic models."""
    formatter = ResponseFormatter()
    list_response = [
        SampleModel(id=1, name="Test1"),
        SampleModel(id=2, name="Test2"),
    ]
    result = ExecutionResult(
        success=True,
        response=list_response,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_list_of_dicts(capsys):
    """Test formatting a successful result with list of dictionaries."""
    formatter = ResponseFormatter()
    list_response = [{"id": 1, "name": "Test1"}, {"id": 2, "name": "Test2"}]
    result = ExecutionResult(
        success=True,
        response=list_response,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_none_response(capsys):
    """Test formatting a successful result with None response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response=None,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_string_response(capsys):
    """Test formatting a successful result with string response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response="Simple string response",
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_debug_info(capsys):
    """Test formatting a successful result with debug information."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response={"status": "ok"},
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info={
            "operation": "test_operation",
            "method": "GET",
            "base_url": "https://api.example.com",
            "args": {"id": 123},
            "response_type": "dict",
        },
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_error_with_exception(capsys):
    """Test formatting an error result with exception."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=False,
        response=None,
        duration=0.5,
        operation="test_operation",
        error=ValueError("Test error message"),
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_error_without_exception(capsys):
    """Test formatting an error result without exception."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=False,
        response=None,
        duration=0.5,
        operation="test_operation",
        error=None,
        debug_info=None,
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_error_with_debug_info(capsys):
    """Test formatting an error result with debug information."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=False,
        response=None,
        duration=0.5,
        operation="test_operation",
        error=RuntimeError("API call failed"),
        debug_info={
            "operation": "test_operation",
            "method": "POST",
            "base_url": "https://api.example.com",
            "args": {"data": "test"},
            "error": "API call failed",
            "error_type": "RuntimeError",
        },
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_object_with_dict_method():
    """Test formatting response with object that has dict() method."""
    formatter = ResponseFormatter()

    class LegacyModel:
        def dict(self):
            return {"id": 1, "legacy": True}

    result = ExecutionResult(
        success=True,
        response=LegacyModel(),
        duration=0.5,
        operation="test_operation",
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True


def test_format_success_with_empty_list():
    """Test formatting response with empty list."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response=[],
        duration=0.5,
        operation="test_operation",
    )

    formatter.format(result)
    # Just verify no exceptions are raised
    assert True
