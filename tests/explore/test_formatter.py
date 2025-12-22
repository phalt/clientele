"""Tests for clientele.explore.formatter module."""

from unittest.mock import Mock, patch
import pytest
from clientele.explore.formatter import ResponseFormatter
from clientele.explore.executor import ExecutionResult


def test_formatter_initialization():
    """Test ResponseFormatter initializes correctly."""
    formatter = ResponseFormatter()
    assert formatter.console is not None


def test_formatter_with_custom_console():
    """Test ResponseFormatter with custom console."""
    console = Mock()
    formatter = ResponseFormatter(console=console)
    assert formatter.console == console


def test_format_success_with_dict():
    """Test formatting successful dict response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response={"key": "value"},
        duration=0.5,
        error=None,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        assert mock_print.called
        # Check for success message
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('Success' in str(call) for call in calls)


def test_format_success_with_pydantic_model():
    """Test formatting Pydantic model response."""
    formatter = ResponseFormatter()
    
    # Mock Pydantic model
    mock_model = Mock()
    mock_model.model_dump.return_value = {"id": 1, "name": "test"}
    
    result = ExecutionResult(
        success=True,
        response=mock_model,
        duration=0.3,
        error=None,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print'):
        formatter.format(result)
        mock_model.model_dump.assert_called_once()


def test_format_success_with_list():
    """Test formatting list response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response=[{"id": 1}, {"id": 2}],
        duration=0.2,
        error=None,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        assert mock_print.called


def test_format_success_with_none():
    """Test formatting None response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response=None,
        duration=0.1,
        error=None,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('No response' in str(call) for call in calls)


def test_format_error():
    """Test formatting error response."""
    formatter = ResponseFormatter()
    error = ValueError("Test error")
    result = ExecutionResult(
        success=False,
        response=None,
        duration=0.05,
        error=error,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('Error' in str(call) for call in calls)


def test_format_with_debug_info():
    """Test formatting with debug information."""
    formatter = ResponseFormatter()
    debug_info = {
        "operation": "test_op",
        "method": "GET",
        "base_url": "https://api.test.com",
        "args": {"id": 1}
    }
    result = ExecutionResult(
        success=True,
        response={"result": "ok"},
        duration=0.4,
        error=None,
        debug_info=debug_info
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        # Debug info should be displayed
        assert mock_print.called


def test_format_success_with_string():
    """Test formatting plain string response."""
    formatter = ResponseFormatter()
    result = ExecutionResult(
        success=True,
        response="Plain text response",
        duration=0.1,
        error=None,
        debug_info=None
    )
    
    with patch.object(formatter.console, 'print') as mock_print:
        formatter.format(result)
        assert mock_print.called
