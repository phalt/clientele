"""Tests for the CommandHandler class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from clientele.explore.commands import CommandHandler
from clientele.explore.introspector import ClientIntrospector
from clientele.explore.session import SessionConfig


@pytest.fixture
def test_client_path():
    """Path to the test client."""
    return Path(__file__).parent.parent / "test_client"


@pytest.fixture
def introspector(test_client_path):
    """Create a ClientIntrospector with loaded test client."""
    intro = ClientIntrospector(test_client_path)
    intro.load_client()
    intro.discover_operations()
    return intro


@pytest.fixture
def session_config():
    """Create a SessionConfig."""
    return SessionConfig()


@pytest.fixture
def handler(introspector, session_config):
    """Create a CommandHandler."""
    return CommandHandler(introspector, session_config)


def test_handler_initialization(introspector, session_config):
    """Test CommandHandler initializes correctly."""
    handler = CommandHandler(introspector, session_config)
    assert handler.introspector is introspector
    assert handler.session_config is session_config
    assert handler.console is not None


def test_handler_initialization_without_config(introspector):
    """Test CommandHandler initializes without session config."""
    handler = CommandHandler(introspector)
    assert handler.introspector is introspector
    assert handler.session_config is None


def test_handler_initialization_with_custom_console(introspector):
    """Test CommandHandler initializes with custom console."""
    custom_console = Mock(spec=Console)
    handler = CommandHandler(introspector, console=custom_console)
    assert handler.console is custom_console


def test_handle_exit_command(handler):
    """Test /exit command returns True."""
    result = handler.handle_command("/exit")
    assert result is True


def test_handle_quit_command(handler):
    """Test /quit command returns True."""
    result = handler.handle_command("/quit")
    assert result is True


def test_handle_list_command(handler):
    """Test /list command."""
    result = handler.handle_command("/list")
    assert result is False


def test_handle_operations_command(handler):
    """Test /operations command (alias for /list)."""
    result = handler.handle_command("/operations")
    assert result is False


def test_handle_help_command(handler):
    """Test /help command."""
    result = handler.handle_command("/help")
    assert result is False


def test_handle_schemas_command_without_arg(handler):
    """Test /schemas command without argument."""
    result = handler.handle_command("/schemas")
    assert result is False


def test_handle_schemas_command_with_arg(handler):
    """Test /schemas command with schema name."""
    result = handler.handle_command("/schemas SimpleResponse")
    assert result is False


def test_handle_config_command_without_arg(handler):
    """Test /config command without argument."""
    result = handler.handle_command("/config")
    assert result is False


def test_handle_debug_command_without_arg(handler):
    """Test /debug command without argument."""
    result = handler.handle_command("/debug")
    assert result is False


def test_handle_debug_on(handler):
    """Test /debug on command."""
    result = handler.handle_command("/debug on")
    assert result is False
    assert handler.session_config.debug_mode is True


def test_handle_debug_off(handler):
    """Test /debug off command."""
    handler.session_config.debug_mode = True
    result = handler.handle_command("/debug off")
    assert result is False
    assert handler.session_config.debug_mode is False


def test_handle_debug_invalid_arg(handler):
    """Test /debug with invalid argument."""
    result = handler.handle_command("/debug invalid")
    assert result is False


def test_handle_unknown_command(handler):
    """Test unknown command."""
    result = handler.handle_command("/unknown")
    assert result is False


def test_list_operations_with_operations(handler):
    """Test listing operations when operations exist."""
    # Just ensure it doesn't raise an exception
    handler._list_operations()


def test_list_operations_without_operations(introspector, session_config):
    """Test listing operations when no operations exist."""
    introspector.operations = {}
    handler = CommandHandler(introspector, session_config)
    handler._list_operations()


def test_show_help(handler):
    """Test showing help message."""
    # Just ensure it doesn't raise an exception
    handler._show_help()


def test_list_schemas(handler):
    """Test listing schemas."""
    # Just ensure it doesn't raise an exception
    handler._list_schemas()


def test_list_schemas_empty(introspector, session_config):
    """Test listing schemas when none exist."""
    with patch.object(introspector, "get_all_schemas", return_value={}):
        handler = CommandHandler(introspector, session_config)
        handler._list_schemas()


def test_show_schema_detail_existing_schema(handler):
    """Test showing details for existing schema."""
    # Just ensure it doesn't raise an exception
    handler._show_schema_detail("SimpleResponse")


def test_show_schema_detail_nonexistent_schema(handler):
    """Test showing details for non-existent schema."""
    handler._show_schema_detail("NonExistentSchema")


def test_simplify_type_display_simple(handler):
    """Test simplifying simple type display."""
    result = handler._simplify_type_display("typing.Optional[str]")
    assert "typing." not in result


def test_simplify_type_display_annotated(handler):
    """Test simplifying Annotated type display."""
    result = handler._simplify_type_display("Annotated[str, ...]")
    assert "Annotated[" not in result


def test_simplify_type_display_long(handler):
    """Test simplifying very long type display."""
    long_type = "a" * 100
    result = handler._simplify_type_display(long_type)
    assert len(result) <= 50


def test_handle_config_show(handler):
    """Test .config command to show configuration."""
    handler._handle_config(None)


def test_handle_config_set_valid(handler):
    """Test .config set with valid key and value."""
    handler._handle_config("set base_url https://api.example.com")
    assert handler.session_config.config_overrides["base_url"] == "https://api.example.com"


def test_handle_config_set_invalid_format(handler):
    """Test .config set with invalid format."""
    handler._handle_config("set invalid")


def test_handle_config_unknown_subcommand(handler):
    """Test .config with unknown subcommand."""
    handler._handle_config("unknown")


def test_show_config(handler):
    """Test showing configuration."""
    # Just ensure it doesn't raise an exception
    handler._show_config()


def test_show_config_no_module(introspector, session_config):
    """Test showing config when no config module exists."""
    # Create a new introspector with a path that won't have a config module in sys.modules
    import sys

    # Temporarily remove the config module
    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    # Save and remove if exists
    saved_module = sys.modules.get(config_module_name)
    if config_module_name in sys.modules:
        del sys.modules[config_module_name]

    try:
        handler = CommandHandler(introspector, session_config)
        handler._show_config()
    finally:
        # Restore if it was there
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_set_config_valid_key(handler):
    """Test setting valid config key."""
    handler._set_config("base_url", "https://example.com")
    assert handler.session_config.config_overrides["base_url"] == "https://example.com"


def test_set_config_invalid_key(handler):
    """Test setting invalid config key."""
    handler._set_config("invalid_key", "value")
    assert "invalid_key" not in handler.session_config.config_overrides


def test_set_config_no_session_config(introspector):
    """Test setting config without session config."""
    handler = CommandHandler(introspector, session_config=None)
    handler._set_config("base_url", "https://example.com")


def test_apply_config_override(handler):
    """Test applying config override."""
    handler._apply_config_override("base_url", "https://example.com")


def test_apply_config_override_no_module(introspector, session_config):
    """Test applying config override when module doesn't exist."""
    import sys

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)
    if config_module_name in sys.modules:
        del sys.modules[config_module_name]

    try:
        handler = CommandHandler(introspector, session_config)
        handler._apply_config_override("base_url", "https://example.com")
    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_handle_debug_without_session_config(introspector):
    """Test /debug command without session config."""
    handler = CommandHandler(introspector, session_config=None)
    result = handler.handle_command("/debug on")
    assert result is False


def test_handle_config_set_bearer_token(handler):
    """Test setting bearer token."""
    handler._handle_config("set bearer_token test_token_12345")
    assert handler.session_config.config_overrides["bearer_token"] == "test_token_12345"


def test_handle_config_set_user_key(handler):
    """Test setting user key."""
    handler._handle_config("set user_key test_user")
    assert handler.session_config.config_overrides["user_key"] == "test_user"


def test_handle_config_set_pass_key(handler):
    """Test setting pass key."""
    handler._handle_config("set pass_key test_password")
    assert handler.session_config.config_overrides["pass_key"] == "test_password"


def test_command_with_leading_trailing_whitespace(handler):
    """Test command handling with whitespace."""
    result = handler.handle_command("  /help  ")
    assert result is False


def test_schemas_command_with_argument_whitespace(handler):
    """Test /schemas command with argument and whitespace."""
    result = handler.handle_command("/schemas  SimpleResponse  ")
    assert result is False


def test_pydantic_config_handling(introspector, session_config):
    """Test that explore properly handles the new Pydantic Config class format."""
    import sys

    # Verify config module is loaded and has the new format
    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"
    assert config_module_name in sys.modules

    config_module = sys.modules[config_module_name]

    # Verify new Pydantic Config format exists
    assert hasattr(config_module, "config"), "Should have config instance"
    assert hasattr(config_module, "Config"), "Should have Config class"

    config_instance = config_module.config

    # Verify config instance has expected attributes
    assert hasattr(config_instance, "api_base_url")
    assert hasattr(config_instance, "bearer_token")
    assert hasattr(config_instance, "user_key")
    assert hasattr(config_instance, "pass_key")
    assert hasattr(config_instance, "additional_headers")

    # Test that CommandHandler can show config
    handler = CommandHandler(introspector, session_config)
    handler._show_config()  # Should not raise an exception

    # Test that we can set config overrides
    handler._set_config("base_url", "https://test.example.com")
    assert session_config.config_overrides["base_url"] == "https://test.example.com"

    # Verify the config was actually updated
    assert config_instance.api_base_url == "https://test.example.com"

    # Test other config values
    handler._set_config("bearer_token", "test_token_xyz")
    assert config_instance.bearer_token == "test_token_xyz"
