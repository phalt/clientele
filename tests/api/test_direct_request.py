"""Tests for direct request() and arequest() methods without decorators."""
from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import APIClient

BASE_URL = "https://api.example.com"


class Pokemon(BaseModel):
    id: int
    name: str


class User(BaseModel):
    id: int
    name: str


class CreateUserRequest(BaseModel):
    name: str
    email: str


class SuccessResponse(BaseModel):
    id: int
    name: str
    status: str = "success"


class ErrorResponse(BaseModel):
    error: str
    code: int


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_get_basic(respx_mock: MockRouter) -> None:
    """Test basic GET request without decorator."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/pokemon/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Bulbasaur"})
    )

    result = client.request("GET", "/pokemon/{id}", response_map={200: Pokemon}, id=1)

    assert isinstance(result, Pokemon)
    assert result.id == 1
    assert result.name == "Bulbasaur"


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_get_with_query_params(respx_mock: MockRouter) -> None:
    """Test GET request with query parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alice"})
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        query={"include_details": "true"},
        user_id=1,
    )

    assert isinstance(result, User)
    assert result.id == 1
    assert result.name == "Alice"

    call = respx_mock.calls[0]
    assert call.request.url.params.get("include_details") == "true"


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_post_with_data_dict(respx_mock: MockRouter) -> None:
    """Test POST request with dict data payload."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 10, "name": "Bob"})
    )

    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "Bob", "email": "bob@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 10
    assert result.name == "Bob"

    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "Bob", "email": "bob@example.com"}


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_post_with_pydantic_model(respx_mock: MockRouter) -> None:
    """Test POST request with Pydantic model data payload."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 11, "name": "Charlie"})
    )

    data = CreateUserRequest(name="Charlie", email="charlie@example.com")
    result = client.request("POST", "/users", response_map={201: User}, data=data)

    assert isinstance(result, User)
    assert result.id == 11
    assert result.name == "Charlie"

    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "Charlie", "email": "charlie@example.com"}


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_put_with_path_and_data(respx_mock: MockRouter) -> None:
    """Test PUT request with path params and data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.put("/users/5").mock(
        return_value=httpx.Response(200, json={"id": 5, "name": "Updated User"})
    )

    result = client.request(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Updated User", "email": "updated@example.com"},
        user_id=5,
    )

    assert isinstance(result, User)
    assert result.id == 5
    assert result.name == "Updated User"

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/5"


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_patch(respx_mock: MockRouter) -> None:
    """Test PATCH request."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.patch("/users/3").mock(
        return_value=httpx.Response(200, json={"id": 3, "name": "Patched"})
    )

    result = client.request(
        "PATCH",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Patched"},
        user_id=3,
    )

    assert isinstance(result, User)
    assert result.name == "Patched"


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_delete(respx_mock: MockRouter) -> None:
    """Test DELETE request."""
    client = APIClient(base_url=BASE_URL)

    # Test with a response that returns data
    respx_mock.delete("/users/5").mock(
        return_value=httpx.Response(200, json={"id": 5, "name": "Deleted"})
    )

    result = client.request(
        "DELETE",
        "/users/{user_id}",
        response_map={200: User},
        user_id=5,
    )

    assert isinstance(result, User)
    assert result.id == 5


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_with_response_map_union(respx_mock: MockRouter) -> None:
    """Test request with response_map returning different types based on status."""
    client = APIClient(base_url=BASE_URL)

    # Test successful response
    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "name": "Alice", "status": "success"}
        )
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: SuccessResponse, 404: ErrorResponse},
        user_id=1,
    )

    assert isinstance(result, SuccessResponse)
    assert result.id == 1
    assert result.name == "Alice"

    # Test error response
    respx_mock.get("/users/999").mock(
        return_value=httpx.Response(404, json={"error": "Not found", "code": 404})
    )

    error_result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: SuccessResponse, 404: ErrorResponse},
        user_id=999,
    )

    assert isinstance(error_result, ErrorResponse)
    assert error_result.error == "Not found"
    assert error_result.code == 404


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_with_custom_headers(respx_mock: MockRouter) -> None:
    """Test request with custom headers."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alice"})
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"X-Custom-Header": "test-value"},
        user_id=1,
    )

    assert isinstance(result, User)

    call = respx_mock.calls[0]
    assert call.request.headers["X-Custom-Header"] == "test-value"


@pytest.mark.respx(base_url=BASE_URL)
def test_direct_request_post_with_query_and_data(respx_mock: MockRouter) -> None:
    """Test POST with both query params and data payload."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 20, "name": "Dave"})
    )

    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "Dave", "email": "dave@example.com"},
        query={"notify": "true"},
    )

    assert isinstance(result, User)
    assert result.id == 20

    call = respx_mock.calls[0]
    assert call.request.url.params.get("notify") == "true"
    assert json.loads(call.request.content) == {"name": "Dave", "email": "dave@example.com"}


# Async tests


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_direct_arequest_get_basic(respx_mock: MockRouter) -> None:
    """Test basic async GET request without decorator."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/pokemon/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Bulbasaur"})
    )

    result = await client.arequest("GET", "/pokemon/{id}", response_map={200: Pokemon}, id=1)

    assert isinstance(result, Pokemon)
    assert result.id == 1
    assert result.name == "Bulbasaur"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_direct_arequest_post_with_data(respx_mock: MockRouter) -> None:
    """Test async POST request with data payload."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 10, "name": "Bob"})
    )

    result = await client.arequest(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "Bob", "email": "bob@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 10
    assert result.name == "Bob"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_direct_arequest_with_response_map_union(respx_mock: MockRouter) -> None:
    """Test async request with response_map returning different types."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "name": "Alice", "status": "success"}
        )
    )

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: SuccessResponse, 404: ErrorResponse},
        user_id=1,
    )

    assert isinstance(result, SuccessResponse)
    assert result.id == 1
    assert result.name == "Alice"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_direct_arequest_put_with_pydantic_model(respx_mock: MockRouter) -> None:
    """Test async PUT request with Pydantic model."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.put("/users/5").mock(
        return_value=httpx.Response(200, json={"id": 5, "name": "Updated"})
    )

    data = CreateUserRequest(name="Updated", email="updated@example.com")
    result = await client.arequest(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data=data,
        user_id=5,
    )

    assert isinstance(result, User)
    assert result.id == 5
    assert result.name == "Updated"
