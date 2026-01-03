from __future__ import annotations

from typing import TypedDict

import httpx
import pytest
from respx import MockRouter

from clientele.framework import Client


# Test TypedDict definitions
class UserDict(TypedDict):
    id: int
    name: str


class CreateUserRequestDict(TypedDict):
    name: str


class ErrorDict(TypedDict):
    message: str
    code: str


BASE_URL = "https://api.example.com"


@pytest.mark.respx(base_url=BASE_URL)
def test_get_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that GET request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = get_user(1)

    assert user == {"id": 1, "name": "Ada"}
    assert isinstance(user, dict)


@pytest.mark.respx(base_url=BASE_URL)
def test_post_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that POST request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 10, "name": "Charlie"})
    )

    @client.post("/users")
    def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}
    assert isinstance(user, dict)


@pytest.mark.respx(base_url=BASE_URL)
def test_get_with_typeddict_list_result(respx_mock: MockRouter) -> None:
    """Test that GET request works with list of TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users").mock(
        return_value=httpx.Response(
            200, json=[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
        )
    )

    @client.get("/users")
    def list_users(result: list[UserDict]) -> list[UserDict]:
        return result

    users = list_users()

    assert users == [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
    assert isinstance(users, list)
    assert all(isinstance(user, dict) for user in users)


@pytest.mark.respx(base_url=BASE_URL)
def test_put_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that PUT request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.put("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada Updated"})
    )

    @client.put("/users/{user_id}")
    def update_user(user_id: int, data: dict, result: UserDict) -> UserDict:
        return result

    user = update_user(1, data={"name": "Ada Updated"})

    assert user == {"id": 1, "name": "Ada Updated"}


@pytest.mark.respx(base_url=BASE_URL)
def test_patch_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that PATCH request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.patch("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada Patched"})
    )

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, data: dict, result: UserDict) -> UserDict:
        return result

    user = patch_user(1, data={"name": "Ada Patched"})

    assert user == {"id": 1, "name": "Ada Patched"}


@pytest.mark.respx(base_url=BASE_URL)
def test_delete_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that DELETE request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.delete("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada Deleted"})
    )

    @client.delete("/users/{user_id}")
    def delete_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = delete_user(1)

    assert user == {"id": 1, "name": "Ada Deleted"}


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_with_typeddict(respx_mock: MockRouter) -> None:
    """Test that response_map works with TypedDict types."""
    client = Client(base_url=BASE_URL)

    # Test successful response
    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )

    @client.get("/users/{user_id}", response_map={200: UserDict, 404: ErrorDict})
    def get_user(user_id: int, result: UserDict | ErrorDict) -> UserDict | ErrorDict:
        return result

    user = get_user(1)
    assert user == {"id": 1, "name": "Ada"}

    # Test error response
    respx_mock.get("/users/999").mock(
        return_value=httpx.Response(404, json={"message": "User not found", "code": "NOT_FOUND"})
    )

    error = get_user(999)
    assert error == {"message": "User not found", "code": "NOT_FOUND"}


@pytest.mark.respx(base_url=BASE_URL)
def test_typeddict_with_query_params(respx_mock: MockRouter) -> None:
    """Test TypedDict result with query parameters."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict, include_details: bool = True) -> UserDict:
        return result

    user = get_user(1, include_details=False)

    assert user == {"id": 1, "name": "Ada"}
    call = respx_mock.calls[0]
    assert call.request.url.params.get("include_details") == "false"


@pytest.mark.respx(base_url=BASE_URL)
def test_typeddict_validation_error_on_non_dict(respx_mock: MockRouter) -> None:
    """Test that TypedDict validation raises error for non-dict payloads."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json="not a dict")
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    with pytest.raises(TypeError, match="Expected dict for TypedDict"):
        get_user(1)


@pytest.mark.respx(base_url=BASE_URL)
@pytest.mark.asyncio
async def test_async_get_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that async GET request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = await get_user(1)

    assert user == {"id": 1, "name": "Ada"}
    assert isinstance(user, dict)


@pytest.mark.respx(base_url=BASE_URL)
@pytest.mark.asyncio
async def test_async_post_with_typeddict_result(respx_mock: MockRouter) -> None:
    """Test that async POST request works with TypedDict as result type."""
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(
        return_value=httpx.Response(201, json={"id": 10, "name": "Charlie"})
    )

    @client.post("/users")
    async def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = await create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}
    assert isinstance(user, dict)
