"""Tests for clientele.explore.executor module."""

import asyncio
from unittest.mock import MagicMock, Mock, patch
from types import ModuleType

import pytest

from clientele.explore.executor import RequestExecutor, ExecutionResult
from clientele.explore.session import SessionConfig


@pytest.fixture
def session():
    """Create a SessionConfig instance."""
    return SessionConfig()


@pytest.fixture
def mock_client():
    """Create a mock client module."""
    client = ModuleType("mock_client")
    
    def sync_operation(param: str):
        """Synchronous operation."""
        return {"result": param}
    
    async def async_operation(param: str):
        """Asynchronous operation."""
        await asyncio.sleep(0.001)
        return {"async_result": param}
    
    def failing_operation():
        """Operation that raises an error."""
        raise ValueError("Operation failed")
    
    client.sync_operation = sync_operation
    client.async_operation = async_operation
    client.failing_operation = failing_operation
    
    return client


@pytest.fixture
def executor(session, mock_client):
    """Create a RequestExecutor instance."""
    return RequestExecutor(session, mock_client)


def test_execute_sync_operation(executor):
    """Test executing a synchronous operation."""
    result = executor.execute("sync_operation", {"param": "test"})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.data == {"result": "test"}
    assert result.error is None
    assert result.duration > 0


def test_execute_async_operation(executor):
    """Test executing an asynchronous operation."""
    result = executor.execute("async_operation", {"param": "async_test"})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.data == {"async_result": "async_test"}
    assert result.error is None


def test_execute_failing_operation(executor):
    """Test executing an operation that raises an error."""
    result = executor.execute("failing_operation", {})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is False
    assert result.data is None
    assert isinstance(result.error, ValueError)
    assert "Operation failed" in str(result.error)


def test_execute_nonexistent_operation(executor):
    """Test executing a nonexistent operation."""
    result = executor.execute("nonexistent_op", {})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is False
    assert result.error is not None


def test_execute_with_debug_mode(session, mock_client):
    """Test executing with debug mode enabled."""
    session.debug = True
    executor = RequestExecutor(session, mock_client)
    
    result = executor.execute("sync_operation", {"param": "debug_test"})
    
    assert result.success is True
    assert result.debug_info is not None
    assert "operation" in result.debug_info
    assert result.debug_info["operation"] == "sync_operation"


def test_execute_with_config_overrides(session, mock_client):
    """Test executing with session config overrides."""
    session.set_config("base_url", "https://test.api")
    executor = RequestExecutor(session, mock_client)
    
    # Config overrides should be available in session
    assert session.config_overrides["base_url"] == "https://test.api"


def test_execution_result_dataclass():
    """Test ExecutionResult dataclass."""
    result = ExecutionResult(
        success=True,
        data={"test": "data"},
        error=None,
        duration=0.123,
        debug_info=None
    )
    
    assert result.success is True
    assert result.data == {"test": "data"}
    assert result.error is None
    assert result.duration == 0.123


def test_execute_timing(executor):
    """Test that execution timing is recorded."""
    result = executor.execute("sync_operation", {"param": "test"})
    
    assert result.duration > 0
    assert isinstance(result.duration, float)


def test_execute_with_empty_args(executor):
    """Test executing operation with empty arguments."""
    def no_args_op():
        return "success"
    
    executor.client.no_args_op = no_args_op
    result = executor.execute("no_args_op", {})
    
    assert result.success is True
    assert result.data == "success"


@pytest.mark.asyncio
async def test_async_operation_with_asyncio(mock_client):
    """Test that async operations work correctly."""
    result = await mock_client.async_operation("test")
    assert result == {"async_result": "test"}
