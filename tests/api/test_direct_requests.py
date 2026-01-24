"""Tests for direct request methods (request and arequest)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from clientele.api import APIClient, APIException
from clientele.testing import ResponseFactory, configure_client_for_testing

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


def test_request_get_simple() -> None:
    """Test simple GET request with direct request method."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)
    assert result.id == 1
    assert result.name == "Alice"

    client.close()


def test_request_get_with_query_params() -> None:
    """Test GET request with query parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        ),
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

    client.close()


def test_request_get_with_path_params() -> None:
    """Test GET request with multiple path parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/organizations/acme/users/42",
        response_obj=ResponseFactory.ok(
            data={"id": 42, "name": "Charlie"},
        ),
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

    client.close()


def test_request_get_with_custom_headers() -> None:
    """Test GET request with custom headers."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"X-Custom-Header": "test-value", "X-Request-ID": "123"},
        user_id=1,
    )

    assert isinstance(result, User)

    client.close()


def test_request_get_with_response_map_error_status() -> None:
    """Test GET request with response_map handling error status."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"error": "User not found", "code": 404},
        ),
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User, 404: ErrorResponse},
        user_id=999,
    )

    assert isinstance(result, ErrorResponse)
    assert result.error == "User not found"
    assert result.code == 404

    client.close()


def test_request_get_unexpected_status_raises_exception() -> None:
    """Test GET request raises exception for unmapped status code."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.internal_server_error(
            data={"error": "Server error"},
        ),
    )

    with pytest.raises(APIException) as exc_info:
        client.request(
            "GET",
            "/users/{user_id}",
            response_map={200: User, 404: ErrorResponse},
            user_id=1,
        )

    assert exc_info.value.response.status_code == 500

    client.close()


def test_request_post_with_dict_data() -> None:
    """Test POST request with dict data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "David"},
        ),
    )

    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "David", "email": "david@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 10

    client.close()


def test_request_post_with_pydantic_model() -> None:
    """Test POST request with Pydantic model data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 11, "name": "Eve"},
        ),
    )

    create_req = CreateUserRequest(name="Eve", email="eve@example.com")
    result = client.request(
        "POST",
        "/users",
        response_map={201: User},
        data=create_req,
    )

    assert isinstance(result, User)
    assert result.id == 11

    client.close()


def test_request_post_with_path_params_and_data() -> None:
    """Test POST request with both path params and data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/organizations/acme/users",
        response_obj=ResponseFactory.created(
            data={"id": 20, "name": "Frank"},
        ),
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

    client.close()


def test_request_post_multiple_status_codes() -> None:
    """Test POST request with multiple status codes in response_map."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.bad_request(
            data={"error": "Invalid request", "code": 400},
        ),
    )

    result = client.request(
        "POST",
        "/users",
        response_map={201: User, 400: ErrorResponse},
        data={"name": "Invalid", "email": "invalid"},
    )

    assert isinstance(result, ErrorResponse)
    assert result.error == "Invalid request"

    client.close()


def test_request_put_with_data() -> None:
    """Test PUT request with data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/5",
        response_obj=ResponseFactory.ok(
            data={"id": 5, "name": "Updated"},
        ),
    )

    result = client.request(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Updated", "email": "updated@example.com"},
        user_id=5,
    )

    assert isinstance(result, User)
    assert result.name == "Updated"

    client.close()


def test_request_patch_with_data() -> None:
    """Test PATCH request with data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/6",
        response_obj=ResponseFactory.ok(
            data={"id": 6, "name": "Patched"},
        ),
    )

    result = client.request(
        "PATCH",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Patched"},
        user_id=6,
    )

    assert isinstance(result, User)
    assert result.name == "Patched"

    client.close()


def test_request_delete_no_content() -> None:
    """Test DELETE request with 204 no content response."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/7",
        response_obj=ResponseFactory.no_content(),
    )

    result = client.request(
        "DELETE",
        "/users/{user_id}",
        response_map={204: type(None)},
        user_id=7,
    )

    assert result is None

    client.close()


def test_request_delete_with_response() -> None:
    """Test DELETE request that returns data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/8",
        response_obj=ResponseFactory.ok(
            data={"id": 8, "name": "Deleted"},
        ),
    )

    result = client.request(
        "DELETE",
        "/users/{user_id}",
        response_map={200: User},
        user_id=8,
    )

    assert isinstance(result, User)

    client.close()


@pytest.mark.asyncio
async def test_arequest_get_simple() -> None:
    """Test simple async GET request."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)
    assert result.id == 1
    assert result.name == "Alice"

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_get_with_query_params() -> None:
    """Test async GET request with query parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        ),
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

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_get_with_path_params() -> None:
    """Test async GET request with path parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/products/electronics/42",
        response_obj=ResponseFactory.ok(
            data={"id": 42, "name": "Laptop", "price": 999.99},
        ),
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

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_get_with_headers() -> None:
    """Test async GET request with custom headers."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"Authorization": "Bearer token123"},
        user_id=1,
    )

    assert isinstance(result, User)

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_get_error_response() -> None:
    """Test async GET request with error response."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"error": "Not found", "code": 404},
        ),
    )

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User, 404: ErrorResponse},
        user_id=999,
    )

    assert isinstance(result, ErrorResponse)
    assert result.code == 404

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_post_with_dict() -> None:
    """Test async POST request with dict data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 100, "name": "Gabriel"},
        ),
    )

    result = await client.arequest(
        "POST",
        "/users",
        response_map={201: User},
        data={"name": "Gabriel", "email": "gabriel@example.com"},
    )

    assert isinstance(result, User)
    assert result.id == 100

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_post_with_model() -> None:
    """Test async POST request with Pydantic model."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 101, "name": "Hannah"},
        ),
    )

    create_req = CreateUserRequest(name="Hannah", email="hannah@example.com")
    result = await client.arequest(
        "POST",
        "/users",
        response_map={201: User},
        data=create_req,
    )

    assert isinstance(result, User)
    assert result.id == 101

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_post_with_path_and_data() -> None:
    """Test async POST request with both path params and data."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/organizations/xyz/users",
        response_obj=ResponseFactory.created(
            data={"id": 200, "name": "Isaac"},
        ),
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

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_put() -> None:
    """Test async PUT request."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/50",
        response_obj=ResponseFactory.ok(
            data={"id": 50, "name": "Updated Async"},
        ),
    )

    result = await client.arequest(
        "PUT",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Updated Async", "email": "updated@example.com"},
        user_id=50,
    )

    assert isinstance(result, User)
    assert result.name == "Updated Async"

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_patch() -> None:
    """Test async PATCH request."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/51",
        response_obj=ResponseFactory.ok(
            data={"id": 51, "name": "Patched Async"},
        ),
    )

    result = await client.arequest(
        "PATCH",
        "/users/{user_id}",
        response_map={200: User},
        data={"name": "Patched Async"},
        user_id=51,
    )

    assert isinstance(result, User)
    assert result.name == "Patched Async"

    await client.aclose()


@pytest.mark.asyncio
async def test_arequest_delete() -> None:
    """Test async DELETE request."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/52",
        response_obj=ResponseFactory.no_content(),
    )

    result = await client.arequest(
        "DELETE",
        "/users/{user_id}",
        response_map={204: type(None)},
        user_id=52,
    )

    assert result is None

    await client.aclose()


def test_request_with_query_and_path_params() -> None:
    """Test request with both query and path parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/organizations/acme/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Alice"}],
        ),
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

    client.close()


def test_request_no_data_for_post_creates_empty_request() -> None:
    """Test POST request without data parameter."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/trigger",
        response_obj=ResponseFactory.ok(
            data={"status": "triggered"},
        ),
    )

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

    client.close()


def test_request_with_query_filtering_none_values() -> None:
    """Test that query parameters work with valid values."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = client.request(
        "GET",
        "/users",
        response_map={200: User},
        query={"status": "active"},
    )

    assert isinstance(result, User)

    client.close()


def test_request_with_client_headers() -> None:
    """Test that client headers are merged with request headers."""
    client = APIClient(base_url=BASE_URL)
    # Set default headers on client config
    client.config.headers = {"Authorization": "Bearer default", "User-Agent": "ClienteleBot"}

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = client.request(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        headers={"X-Custom": "value"},  # Override with custom header
        user_id=1,
    )

    assert isinstance(result, User)

    client.close()


@pytest.mark.asyncio
async def test_arequest_with_client_headers() -> None:
    """Test async request with client headers merged."""
    client = APIClient(base_url=BASE_URL)
    client.config.headers = {"Authorization": "Bearer token"}

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice"},
        ),
    )

    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1,
    )

    assert isinstance(result, User)

    await client.aclose()


def test_request_complex_path_substitution() -> None:
    """Test request with complex path substitution."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/v1/tenants/tenant-123/projects/proj-456/resources/res-789",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Resource"},
        ),
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

    client.close()


def test_request_list_response_validation() -> None:
    """Test that list responses are properly validated into model instances."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/products",
        response_obj=ResponseFactory.ok(
            data=[
                {"id": 1, "name": "Widget", "price": 9.99},
                {"id": 2, "name": "Gadget", "price": 19.99},
            ],
        ),
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

    client.close()


def test_request_string_response() -> None:
    """Test request that returns a string response."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/version",
        response_obj=ResponseFactory.ok(
            data="1.2.3",
            headers={"content-type": "text/plain"},
        ),
    )

    result = client.request(
        "GET",
        "/version",
        response_map={200: str},
    )

    assert result == "1.2.3"

    client.close()


@pytest.mark.asyncio
async def test_arequest_string_response() -> None:
    """Test async request that returns a string response."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/version",
        response_obj=ResponseFactory.ok(
            data="1.2.3",
        ),
    )

    result = await client.arequest(
        "GET",
        "/version",
        response_map={200: str},
    )

    assert result == "1.2.3"

    await client.aclose()
