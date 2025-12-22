"""Tests for clientele.explore.executor module."""

from unittest.mock import Mock, patch

from clientele.explore.executor import ExecutionResult, RequestExecutor
from clientele.explore.session import SessionConfig


def test_execution_result_creation():
    """Test ExecutionResult data class."""
    result = ExecutionResult(success=True, response={"key": "value"}, duration=0.5, error=None, debug_info=None)

    assert result.success is True
    assert result.response == {"key": "value"}
    assert result.duration == 0.5
    assert result.error is None
    assert result.debug_info is None


def test_executor_initialization():
    """Test RequestExecutor initialization."""
    introspector = Mock()
    config = Mock()

    executor = RequestExecutor(introspector, config)

    assert executor.introspector == introspector
    assert executor.config_module == config


def test_execute_sync_operation_success():
    """Test executing synchronous operation successfully."""
    # Setup
    mock_operation = Mock(return_value={"result": "success"})
    mock_introspector = Mock()
    mock_introspector.operations = {"test_op": Mock(method=mock_operation, http_method="GET")}
    mock_config = Mock()

    executor = RequestExecutor(mock_introspector, mock_config)

    # Execute
    result = executor.execute("test_op", id=1, name="test")

    # Verify
    assert result.success is True
    assert result.response == {"result": "success"}
    assert result.error is None
    mock_operation.assert_called_once_with(id=1, name="test")


def test_execute_async_operation_success():
    """Test executing async operation successfully."""

    # Setup async operation
    async def async_operation(id: int):
        return {"result": "async_success"}

    mock_introspector = Mock()
    mock_introspector.operations = {"async_op": Mock(method=async_operation, http_method="GET")}
    mock_config = Mock()

    executor = RequestExecutor(mock_introspector, mock_config)

    # Execute
    with patch("clientele.explore.executor.inspect.iscoroutinefunction", return_value=True):
        with patch("clientele.explore.executor.asyncio.run", return_value={"result": "async_success"}):
            result = executor.execute("async_op", id=1)

    # Verify
    assert result.success is True
    assert result.response == {"result": "async_success"}


def test_execute_operation_error():
    """Test executing operation that raises error."""

    # Setup
    def error_operation(id: int):
        raise ValueError("Test error")

    mock_introspector = Mock()
    mock_introspector.operations = {"error_op": Mock(method=error_operation, http_method="POST")}
    mock_config = Mock()

    executor = RequestExecutor(mock_introspector, mock_config)

    # Execute
    result = executor.execute("error_op", id=1)

    # Verify
    assert result.success is False
    assert result.response is None
    assert isinstance(result.error, ValueError)
    assert "Test error" in str(result.error)


def test_execute_with_debug_mode():
    """Test executing with debug mode enabled."""
    # Setup
    mock_operation = Mock(return_value={"result": "ok"})
    mock_introspector = Mock()
    mock_introspector.operations = {"debug_op": Mock(method=mock_operation, http_method="GET")}
    mock_config = Mock()
    mock_config.api_base_url = Mock(return_value="https://api.test.com")

    session_config = SessionConfig(debug_mode=True)
    executor = RequestExecutor(mock_introspector, mock_config, session_config)

    # Execute
    result = executor.execute("debug_op", id=1)

    # Verify debug info is included
    assert result.success is True
    assert result.debug_info is not None
    assert "operation" in result.debug_info
    assert result.debug_info["operation"] == "debug_op"


def test_execute_nonexistent_operation():
    """Test executing operation that doesn't exist."""
    mock_introspector = Mock()
    mock_introspector.operations = {}
    mock_config = Mock()

    executor = RequestExecutor(mock_introspector, mock_config)

    # Execute
    result = executor.execute("nonexistent_op")

    # Verify
    assert result.success is False
    assert result.error is not None


def test_execute_with_config_override():
    """Test executing with runtime config override."""
    mock_operation = Mock(return_value={"result": "ok"})
    mock_introspector = Mock()
    mock_introspector.operations = {"test_op": Mock(method=mock_operation, http_method="GET")}
    mock_config = Mock()
    mock_config.api_base_url = Mock(return_value="https://default.com")

    # Session with config override
    session_config = SessionConfig(config_overrides={"base_url": "https://override.com"})
    executor = RequestExecutor(mock_introspector, mock_config, session_config)

    # Execute
    result = executor.execute("test_op")

    # Verify it doesn't crash with overrides
    assert result.success is True
