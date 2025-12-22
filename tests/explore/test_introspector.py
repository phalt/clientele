"""Tests for clientele.explore.introspector module."""

from unittest.mock import Mock

from clientele.explore.introspector import ClientIntrospector, OperationInfo


def test_operation_info_creation():
    """Test OperationInfo data class."""
    op_info = OperationInfo(
        name="test_operation",
        method=Mock(),
        signature="test_operation(id: int)",
        parameters={"id": int},
        docstring="Test operation",
        http_method="GET",
    )

    assert op_info.name == "test_operation"
    assert op_info.signature == "test_operation(id: int)"
    assert op_info.parameters == {"id": int}
    assert op_info.docstring == "Test operation"
    assert op_info.http_method == "GET"


def test_introspector_initialization():
    """Test ClientIntrospector initialization."""
    mock_client = Mock()
    mock_schemas = Mock()

    introspector = ClientIntrospector(mock_client, mock_schemas)

    assert introspector.client_module == mock_client
    assert introspector.schemas_module == mock_schemas
    assert introspector.operations == {}
    assert introspector.schemas == {}


def test_discover_operations():
    """Test discovering operations from client."""
    # Create mock client with operations
    mock_client = Mock()

    def mock_get_user(id: int) -> dict:
        """Get user by ID."""
        pass

    def mock_list_users(limit: int = 10) -> list:
        """List all users."""
        pass

    # Set up mock client attributes
    mock_client.get_user = mock_get_user
    mock_client.list_users = mock_list_users
    mock_client._internal_method = lambda: None  # Should be ignored

    mock_schemas = Mock()
    introspector = ClientIntrospector(mock_client, mock_schemas)
    introspector._discover_operations()

    assert "get_user" in introspector.operations
    assert "list_users" in introspector.operations
    assert "_internal_method" not in introspector.operations


def test_discover_schemas():
    """Test discovering schemas from module."""
    # Create mock schemas module
    mock_schemas = Mock()

    # Create mock Pydantic models
    mock_user_model = type(
        "User",
        (),
        {
            "__doc__": "User model",
            "model_fields": {
                "id": Mock(annotation=int, is_required=lambda: True),
                "name": Mock(annotation=str, is_required=lambda: True),
            },
        },
    )

    mock_post_model = type(
        "Post",
        (),
        {
            "__doc__": "Post model",
            "model_fields": {
                "id": Mock(annotation=int, is_required=lambda: True),
                "title": Mock(annotation=str, is_required=lambda: False),
            },
        },
    )

    # Set up schema module
    mock_schemas.User = mock_user_model
    mock_schemas.Post = mock_post_model
    mock_schemas._internal = "should be ignored"

    mock_client = Mock()
    introspector = ClientIntrospector(mock_client, mock_schemas)
    introspector._discover_schemas()

    assert "User" in introspector.schemas
    assert "Post" in introspector.schemas


def test_get_operation_signature():
    """Test getting operation signature."""
    mock_client = Mock()

    def test_func(id: int, name: str = "default") -> dict:
        """Test function."""
        pass

    mock_client.test_func = test_func

    mock_schemas = Mock()
    introspector = ClientIntrospector(mock_client, mock_schemas)

    signature = introspector._get_operation_signature(test_func)
    assert "id" in signature
    assert "name" in signature
