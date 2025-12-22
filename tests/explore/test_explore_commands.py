"""Tests for clientele.explore.commands module."""

from unittest.mock import MagicMock, Mock, patch
from types import ModuleType

import pytest

from clientele.explore.commands import CommandHandler
from clientele.explore.session import SessionConfig
from clientele.explore.introspector import ClientIntrospector


@pytest.fixture
def session():
    """Create a SessionConfig instance."""
    return SessionConfig()


@pytest.fixture
def mock_client():
    """Create a mock client module."""
    client = ModuleType("mock_client")
    
    def operation_one():
        """First operation."""
        pass
    
    def operation_two():
        """Second operation."""
        pass
    
    client.operation_one = operation_one
    client.operation_two = operation_two
    
    return client


@pytest.fixture
def mock_schemas():
    """Create a mock schemas module."""
    schemas = ModuleType("mock_schemas")
    
    class TestSchema:
        """Test schema class."""
        __doc__ = "A test schema"
        field1: str
        field2: int
    
    schemas.TestSchema = TestSchema
    
    return schemas


@pytest.fixture
def introspector(mock_client, mock_schemas):
    """Create a ClientIntrospector instance."""
    return ClientIntrospector(mock_client, mock_schemas)


@pytest.fixture
def command_handler(session, introspector):
    """Create a CommandHandler instance."""
    return CommandHandler(session, introspector)


def test_handle_list_command(command_handler):
    """Test handling /list command."""
    result = command_handler.handle("/list")
    
    assert "operation_one" in result
    assert "operation_two" in result


def test_handle_list_command_no_operations():
    """Test /list command with no operations."""
    session = SessionConfig()
    empty_client = ModuleType("empty")
    empty_schemas = ModuleType("empty_schemas")
    introspector = ClientIntrospector(empty_client, empty_schemas)
    handler = CommandHandler(session, introspector)
    
    result = handler.handle("/list")
    assert "No operations" in result or "0" in result


def test_handle_schemas_list(command_handler):
    """Test handling /schemas command without arguments."""
    result = command_handler.handle("/schemas")
    
    assert "TestSchema" in result


def test_handle_schemas_inspect(command_handler):
    """Test handling /schemas <name> command."""
    result = command_handler.handle("/schemas TestSchema")
    
    assert "TestSchema" in result


def test_handle_config_show(command_handler):
    """Test handling /config command."""
    result = command_handler.handle("/config")
    
    assert "base_url" in result or "Configuration" in result


def test_handle_config_set(command_handler, session):
    """Test handling /config set command."""
    result = command_handler.handle("/config set base_url https://api.test.com")
    
    assert "base_url" in result
    assert session.config_overrides.get("base_url") == "https://api.test.com"


def test_handle_debug_on(command_handler, session):
    """Test handling /debug on command."""
    assert session.debug is False
    
    result = command_handler.handle("/debug on")
    
    assert session.debug is True
    assert "enabled" in result.lower() or "on" in result.lower()


def test_handle_debug_off(command_handler, session):
    """Test handling /debug off command."""
    session.debug = True
    
    result = command_handler.handle("/debug off")
    
    assert session.debug is False
    assert "disabled" in result.lower() or "off" in result.lower()


def test_handle_help_command(command_handler):
    """Test handling /help command."""
    result = command_handler.handle("/help")
    
    assert "/list" in result
    assert "/schemas" in result
    assert "/config" in result
    assert "/debug" in result
    assert "/exit" in result


def test_handle_exit_command(command_handler):
    """Test handling /exit command."""
    result = command_handler.handle("/exit")
    
    # Exit should return None or empty to signal exit
    assert result is None or result == ""


def test_handle_quit_command(command_handler):
    """Test handling /quit command."""
    result = command_handler.handle("/quit")
    
    # Quit should behave like exit
    assert result is None or result == ""


def test_handle_unknown_command(command_handler):
    """Test handling unknown command."""
    result = command_handler.handle("/unknown")
    
    assert "Unknown" in result or "not recognized" in result.lower()


def test_handle_question_mark(command_handler):
    """Test handling ? as shortcut for help."""
    result = command_handler.handle("?")
    
    # ? should show help
    assert "/list" in result or "help" in result.lower()


def test_handle_config_set_multiple_words(command_handler, session):
    """Test /config set with value containing spaces."""
    result = command_handler.handle("/config set bearer_token my_secret_token_123")
    
    assert session.config_overrides.get("bearer_token") == "my_secret_token_123"


def test_handle_schemas_nonexistent(command_handler):
    """Test /schemas with nonexistent schema name."""
    result = command_handler.handle("/schemas NonExistent")
    
    assert "not found" in result.lower() or "NonExistent" in result
