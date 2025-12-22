"""Tests for clientele.explore.commands module."""

from unittest.mock import Mock, patch

from clientele.explore.commands import CommandHandler
from clientele.explore.session import SessionConfig


def test_command_handler_initialization():
    """Test CommandHandler initializes correctly."""
    introspector = Mock()
    session_config = SessionConfig()

    handler = CommandHandler(introspector, session_config)

    assert handler.introspector == introspector
    assert handler.session_config == session_config
    assert handler.console is not None


def test_handle_exit_command():
    """Test /exit command returns True."""
    introspector = Mock()
    handler = CommandHandler(introspector)

    result = handler.handle_command("/exit")
    assert result is True

    result = handler.handle_command("/quit")
    assert result is True


def test_handle_list_command():
    """Test /list command lists operations."""
    # Setup mock operations
    mock_op1 = Mock(http_method="GET", docstring="Get operation")
    mock_op2 = Mock(http_method="POST", docstring="Create operation")

    introspector = Mock()
    introspector.operations = {"get_user": mock_op1, "create_user": mock_op2}

    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/list")

    assert result is False


def test_handle_list_no_operations():
    """Test /list with no operations."""
    introspector = Mock()
    introspector.operations = {}

    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print") as mock_print:
        result = handler.handle_command("/list")

    assert result is False
    # Should print "No operations found"
    assert mock_print.called


def test_handle_schemas_list():
    """Test /schemas command lists schemas."""
    introspector = Mock()
    introspector.schemas = {"User": Mock(__doc__="User model"), "Post": Mock(__doc__="Post model")}

    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/schemas")

    assert result is False


def test_handle_schemas_detail():
    """Test /schemas <name> shows schema details."""
    # Create mock schema with model_fields
    mock_field1 = Mock()
    mock_field1.annotation = int
    mock_field1.is_required = lambda: True

    mock_field2 = Mock()
    mock_field2.annotation = str
    mock_field2.is_required = lambda: False

    mock_schema = Mock()
    mock_schema.__doc__ = "User model"
    mock_schema.model_fields = {"id": mock_field1, "name": mock_field2}

    introspector = Mock()
    introspector.schemas = {"User": mock_schema}

    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/schemas User")

    assert result is False


def test_handle_config_show():
    """Test /config shows configuration."""
    introspector = Mock()
    session_config = SessionConfig()

    # Mock config module
    mock_config = Mock()
    mock_config.api_base_url = Mock(return_value="https://api.test.com")
    mock_config.api_bearer_token = Mock(return_value=None)
    mock_config.api_user_key = Mock(return_value=None)
    mock_config.api_pass_key = Mock(return_value=None)

    handler = CommandHandler(introspector, session_config)
    handler.config_module = mock_config

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/config")

    assert result is False


def test_handle_config_set():
    """Test /config set <key> <value> sets configuration."""
    introspector = Mock()
    session_config = SessionConfig()

    # Mock config module
    mock_config = Mock()
    handler = CommandHandler(introspector, session_config)
    handler.config_module = mock_config

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/config set base_url https://new-api.com")

    assert result is False
    assert session_config.config_overrides["base_url"] == "https://new-api.com"


def test_handle_debug_on():
    """Test /debug on enables debug mode."""
    introspector = Mock()
    session_config = SessionConfig()

    handler = CommandHandler(introspector, session_config)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/debug on")

    assert result is False
    assert session_config.debug_mode is True


def test_handle_debug_off():
    """Test /debug off disables debug mode."""
    introspector = Mock()
    session_config = SessionConfig(debug_mode=True)

    handler = CommandHandler(introspector, session_config)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/debug off")

    assert result is False
    assert session_config.debug_mode is False


def test_handle_help():
    """Test /help shows help message."""
    introspector = Mock()
    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print"):
        result = handler.handle_command("/help")

    assert result is False


def test_handle_unknown_command():
    """Test unknown command shows error."""
    introspector = Mock()
    handler = CommandHandler(introspector)

    with patch.object(handler.console, "print") as mock_print:
        result = handler.handle_command("/unknown")

    assert result is False
    # Should print error message
    assert mock_print.called
