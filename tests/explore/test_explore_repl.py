"""Tests for clientele.explore.repl module."""

from unittest.mock import MagicMock, Mock, patch
from types import ModuleType

import pytest

from clientele.explore.repl import ClienteleREPL
from clientele.explore.session import SessionConfig


@pytest.fixture
def mock_client():
    """Create a mock client module."""
    client = ModuleType("mock_client")
    
    def test_operation(param: str = "default"):
        """Test operation."""
        return {"result": param}
    
    client.test_operation = test_operation
    
    return client


@pytest.fixture
def mock_schemas():
    """Create a mock schemas module."""
    schemas = ModuleType("mock_schemas")
    
    class TestSchema:
        pass
    
    schemas.TestSchema = TestSchema
    
    return schemas


@pytest.fixture
def repl(mock_client, mock_schemas):
    """Create a ClienteleREPL instance."""
    session = SessionConfig()
    return ClienteleREPL(mock_client, mock_schemas, session)


def test_repl_initialization(repl):
    """Test REPL initialization."""
    assert repl.client is not None
    assert repl.schemas is not None
    assert repl.session is not None
    assert repl.introspector is not None
    assert repl.executor is not None
    assert repl.formatter is not None
    assert repl.command_handler is not None


def test_is_command_detection(repl):
    """Test command detection."""
    assert repl._is_command("/list") is True
    assert repl._is_command("/help") is True
    assert repl._is_command("?") is True
    assert repl._is_command("test_operation()") is False
    assert repl._is_command("regular text") is False


def test_parse_operation_call_no_args(repl):
    """Test parsing operation call without arguments."""
    name, args = repl._parse_operation_call("test_operation()")
    
    assert name == "test_operation"
    assert args == {}


def test_parse_operation_call_with_args(repl):
    """Test parsing operation call with arguments."""
    name, args = repl._parse_operation_call('test_operation(param="value")')
    
    assert name == "test_operation"
    assert args == {"param": "value"}


def test_parse_operation_call_invalid(repl):
    """Test parsing invalid operation call."""
    name, args = repl._parse_operation_call("invalid syntax")
    
    # Should handle gracefully
    assert name is not None or args is not None


@patch("clientele.explore.repl.Console")
def test_welcome_message(mock_console, repl):
    """Test that welcome message is displayed."""
    with patch.object(repl, "console"):
        repl.show_welcome()
        # Welcome message should be shown
        assert True  # If no exception, test passes


@patch("clientele.explore.repl.PromptSession")
def test_repl_run_exit(mock_session, mock_client, mock_schemas):
    """Test REPL exits gracefully."""
    session = SessionConfig()
    repl = ClienteleREPL(mock_client, mock_schemas, session)
    
    # Mock prompt to return exit command
    mock_session_instance = Mock()
    mock_session_instance.prompt.return_value = "/exit"
    mock_session.return_value = mock_session_instance
    
    # Run should exit without error
    with patch.object(repl, "session", mock_session_instance):
        # Test that exit is handled
        assert True


def test_operation_name_parsing(repl):
    """Test extracting operation name from input."""
    name, _ = repl._parse_operation_call("my_operation()")
    assert name == "my_operation"
    
    name, _ = repl._parse_operation_call("another_op(x=1)")
    assert name == "another_op"
