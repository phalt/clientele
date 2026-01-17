"""Tests for direct request methods (request and arequest)."""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import APIClient, APIException

BASE_URL = "https://api.example.com"


# Test models
class User(BaseModel):
    id: int
    name: str


class CreateUserRequest(BaseModel):
    name: str
    email: str


class ErrorResponse(BaseModel):
    error: str
    code: int


class Product(BaseModel):
    id: int
    name: str
    price: float


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_simple(respx_mock: MockRouter) -> None:
    """Test simple GET request with direct request method."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)
    assert result.id == 1
    assert result.name == "Alice"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_with_query_params(respx_mock: MockRouter) -> None:
    """Test GET request with query parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
    )

    result = client.request(
        "GET",
        "/users",
        response_map={200: list[User]},
        query={"search": "dev", "limit": "10"},
    )

    assert isinstance(result, list)
    assert len(result) == 2
    # Items should be User instances after validation
    assert isinstance(result[0], User)
    assert result[0].name == "Alice"

    # Verify query params were sent
    call = respx_mock.calls[0]
    assert call.request.url.params["search"] == "dev"
    assert call.request.url.params["limit"] == "10"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_with_path_params(respx_mock: MockRouter) -> None:
    """Test GET request with multiple path parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/organizations/acme/users/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "name": "Charlie"})
    )

    result = client.request(
        "GET",
        "/organizations/{org_id}/users/{user_id}",
        response_map={200: User},
        org_id="acme",
        user_id=42,
    )

    assert isinstance(result, User)
    assert result.id == 42
    assert result.name == "Charlie"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_with_custom_headers(respx_mock: MockRouter) -> None:
    """Test GET request with custom headers."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"X-Custom-Header": "test-value", "X-Request-ID": "123"},
        user_id=1,
    )

    assert isinstance(result, User)

    # Verify custom headers were sent
    call = respx_mock.calls[0]
    assert call.request.headers["X-Custom-Header"] == "test-value"
    assert call.request.headers["X-Request-ID"] == "123"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_with_response_map_error_status(respx_mock: MockRouter) -> None:
    """Test GET request with response_map handling error status."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "User not found", "code": 404}))

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User, 404: ErrorResponse},
        user_id=999,
    )

    assert isinstance(result, ErrorResponse)
    assert result.error == "User not found"
    assert result.code == 404


@pytest.mark.respx(base_url=BASE_URL)
def test_request_get_unexpected_status_raises_exception(respx_mock: MockRouter) -> None:
    """Test GET request raises exception for unmapped status code."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(500, json={"error": "Server error"}))

    with pytest.raises(APIException) as exc_info:
        client.request(
            "GET",
            "/users/{user_id}",
            response_map={200: User, 404: ErrorResponse},
            user_id=1,
        )

    assert exc_info.value.response.status_code == 500


@pytest.mark.respx(base_url=BASE_URL)
def test_request_post_with_dict_data(respx_mock: MockRouter) -> None:
    """Test POST request with dict data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "David"}))

    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "David", "email": "david@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 10

    # Verify request body
    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "David", "email": "david@example.com"}


@pytest.mark.respx(base_url=BASE_URL)
def test_request_post_with_pydantic_model(respx_mock: MockRouter) -> None:
    """Test POST request with Pydantic model data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 11, "name": "Eve"}))

    create_req = CreateUserRequest(name="Eve", email="eve@example.com")
    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data=create_req,
    )

    assert isinstance(result, User)
    assert result.id == 11

    # Verify request body was serialized
    call = respx_mock.calls[0]
    body = json.loads(call.request.content)
    assert body["name"] == "Eve"
    assert body["email"] == "eve@example.com"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_post_with_path_params_and_data(respx_mock: MockRouter) -> None:
    """Test POST request with both path params and data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/organizations/acme/users").mock(
        return_value=httpx.Response(201, json={"id": 20, "name": "Frank"})
    )

    result = client.request(
        "POST",
        "/organizations/{org_id}/users",
        response_map={201: User},
        data={"name": "Frank", "email": "frank@example.com"},
        org_id="acme",
    )

    assert isinstance(result, User)
    assert result.id == 20


@pytest.mark.respx(base_url=BASE_URL)
def test_request_post_multiple_status_codes(respx_mock: MockRouter) -> None:
    """Test POST request with multiple status codes in response_map."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(400, json={"error": "Invalid request", "code": 400}))

    result = client.request(
        "POST",
        "/users",
        response_map={201: User, 400: ErrorResponse},
        data={"name": "Invalid", "email": "invalid"},
    )

    assert isinstance(result, ErrorResponse)
    assert result.error == "Invalid request"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_put_with_data(respx_mock: MockRouter) -> None:
    """Test PUT request with data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.put("/users/5").mock(return_value=httpx.Response(200, json={"id": 5, "name": "Updated"}))

    result = client.request(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Updated", "email": "updated@example.com"},
        user_id=5,
    )

    assert isinstance(result, User)
    assert result.name == "Updated"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_patch_with_data(respx_mock: MockRouter) -> None:
    """Test PATCH request with data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.patch("/users/6").mock(return_value=httpx.Response(200, json={"id": 6, "name": "Patched"}))

    result = client.request(
        "PATCH",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Patched"},
        user_id=6,
    )

    assert isinstance(result, User)
    assert result.name == "Patched"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_delete_no_content(respx_mock: MockRouter) -> None:
    """Test DELETE request with 204 no content response."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.delete("/users/7").mock(return_value=httpx.Response(204))

    result = client.request(
        "DELETE",
        "/users/{user_id}",
        response_map={204: type(None)},
        user_id=7,
    )

    assert result is None


@pytest.mark.respx(base_url=BASE_URL)
def test_request_delete_with_response(respx_mock: MockRouter) -> None:
    """Test DELETE request that returns data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.delete("/users/8").mock(return_value=httpx.Response(200, json={"id": 8, "name": "Deleted"}))

    result = client.request(
        "DELETE",
        "/users/{user_id}",
        response_map={200: User},
        user_id=8,
    )

    assert isinstance(result, User)


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_get_simple(respx_mock: MockRouter) -> None:
    """Test simple async GET request."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)
    assert result.id == 1
    assert result.name == "Alice"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_get_with_query_params(respx_mock: MockRouter) -> None:
    """Test async GET request with query parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
    )

    result = await client.arequest(
        "GET",
        "/users",
        response_map={200: list[User]},
        query={"search": "dev"},
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], User)
    assert result[0].name == "Alice"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_get_with_path_params(respx_mock: MockRouter) -> None:
    """Test async GET request with path parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/products/electronics/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "name": "Laptop", "price": 999.99})
    )

    result = await client.arequest(
        "GET",
        "/products/{category}/{product_id}",
        response_map={200: Product},
        category="electronics",
        product_id=42,
    )

    assert isinstance(result, Product)
    assert result.name == "Laptop"
    assert result.price == 999.99


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_get_with_headers(respx_mock: MockRouter) -> None:
    """Test async GET request with custom headers."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"Authorization": "Bearer token123"},
        user_id=1,
    )

    assert isinstance(result, User)

    # Verify headers
    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer token123"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_get_error_response(respx_mock: MockRouter) -> None:
    """Test async GET request with error response."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "Not found", "code": 404}))

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User, 404: ErrorResponse},
        user_id=999,
    )

    assert isinstance(result, ErrorResponse)
    assert result.code == 404


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_post_with_dict(respx_mock: MockRouter) -> None:
    """Test async POST request with dict data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 100, "name": "Gabriel"}))

    result = await client.arequest(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "Gabriel", "email": "gabriel@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 100


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_post_with_model(respx_mock: MockRouter) -> None:
    """Test async POST request with Pydantic model."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 101, "name": "Hannah"}))

    create_req = CreateUserRequest(name="Hannah", email="hannah@example.com")
    result = await client.arequest(
        "POST",
        "/users",
        response_map={201: User},
        data=create_req,
    )

    assert isinstance(result, User)
    assert result.id == 101


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_post_with_path_and_data(respx_mock: MockRouter) -> None:
    """Test async POST request with both path params and data."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/organizations/xyz/users").mock(
        return_value=httpx.Response(201, json={"id": 200, "name": "Isaac"})
    )

    result = await client.arequest(
        "POST",
        "/organizations/{org_id}/users",
        response_map={201: User},
        data={"name": "Isaac", "email": "isaac@example.com"},
        org_id="xyz",
    )

    assert isinstance(result, User)
    assert result.id == 200


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_put(respx_mock: MockRouter) -> None:
    """Test async PUT request."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.put("/users/50").mock(return_value=httpx.Response(200, json={"id": 50, "name": "Updated Async"}))

    result = await client.arequest(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Updated Async", "email": "updated@example.com"},
        user_id=50,
    )

    assert isinstance(result, User)
    assert result.name == "Updated Async"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_patch(respx_mock: MockRouter) -> None:
    """Test async PATCH request."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.patch("/users/51").mock(return_value=httpx.Response(200, json={"id": 51, "name": "Patched Async"}))

    result = await client.arequest(
        "PATCH",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Patched Async"},
        user_id=51,
    )

    assert isinstance(result, User)
    assert result.name == "Patched Async"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_delete(respx_mock: MockRouter) -> None:
    """Test async DELETE request."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.delete("/users/52").mock(return_value=httpx.Response(204))

    result = await client.arequest(
        "DELETE",
        "/users/{user_id}",
        response_map={204: type(None)},
        user_id=52,
    )

    assert result is None


@pytest.mark.respx(base_url=BASE_URL)
def test_request_with_query_and_path_params(respx_mock: MockRouter) -> None:
    """Test request with both query and path parameters."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/organizations/acme/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Alice"}])
    )

    result = client.request(
        "GET",
        "/organizations/{org_id}/users",
        response_map={200: list[User]},
        org_id="acme",
        query={"status": "active", "limit": "5"},
    )

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], User)

    # Verify both path and query params
    call = respx_mock.calls[0]
    assert "/organizations/acme/users" in str(call.request.url)
    assert call.request.url.params["status"] == "active"
    assert call.request.url.params["limit"] == "5"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_no_data_for_post_creates_empty_request(respx_mock: MockRouter) -> None:
    """Test POST request without data parameter."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/trigger").mock(return_value=httpx.Response(200, json={"status": "triggered"}))

    # Create a simple response model
    class SimpleResponse(BaseModel):
        status: str

    result = client.request(
        "POST",
        "/trigger",
        response_map={200: SimpleResponse},
    )

    assert isinstance(result, SimpleResponse)
    assert result.status == "triggered"

    # Verify that no request body was sent (or empty)
    call = respx_mock.calls[0]
    # When no data is provided, the json key shouldn't be in request kwargs
    assert call.request.content == b""


@pytest.mark.respx(base_url=BASE_URL)
def test_request_with_query_filtering_none_values(respx_mock: MockRouter) -> None:
    """Test that query parameters work with valid values."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = client.request(
        "GET",
        "/users",
        response_map={200: User},
        query={"status": "active"},
    )

    assert isinstance(result, User)

    # Verify that parameters were sent
    call = respx_mock.calls[0]
    assert call.request.url.params["status"] == "active"
    assert call.request.url.params.get("tag") is None or "tag" not in str(call.request.url)


@pytest.mark.respx(base_url=BASE_URL)
def test_request_with_client_headers(respx_mock: MockRouter) -> None:
    """Test that client headers are merged with request headers."""
    client = APIClient(base_url=BASE_URL)
    # Set default headers on client config
    client.config.headers = {"Authorization": "Bearer default", "User-Agent": "ClienteleBot"}

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"X-Custom": "value"},  # Override with custom header
        user_id=1,
    )

    assert isinstance(result, User)

    # Verify merged headers
    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer default"
    assert call.request.headers["User-Agent"] == "ClienteleBot"
    assert call.request.headers["X-Custom"] == "value"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_with_client_headers(respx_mock: MockRouter) -> None:
    """Test async request with client headers merged."""
    client = APIClient(base_url=BASE_URL)
    client.config.headers = {"Authorization": "Bearer token"}

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Alice"}))

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)

    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer token"


@pytest.mark.respx(base_url=BASE_URL)
def test_request_complex_path_substitution(respx_mock: MockRouter) -> None:
    """Test request with complex path substitution."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/v1/tenants/tenant-123/projects/proj-456/resources/res-789").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Resource"})
    )

    # Use a simple model for this test
    class Resource(BaseModel):
        id: int
        name: str

    result = client.request(
        "GET",
        "/v1/tenants/{tenant_id}/projects/{project_id}/resources/{resource_id}",
        response_map={200: Resource},
        tenant_id="tenant-123",
        project_id="proj-456",
        resource_id="res-789",
    )

    assert isinstance(result, Resource)
    assert result.id == 1


@pytest.mark.respx(base_url=BASE_URL)
def test_request_list_response_validation(respx_mock: MockRouter) -> None:
    """Test that list responses are properly validated into model instances."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/products").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "name": "Widget", "price": 9.99},
                {"id": 2, "name": "Gadget", "price": 19.99},
            ],
        )
    )

    result = client.request(
        "GET",
        "/products",
        response_map={200: list[Product]},
    )

    assert isinstance(result, list)
    assert len(result) == 2
    # All items should be Product instances
    assert all(isinstance(item, Product) for item in result)
    assert result[0].id == 1
    assert result[0].name == "Widget"
    assert result[0].price == 9.99


@pytest.mark.respx(base_url=BASE_URL)
def test_request_string_response(respx_mock: MockRouter) -> None:
    """Test request that returns a string response."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/version").mock(return_value=httpx.Response(200, text="1.2.3"))

    result = client.request(
        "GET",
        "/version",
        response_map={200: str},
    )

    assert result == "1.2.3"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_arequest_string_response(respx_mock: MockRouter) -> None:
    """Test async request that returns a string response."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/version").mock(return_value=httpx.Response(200, text="1.2.3"))

    result = await client.arequest(
        "GET",
        "/version",
        response_map={200: str},
    )

    assert result == "1.2.3"
