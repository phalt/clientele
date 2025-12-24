"""Tests for the RequestExecutor class."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from clientele.explore.executor import ExecutionResult, RequestExecutor
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


def test_executor_initialization(introspector):
    """Test executor initializes correctly."""
    executor = RequestExecutor(introspector)
    assert executor.introspector is introspector
    assert executor.session_config is None


def test_executor_initialization_with_session_config(introspector):
    """Test executor initializes with session config."""
    session_config = SessionConfig()
    executor = RequestExecutor(introspector, session_config)
    assert executor.introspector is introspector
    assert executor.session_config is session_config


def test_execute_nonexistent_operation(introspector):
    """Test executing a non-existent operation."""
    executor = RequestExecutor(introspector)
    result = executor.execute("nonexistent_operation", {})

    assert result.success is False
    assert result.response is None
    assert result.operation == "nonexistent_operation"
    assert isinstance(result.error, ValueError)
    assert "Operation not found" in str(result.error)


def test_execute_with_missing_required_parameter(introspector):
    """Test executing operation with missing required parameter."""
    executor = RequestExecutor(introspector)
    # parameter_request_simple_request requires 'your_input' parameter
    result = executor.execute("parameter_request_simple_request", {})

    assert result.success is False
    assert result.response is None
    assert isinstance(result.error, ValueError)
    assert "Missing required parameter" in str(result.error)


def test_execute_with_unknown_parameter(introspector):
    """Test executing operation with unknown parameter."""
    executor = RequestExecutor(introspector)
    result = executor.execute("parameter_request_simple_request", {"your_input": "test", "unknown_param": "value"})

    assert result.success is False
    assert result.response is None
    assert isinstance(result.error, ValueError)
    assert "Unknown parameter" in str(result.error)


def test_execute_with_debug_mode(introspector):
    """Test executing operation with debug mode enabled."""
    session_config = SessionConfig()
    session_config.debug_mode = True
    executor = RequestExecutor(introspector, session_config)

    # Use an operation that exists but will fail when called
    # This tests that debug info is populated
    result = executor.execute("parameter_request_simple_request", {"your_input": "test"})

    # Debug info should be populated even on error
    assert result.debug_info is not None
    assert "operation" in result.debug_info
    assert result.debug_info["operation"] == "parameter_request_simple_request"


def test_execute_with_debug_mode_disabled(introspector):
    """Test executing operation with debug mode disabled."""
    session_config = SessionConfig()
    session_config.debug_mode = False
    executor = RequestExecutor(introspector, session_config)

    result = executor.execute("parameter_request_simple_request", {"your_input": "test"})

    # Debug info should be None when debug mode is off
    assert result.debug_info is None


def test_execution_result_dataclass():
    """Test ExecutionResult dataclass creation."""
    result = ExecutionResult(
        success=True,
        response={"data": "test"},
        duration=0.5,
        operation="test_op",
        error=None,
        debug_info={"method": "GET"},
    )

    assert result.success is True
    assert result.response == {"data": "test"}
    assert result.duration == 0.5
    assert result.operation == "test_op"
    assert result.error is None
    assert result.debug_info == {"method": "GET"}


def test_execution_result_with_error():
    """Test ExecutionResult with error."""
    error = RuntimeError("Test error")
    result = ExecutionResult(
        success=False,
        response=None,
        duration=0.5,
        operation="test_op",
        error=error,
    )

    assert result.success is False
    assert result.response is None
    assert result.error is error
    assert result.debug_info is None


def test_validate_args_with_valid_args():
    """Test argument validation with valid arguments."""
    # Create a mock operation info
    mock_op_info = Mock()
    mock_op_info.parameters = {
        "id": {"type": int, "required": True, "default": None},
        "name": {"type": str, "required": False, "default": "default"},
    }

    executor = RequestExecutor(Mock())
    # Should not raise any exception
    executor._validate_args(mock_op_info, {"id": 123, "name": "test"})


def test_validate_args_with_missing_optional():
    """Test argument validation with missing optional parameter."""
    mock_op_info = Mock()
    mock_op_info.parameters = {
        "id": {"type": int, "required": True, "default": None},
        "name": {"type": str, "required": False, "default": "default"},
    }

    executor = RequestExecutor(Mock())
    # Should not raise exception when optional parameter is missing
    executor._validate_args(mock_op_info, {"id": 123})


def test_validate_args_with_all_optional():
    """Test argument validation with all optional parameters."""
    mock_op_info = Mock()
    mock_op_info.parameters = {
        "limit": {"type": int, "required": False, "default": 10},
        "offset": {"type": int, "required": False, "default": 0},
    }

    executor = RequestExecutor(Mock())
    # Should not raise exception when no args provided for all optional
    executor._validate_args(mock_op_info, {})


def test_convert_dict_to_pydantic_model(introspector):
    """Test converting dict to Pydantic model for data parameter."""
    executor = RequestExecutor(introspector)

    # Get operation that expects a Pydantic model
    op_info = introspector.operations.get("request_data_request_data_post")

    # Test with dict argument
    args = {"data": {"my_input": "test", "my_decimal_input": 3.14}}
    converted_args = executor._convert_dict_args_to_models(op_info, args)

    # Should convert dict to Pydantic model
    assert "data" in converted_args
    assert hasattr(converted_args["data"], "model_dump")
    assert converted_args["data"].my_input == "test"


def test_convert_dict_preserves_non_dict_args(introspector):
    """Test that non-dict arguments are preserved unchanged."""
    executor = RequestExecutor(introspector)

    # Get operation with string parameter
    op_info = introspector.operations.get("parameter_request_simple_request")

    # Test with string argument
    args = {"your_input": "test"}
    converted_args = executor._convert_dict_args_to_models(op_info, args)

    # Should preserve string argument
    assert converted_args == args
    assert isinstance(converted_args["your_input"], str)


def test_convert_dict_handles_optional_pydantic_model(introspector):
    """Test converting dict to optional Pydantic model."""
    executor = RequestExecutor(introspector)

    # Get operation with optional Pydantic parameter
    op_info = introspector.operations.get("header_request_header_request_get")

    # Test with dict argument (use correct field name from schema)
    args = {"headers": {"x_test": "value"}}
    converted_args = executor._convert_dict_args_to_models(op_info, args)

    # Should convert dict to Pydantic model even if optional
    assert "headers" in converted_args
    assert hasattr(converted_args["headers"], "model_dump")


def test_convert_dict_invalid_model_data_raises_error(introspector):
    """Test that invalid dict data raises helpful error."""
    executor = RequestExecutor(introspector)

    # Get operation that expects a Pydantic model
    op_info = introspector.operations.get("request_data_request_data_post")

    # Test with invalid dict (missing required field)
    args = {"data": {"invalid_field": "test"}}

    with pytest.raises(ValueError, match="Failed to convert dict"):
        executor._convert_dict_args_to_models(op_info, args)


def test_is_pydantic_model(introspector):
    """Test identifying Pydantic models."""
    executor = RequestExecutor(introspector)

    # Get a Pydantic model from schemas
    schemas = introspector.get_all_schemas()
    request_data_model = schemas["RequestDataRequest"]

    # Should identify as Pydantic model
    assert executor._is_pydantic_model(request_data_model)

    # Should not identify non-models
    assert not executor._is_pydantic_model(str)
    assert not executor._is_pydantic_model(dict)
    assert not executor._is_pydantic_model(int)
