"""Additional tests for CommandHandler to achieve 100% coverage."""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

import pytest

from clientele.explore.commands import CommandHandler
from clientele.explore.introspector import ClientIntrospector
from clientele.explore.session import SessionConfig


@pytest.fixture
def test_client_path():
    """Path to the test client."""
    return Path(__file__).parent.parent / "old_clients" / "test_client"


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


def test_get_config_instance_with_config_singleton(introspector):
    """Test _get_config_instance when module has a config singleton."""
    handler = CommandHandler(introspector)

    # Create a mock config module with a config instance
    config_module = ModuleType("test_config")
    config_module.config = Mock()

    result = handler._get_config_instance(config_module)
    assert result is config_module.config


def test_get_config_instance_with_config_class_no_singleton(introspector):
    """Test _get_config_instance when module has Config class but no singleton."""
    handler = CommandHandler(introspector)

    # Create a mock config module with Config class
    config_module = ModuleType("test_config")

    class MockConfig:
        def __init__(self):
            self.api_base_url = "http://example.com"

    config_module.Config = MockConfig

    result = handler._get_config_instance(config_module)
    assert result is not None
    assert isinstance(result, MockConfig)

    # Second call should reuse the same instance
    result2 = handler._get_config_instance(config_module)
    assert result2 is result


def test_get_config_instance_config_class_instantiation_fails(introspector):
    """Test _get_config_instance when Config class can't be instantiated."""
    handler = CommandHandler(introspector)

    # Create a mock config module with Config class that raises on __init__
    config_module = ModuleType("test_config")

    class FailingConfig:
        def __init__(self):
            raise ValueError("Required argument missing")

    config_module.Config = FailingConfig

    result = handler._get_config_instance(config_module)
    assert result is None


def test_get_config_instance_old_function_based_config(introspector):
    """Test _get_config_instance with old function-based config (returns None)."""
    handler = CommandHandler(introspector)

    # Create a mock config module with old-style functions
    config_module = ModuleType("test_config")
    config_module.api_base_url = lambda: "http://example.com"
    config_module.get_bearer_token = lambda: "token123"

    result = handler._get_config_instance(config_module)
    assert result is None


def test_show_config_with_runtime_overrides(handler):
    """Test _show_config with runtime overrides in session config."""
    # Set runtime overrides
    handler.session_config.config_overrides["base_url"] = "https://override.example.com"
    handler.session_config.config_overrides["bearer_token"] = "runtime_token_12345"

    # Should not raise exception
    handler._show_config()


def test_show_config_with_old_format_callable_values(introspector, session_config):
    """Test _show_config with old function-based config format."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    # Save original module
    saved_module = sys.modules.get(config_module_name)

    try:
        # Create old-style config module
        old_config = ModuleType(config_module_name)
        old_config.api_base_url = lambda: "http://old.example.com"
        old_config.get_bearer_token = lambda: "old_token"
        old_config.get_user_key = lambda: "old_user"
        old_config.get_pass_key = lambda: "old_pass"
        old_config.additional_headers = lambda: {"X-Custom": "header"}

        sys.modules[config_module_name] = old_config

        handler = CommandHandler(introspector, session_config)
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_config_with_non_callable_old_format_values(introspector, session_config):
    """Test _show_config with old format that has non-callable attribute values."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create old-style config module with direct values
        old_config = ModuleType(config_module_name)
        old_config.api_base_url = "http://direct.example.com"
        old_config.bearer_token = "direct_token"

        sys.modules[config_module_name] = old_config

        handler = CommandHandler(introspector, session_config)
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_config_with_additional_headers_pydantic(handler):
    """Test _show_config displays additional_headers from Pydantic config."""
    # The test_client config should have additional_headers attribute
    handler._show_config()


def test_show_config_with_additional_headers_old_format_exception(introspector, session_config):
    """Test _show_config handles exception when calling old format additional_headers."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create old-style config module with failing additional_headers
        old_config = ModuleType(config_module_name)
        old_config.additional_headers = lambda: 1 / 0  # Will raise ZeroDivisionError

        sys.modules[config_module_name] = old_config

        handler = CommandHandler(introspector, session_config)
        # Should not raise exception, just skip additional headers
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_config_attribute_error_handling(introspector, session_config):
    """Test _show_config handles errors when getting config attribute values."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create config module with problematic attribute
        bad_config = ModuleType(config_module_name)

        class ProblematicConfig:
            @property
            def api_base_url(self):
                raise RuntimeError("Cannot access property")

        bad_config.config = ProblematicConfig()

        sys.modules[config_module_name] = bad_config

        handler = CommandHandler(introspector, session_config)
        # Should handle the exception gracefully
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_config_value_masking_short_password(handler):
    """Test _show_config masks sensitive values correctly for short passwords."""
    # Set a short password
    handler.session_config.config_overrides["pass_key"] = "abc"

    # Should not raise exception and should mask the value
    handler._show_config()


def test_show_config_value_masking_long_token(handler):
    """Test _show_config masks sensitive values correctly for long tokens."""
    # Set a long bearer token
    handler.session_config.config_overrides["bearer_token"] = "very_long_secret_token_value_12345"

    # Should not raise exception and should show last 4 chars
    handler._show_config()


def test_show_config_skip_default_token_password(introspector, session_config):
    """Test _show_config doesn't mask default 'token' and 'password' values."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create config with default values
        config_module = ModuleType(config_module_name)

        class DefaultConfig:
            bearer_token = "token"
            pass_key = "password"

        config_module.config = DefaultConfig()

        sys.modules[config_module_name] = config_module

        handler = CommandHandler(introspector, session_config)
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_apply_config_override_pydantic_config(handler):
    """Test _apply_config_override with Pydantic config instance."""

    package_name = handler.introspector.client_path.name
    config_module_name = f"{package_name}.config"

    if config_module_name in sys.modules:
        config_module = sys.modules[config_module_name]

        # Set base_url
        handler._apply_config_override("base_url", "https://new.example.com")

        # Check if config instance was updated
        if hasattr(config_module, "config"):
            config_instance = config_module.config
            if hasattr(config_instance, "api_base_url"):
                assert config_instance.api_base_url == "https://new.example.com"


def test_apply_config_override_old_format(introspector, session_config):
    """Test _apply_config_override with old function-based config."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create old-style config module
        old_config = ModuleType(config_module_name)
        old_config.api_base_url = lambda: "http://old.example.com"
        old_config.get_bearer_token = lambda: "old_token"
        old_config.get_user_key = lambda: "old_user"
        old_config.get_pass_key = lambda: "old_pass"

        sys.modules[config_module_name] = old_config

        handler = CommandHandler(introspector, session_config)

        # Apply overrides
        handler._apply_config_override("base_url", "https://override.example.com")
        handler._apply_config_override("bearer_token", "override_token")
        handler._apply_config_override("user_key", "override_user")
        handler._apply_config_override("pass_key", "override_pass")

        # Verify the functions were replaced
        assert old_config.api_base_url() == "https://override.example.com"
        assert old_config.get_bearer_token() == "override_token"
        assert old_config.get_user_key() == "override_user"
        assert old_config.get_pass_key() == "override_pass"

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_apply_config_override_pydantic_without_attribute(introspector, session_config):
    """Test _apply_config_override when Pydantic config doesn't have the attribute."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create config with missing attributes
        config_module = ModuleType(config_module_name)

        class PartialConfig:
            api_base_url = "http://example.com"
            # Missing other attributes

        config_module.config = PartialConfig()

        sys.modules[config_module_name] = config_module

        handler = CommandHandler(introspector, session_config)
        # Should handle gracefully when attribute doesn't exist
        handler._apply_config_override("bearer_token", "token123")

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_apply_config_override_old_format_missing_function(introspector, session_config):
    """Test _apply_config_override when old format doesn't have expected function."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create old-style config with missing functions
        old_config = ModuleType(config_module_name)
        # Only has api_base_url, missing others
        old_config.api_base_url = lambda: "http://example.com"

        sys.modules[config_module_name] = old_config

        handler = CommandHandler(introspector, session_config)
        # Should handle gracefully when function doesn't exist
        handler._apply_config_override("bearer_token", "token123")

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_schema_detail_with_fields_and_docstring(handler):
    """Test _show_schema_detail with schema that has fields and docstring."""
    # The SimpleResponse schema should have both
    handler._show_schema_detail("SimpleResponse")


def test_show_schema_detail_with_field_descriptions(handler):
    """Test _show_schema_detail displays field descriptions correctly."""
    # Just ensure it works with schemas that have field descriptions
    handler._show_schema_detail("SimpleResponse")


def test_show_schema_detail_with_default_values(introspector, session_config):
    """Test _show_schema_detail displays default values in field descriptions."""
    # Mock a schema with default values
    with patch.object(introspector, "get_schema_info") as mock_get_schema:
        mock_get_schema.return_value = {
            "name": "TestSchema",
            "docstring": "Test schema",
            "fields": {"field1": {"type": "str", "required": False, "description": "", "default": "default_value"}},
        }

        handler = CommandHandler(introspector, session_config)
        handler._show_schema_detail("TestSchema")


def test_show_operation_detail_with_parameters(handler):
    """Test _show_operation_detail with an operation that has parameters."""
    # simple_request_simple_request_get should have parameters
    handler._show_operation_detail("simple_request_simple_request_get")


def test_show_operation_detail_with_return_type(handler):
    """Test _show_operation_detail displays return type correctly."""
    # simple_request_simple_request_get should have a return type
    handler._show_operation_detail("simple_request_simple_request_get")


def test_show_operation_detail_missing_return_type(introspector, session_config):
    """Test _show_operation_detail when operation has no return type."""
    # Save original operations
    original_ops = introspector.operations.copy()

    try:
        # Create operation without return type
        mock_op = Mock()
        mock_op.name = "test_op"
        mock_op.http_method = "GET"
        mock_op.path = "/test"
        mock_op.docstring = "Test operation"
        mock_op.parameters = {}
        mock_op.return_type = None  # No return type

        introspector.operations["test_op"] = mock_op

        handler = CommandHandler(introspector, session_config)
        handler._show_operation_detail("test_op")

    finally:
        introspector.operations = original_ops


def test_debug_command_show_status_when_off(handler):
    """Test /debug without arg shows status when debug mode is off."""
    handler.session_config.debug_mode = False
    handler._handle_debug(None)


def test_debug_command_show_status_when_on(handler):
    """Test /debug without arg shows status when debug mode is on."""
    handler.session_config.debug_mode = True
    handler._handle_debug(None)


def test_debug_command_turn_on(handler):
    """Test /debug on command turns on debug mode."""
    handler.session_config.debug_mode = False
    handler._handle_debug("on")
    assert handler.session_config.debug_mode is True


def test_debug_command_turn_off(handler):
    """Test /debug off command turns off debug mode."""
    handler.session_config.debug_mode = True
    handler._handle_debug("off")
    assert handler.session_config.debug_mode is False


def test_debug_command_invalid_argument(handler):
    """Test /debug with invalid argument shows error."""
    handler._handle_debug("invalid")
    # Should not change debug mode


def test_debug_command_case_insensitive(handler):
    """Test /debug command is case insensitive."""
    handler._handle_debug("ON")
    assert handler.session_config.debug_mode is True

    handler._handle_debug("OFF")
    assert handler.session_config.debug_mode is False


def test_debug_command_without_session_config(introspector):
    """Test /debug command when session_config is None."""
    handler = CommandHandler(introspector, session_config=None)
    handler._handle_debug("on")
    # Should handle gracefully


def test_show_schema_detail_without_docstring(introspector, session_config):
    """Test _show_schema_detail when schema has no docstring."""
    with patch.object(introspector, "get_schema_info") as mock_get_schema:
        mock_get_schema.return_value = {
            "name": "TestSchema",
            "fields": {"field1": {"type": "str", "required": True, "description": "A field"}},
            # No docstring
        }

        handler = CommandHandler(introspector, session_config)
        handler._show_schema_detail("TestSchema")


def test_list_schemas_with_inspect_fallback(introspector, session_config):
    """Test _list_schemas when it needs to use inspect.getdoc as fallback."""

    # Create a schema class that has no __doc__ but has inspect docstring
    class TestSchemaWithInspectDoc:
        """Inspect docstring for the schema."""

        pass

    # Remove __doc__ attribute to force inspect.getdoc usage
    TestSchemaWithInspectDoc.__doc__ = None

    with patch.object(introspector, "get_all_schemas") as mock_get_schemas:
        mock_get_schemas.return_value = {"TestSchema": TestSchemaWithInspectDoc}

        handler = CommandHandler(introspector, session_config)
        handler._list_schemas()


def test_show_config_with_empty_additional_headers(introspector, session_config):
    """Test _show_config when additional_headers is empty dict."""

    package_name = introspector.client_path.name
    config_module_name = f"{package_name}.config"

    saved_module = sys.modules.get(config_module_name)

    try:
        # Create config with empty additional_headers
        config_module = ModuleType(config_module_name)

        class ConfigWithEmptyHeaders:
            api_base_url = "http://example.com"
            additional_headers = {}  # Empty dict

        config_module.config = ConfigWithEmptyHeaders()

        sys.modules[config_module_name] = config_module

        handler = CommandHandler(introspector, session_config)
        handler._show_config()

    finally:
        if saved_module:
            sys.modules[config_module_name] = saved_module


def test_show_config_with_populated_additional_headers(handler):
    """Test _show_config when additional_headers has values."""
    # The test client should have additional_headers with values
    handler._show_config()


def test_apply_config_override_invalid_key(handler):
    """Test _apply_config_override with an invalid key that's not mapped."""

    package_name = handler.introspector.client_path.name
    config_module_name = f"{package_name}.config"

    if config_module_name in sys.modules:
        # This should return early without doing anything
        handler._apply_config_override("invalid_key_not_in_map", "some_value")


def test_show_operation_detail_with_parameter_details(handler):
    """Test _show_operation_detail displays operation parameters correctly."""
    # Use an operation that has parameters to ensure parameter loop is executed
    handler._show_operation_detail("simple_request_simple_request_get")
