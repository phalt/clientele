"""Tests for the non-decorator endpoint API."""

from __future__ import annotations

import inspect
import json

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele import Client, endpoint

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


class CreateUserRequest(BaseModel):
    name: str


class ErrorResponse(BaseModel):
    error: str
    code: int


class ValidationErrorResponse(BaseModel):
    errors: list[str]


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_get_basic(respx_mock: MockRouter) -> None:
    """Test basic GET endpoint without signature decorator."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    # Create and bind endpoint
    get_user = endpoint.get("/users/{user_id}")
    get_user = get_user.bind(client)

    # Call it
    result = get_user(user_id=1)

    # Verify the request was made and result is correct
    assert respx_mock.calls[0].request.url.path == "/users/1"
    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["name"] == "Alice"


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_get_with_signature(respx_mock: MockRouter) -> None:
    """Test GET endpoint with signature decorator."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    # Create endpoint with signature
    get_user_ep = endpoint.get("/users/{user_id}")

    @get_user_ep.signature
    def _(user_id: int, expand: bool = False) -> User:  # type: ignore[return]
        ...

    get_user = get_user_ep.bind(client)

    # Verify signature is preserved
    sig = inspect.signature(get_user)
    params = list(sig.parameters.keys())
    assert params == ["user_id", "expand"]
    assert sig.parameters["expand"].default is False

    # Call it
    _ = get_user(user_id=1)

    assert respx_mock.calls[0].request.url.path == "/users/1"


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_get_with_query_params(respx_mock: MockRouter) -> None:
    """Test GET endpoint with query parameters."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
    )

    list_users_ep = endpoint.get("/users")

    @list_users_ep.signature
    def _(page: int = 1, per_page: int = 10) -> list[User]:  # type: ignore[return]
        ...

    list_users = list_users_ep.bind(client)

    _ = list_users(page=2, per_page=5)

    call = respx_mock.calls[0]
    assert call.request.url.params.get("page") == "2"
    assert call.request.url.params.get("per_page") == "5"


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_post_with_data(respx_mock: MockRouter) -> None:
    """Test POST endpoint with request body."""
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 3, "name": "Charlie"}))

    create_user_ep = endpoint.post("/users")

    @create_user_ep.signature
    def _(data: CreateUserRequest) -> User:  # type: ignore[return]
        ...

    create_user = create_user_ep.bind(client)

    _ = create_user(data=CreateUserRequest(name="Charlie"))

    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "Charlie"}


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_put_with_path_and_data(respx_mock: MockRouter) -> None:
    """Test PUT endpoint with path parameter and request body."""
    client = Client(base_url=BASE_URL)

    respx_mock.put("/users/3").mock(return_value=httpx.Response(200, json={"id": 3, "name": "Charlie Updated"}))

    update_user_ep = endpoint.put("/users/{user_id}")

    @update_user_ep.signature
    def _(user_id: int, data: CreateUserRequest) -> User:  # type: ignore[return]
        ...

    update_user = update_user_ep.bind(client)

    _ = update_user(user_id=3, data=CreateUserRequest(name="Charlie Updated"))

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/3"
    assert json.loads(call.request.content) == {"name": "Charlie Updated"}


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_delete(respx_mock: MockRouter) -> None:
    """Test DELETE endpoint."""
    client = Client(base_url=BASE_URL)

    respx_mock.delete("/users/3").mock(return_value=httpx.Response(204))

    delete_user_ep = endpoint.delete("/users/{user_id}")

    @delete_user_ep.signature
    def _(user_id: int) -> None:  # type: ignore[return]
        ...

    delete_user = delete_user_ep.bind(client)

    result = delete_user(user_id=3)

    assert result is None
    assert respx_mock.calls[0].request.url.path == "/users/3"


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_patch(respx_mock: MockRouter) -> None:
    """Test PATCH endpoint."""
    client = Client(base_url=BASE_URL)

    respx_mock.patch("/users/3").mock(return_value=httpx.Response(200, json={"id": 3, "name": "Partial"}))

    patch_user_ep = endpoint.patch("/users/{user_id}")

    @patch_user_ep.signature
    def _(user_id: int, data: CreateUserRequest) -> User:  # type: ignore[return]
        ...

    patch_user = patch_user_ep.bind(client)

    _ = patch_user(user_id=3, data={"name": "Partial"})

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/3"


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_with_response_map(respx_mock: MockRouter) -> None:
    """Test endpoint with response_map for error handling."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "Not found", "code": 404}))

    get_user_ep = endpoint.get("/users/{user_id}", response_map={200: User, 404: ErrorResponse})

    @get_user_ep.signature
    def _(user_id: int) -> User | ErrorResponse:  # type: ignore[return]
        ...

    get_user = get_user_ep.bind(client)

    result = get_user(user_id=999)

    assert isinstance(result, ErrorResponse)
    assert result.code == 404


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_with_headers(respx_mock: MockRouter) -> None:
    """Test endpoint with custom headers."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    get_user_ep = endpoint.get("/users/{user_id}")

    @get_user_ep.signature
    def _(user_id: int) -> User:  # type: ignore[return]
        ...

    get_user = get_user_ep.bind(client)

    _ = get_user(user_id=1, headers={"X-Custom": "value"})

    call = respx_mock.calls[0]
    assert call.request.headers["X-Custom"] == "value"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_endpoint_async(respx_mock: MockRouter) -> None:
    """Test async endpoint."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Async User"}))

    get_user_ep = endpoint.get("/users/{user_id}")

    @get_user_ep.signature
    async def _(user_id: int) -> User:  # type: ignore[return]
        ...

    get_user = get_user_ep.bind(client)

    _ = await get_user(user_id=1)

    assert respx_mock.calls[0].request.url.path == "/users/1"


def test_endpoint_signature_chain_returns_self() -> None:
    """Test that .signature() returns self for chaining."""
    ep = endpoint.get("/users")

    result = ep.signature(lambda: ...)  # type: ignore[arg-type]

    assert result is ep


def test_endpoint_signature_preservation() -> None:
    """Test that signatures are correctly preserved for IDE support."""
    client = Client(base_url=BASE_URL)

    get_user_ep = endpoint.get("/users/{user_id}")

    @get_user_ep.signature
    def _(user_id: int, expand: bool = False, filter: str | None = None) -> User:  # type: ignore[return]
        """Get a user by ID."""
        ...

    get_user = get_user_ep.bind(client)

    # Check signature
    sig = inspect.signature(get_user)
    params = list(sig.parameters.keys())
    assert params == ["user_id", "expand", "filter"]

    # Check parameter details
    assert sig.parameters["user_id"].default == inspect.Parameter.empty
    assert sig.parameters["expand"].default is False
    assert sig.parameters["filter"].default is None

    # Check docstring
    assert get_user.__doc__ == "Get a user by ID."


@pytest.mark.respx(base_url=BASE_URL)
def test_endpoint_response_map_multiple_status_codes(respx_mock: MockRouter) -> None:
    """Test endpoint with multiple status codes in response_map."""
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(422, json={"errors": ["Invalid input"]}))

    create_user_ep = endpoint.post("/users", response_map={201: User, 400: ErrorResponse, 422: ValidationErrorResponse})

    @create_user_ep.signature
    def _(data: CreateUserRequest) -> User | ErrorResponse | ValidationErrorResponse:  # type: ignore[return]
        ...

    create_user = create_user_ep.bind(client)

    result = create_user(data=CreateUserRequest(name="Test"))

    assert isinstance(result, ValidationErrorResponse)
    assert result.errors == ["Invalid input"]
