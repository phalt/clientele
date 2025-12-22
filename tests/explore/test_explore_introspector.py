"""Tests for clientele.explore.introspector module."""

from unittest.mock import MagicMock, Mock
from types import ModuleType
import inspect

import pytest

from clientele.explore.introspector import ClientIntrospector, OperationInfo


@pytest.fixture
def mock_client():
    """Create a mock client module."""
    client = ModuleType("mock_client")
    
    # Add mock operations
    def get_users(id: int = None):
        """Get users from the API."""
        pass
    
    def create_user(name: str, email: str):
        """Create a new user."""
        pass
    
    async def async_operation(param: str):
        """Async operation."""
        pass
    
    def _private_method():
        """Private method that should be filtered."""
        pass
    
    client.get_users = get_users
    client.create_user = create_user
    client.async_operation = async_operation
    client._private_method = _private_method
    
    return client


@pytest.fixture
def mock_schemas():
    """Create a mock schemas module."""
    schemas = ModuleType("mock_schemas")
    
    # Add mock schema classes
    class User:
        pass
    
    class Post:
        pass
    
    schemas.User = User
    schemas.Post = Post
    
    return schemas


@pytest.fixture
def introspector(mock_client, mock_schemas):
    """Create a ClientIntrospector instance."""
    return ClientIntrospector(mock_client, mock_schemas)


def test_get_operations(introspector):
    """Test getting all operations from client."""
    operations = introspector.get_operations()
    
    assert len(operations) == 3  # get_users, create_user, async_operation
    assert "get_users" in operations
    assert "create_user" in operations
    assert "async_operation" in operations
    assert "_private_method" not in operations  # Private methods excluded


def test_get_operation_info(introspector):
    """Test getting operation information."""
    info = introspector.get_operation_info("get_users")
    
    assert isinstance(info, OperationInfo)
    assert info.name == "get_users"
    assert info.doc == "Get users from the API."
    assert "id" in info.signature


def test_get_operation_info_nonexistent(introspector):
    """Test getting info for nonexistent operation."""
    info = introspector.get_operation_info("nonexistent")
    assert info is None


def test_get_schemas(introspector):
    """Test getting all schema names."""
    schemas = introspector.get_schemas()
    
    assert len(schemas) == 2
    assert "User" in schemas
    assert "Post" in schemas


def test_get_schema_info(introspector):
    """Test getting schema information."""
    info = introspector.get_schema_info("User")
    
    assert info is not None
    assert "User" in str(info)


def test_get_schema_info_nonexistent(introspector):
    """Test getting info for nonexistent schema."""
    info = introspector.get_schema_info("NonExistent")
    assert info is None


def test_operation_info_dataclass():
    """Test OperationInfo dataclass."""
    info = OperationInfo(
        name="test_op",
        signature="test_op(param: str)",
        doc="Test operation",
        http_method="GET"
    )
    
    assert info.name == "test_op"
    assert info.signature == "test_op(param: str)"
    assert info.doc == "Test operation"
    assert info.http_method == "GET"


def test_async_operation_detection(introspector):
    """Test that async operations are properly detected."""
    operations = introspector.get_operations()
    assert "async_operation" in operations


def test_empty_client():
    """Test introspector with empty client."""
    empty_client = ModuleType("empty")
    empty_schemas = ModuleType("empty_schemas")
    
    introspector = ClientIntrospector(empty_client, empty_schemas)
    
    assert len(introspector.get_operations()) == 0
    assert len(introspector.get_schemas()) == 0
