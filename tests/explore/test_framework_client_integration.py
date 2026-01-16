"""Integration tests for explorer with framework-based (decorator) clients."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clientele.explore.executor import RequestExecutor
from clientele.explore.introspector import ClientIntrospector
from clientele.explore.session import SessionConfig


@pytest.fixture
def framework_client_dir():
    """Create a temporary framework-based client for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        client_dir = Path(tmpdir) / "test_client"
        client_dir.mkdir()

        # Create __init__.py
        (client_dir / "__init__.py").write_text("")

        # Create config.py
        config_content = """
from clientele.api import BaseConfig

class Config(BaseConfig):
    base_url: str = "http://localhost:8000"
    headers: dict = {}
    timeout: float = 5.0
"""
        (client_dir / "config.py").write_text(config_content)

        # Create schemas.py
        schemas_content = """
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class CreateUserRequest(BaseModel):
    name: str
    email: str
"""
        (client_dir / "schemas.py").write_text(schemas_content)

        # Create client.py with framework-based decorators
        client_content = """
from __future__ import annotations

import clientele
from test_client import config, schemas

client = clientele.api.APIClient(config=config.Config())

@client.get("/users")
def list_users(result: list[schemas.User]) -> list[schemas.User]:
    '''List all users.'''
    return result

@client.post("/users")
def create_user(data: schemas.CreateUserRequest, result: schemas.User) -> schemas.User:
    '''Create a new user.'''
    return result

@client.get("/users/{user_id}")
def get_user(user_id: int, result: schemas.User) -> schemas.User:
    '''Get a specific user by ID.'''
    return result
"""
        (client_dir / "client.py").write_text(client_content)

        yield client_dir


def test_introspector_loads_framework_client(framework_client_dir):
    """Test that introspector can load a framework-based client."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()

    assert introspector.client_module is not None
    assert introspector.schemas_module is not None
    assert not introspector.is_class_based


def test_introspector_discovers_framework_operations(framework_client_dir):
    """Test that introspector discovers operations from framework-based client."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()
    operations = introspector.discover_operations()

    assert len(operations) == 3
    assert "list_users" in operations
    assert "create_user" in operations
    assert "get_user" in operations

    # Check operation details
    list_users_op = operations["list_users"]
    assert list_users_op.name == "list_users"
    assert list_users_op.http_method == "GET"
    assert list_users_op.docstring == "List all users."
    assert len(list_users_op.parameters) == 0

    get_user_op = operations["get_user"]
    assert get_user_op.name == "get_user"
    assert get_user_op.http_method == "GET"
    assert "user_id" in get_user_op.parameters
    assert get_user_op.parameters["user_id"]["required"] is True

    create_user_op = operations["create_user"]
    assert create_user_op.name == "create_user"
    assert create_user_op.http_method == "POST"
    assert "data" in create_user_op.parameters


def test_executor_can_call_framework_operations(framework_client_dir):
    """Test that executor can successfully call framework-based operations."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()
    introspector.discover_operations()

    config = SessionConfig()
    executor = RequestExecutor(introspector, config)

    # Mock the actual HTTP call
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.content = b'[{"id": 1, "name": "Alice", "email": "alice@example.com"}]'
    mock_response.text = '[{"id": 1, "name": "Alice", "email": "alice@example.com"}]'

    # Patch the request method on the singleton httpx.Client instance
    with patch.object(
        introspector.client_module.client.config.http_backend._sync_client,  # type: ignore
        "request",
        return_value=mock_response,
    ):
        # Execute the operation
        result = executor.execute("list_users", {})

        assert result.success is True
        assert result.error is None
        assert result.operation == "list_users"
        assert result.duration > 0


def test_executor_validates_framework_operation_args(framework_client_dir):
    """Test that executor validates arguments for framework-based operations."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()
    introspector.discover_operations()

    config = SessionConfig()
    executor = RequestExecutor(introspector, config)

    # Try to call get_user without required user_id
    result = executor.execute("get_user", {})

    assert result.success is False
    assert result.error is not None
    assert "Missing required parameter: user_id" in str(result.error)


def test_executor_converts_dict_to_pydantic_model(framework_client_dir):
    """Test that executor converts dict arguments to Pydantic models for framework clients."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()
    introspector.discover_operations()

    config = SessionConfig()
    executor = RequestExecutor(introspector, config)

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 3, "name": "Charlie", "email": "charlie@test.com"}
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.content = b'{"id": 3, "name": "Charlie", "email": "charlie@test.com"}'
    mock_response.text = '{"id": 3, "name": "Charlie", "email": "charlie@test.com"}'

    # Patch the request method on the singleton httpx.Client instance
    with patch.object(
        introspector.client_module.client.config.http_backend._sync_client,  # type: ignore
        "request",
        return_value=mock_response,
    ):
        # Pass data as dict - should be converted to CreateUserRequest
        result = executor.execute("create_user", {"data": {"name": "Charlie", "email": "charlie@test.com"}})

        assert result.success is True
        # The executor should have converted the dict to a Pydantic model


def test_framework_client_with_debug_mode(framework_client_dir):
    """Test that debug mode works with framework-based clients."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()
    introspector.discover_operations()

    config = SessionConfig()
    config.debug_mode = True
    executor = RequestExecutor(introspector, config)

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.content = b"[]"
    mock_response.text = "[]"

    # Patch the request method on the singleton httpx.Client instance
    with patch.object(
        introspector.client_module.client.config.http_backend._sync_client,  # type: ignore
        "request",
        return_value=mock_response,
    ):
        result = executor.execute("list_users", {})

        assert result.success is True
        assert result.debug_info is not None
        assert "operation" in result.debug_info
        assert result.debug_info["operation"] == "list_users"
        assert "method" in result.debug_info
        assert result.debug_info["method"] == "GET"


def test_introspector_discovers_schemas_from_framework_client(framework_client_dir):
    """Test that introspector can discover schemas from framework-based client."""
    introspector = ClientIntrospector(framework_client_dir)
    introspector.load_client()

    schemas = introspector.get_all_schemas()

    assert len(schemas) >= 2
    assert "User" in schemas
    assert "CreateUserRequest" in schemas

    # Check schema details
    user_info = introspector.get_schema_info("User")
    assert user_info is not None
    assert "id" in user_info["fields"]
    assert "name" in user_info["fields"]
    assert "email" in user_info["fields"]
