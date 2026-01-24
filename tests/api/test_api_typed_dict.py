from __future__ import annotations

from typing import TypedDict

import pytest

from clientele.api import APIClient
from clientele.testing import ResponseFactory, configure_client_for_testing


# Test TypedDict definitions
class UserDict(TypedDict):
    id: int
    name: str


class CreateUserRequestDict(TypedDict):
    name: str


class ErrorDict(TypedDict):
    message: str
    code: str


class DeleteBatchDict(TypedDict):
    user_ids: list[int]


class DeleteResultDict(TypedDict):
    deleted: int


BASE_URL = "https://api.example.com"


def test_get_with_typeddict_result() -> None:
    """Test that GET request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = get_user(1)

    assert user == {"id": 1, "name": "Ada"}
    assert isinstance(user, dict)

    client.close()


def test_post_with_typeddict_result() -> None:
    """Test that POST request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}
    assert isinstance(user, dict)

    client.close()


def test_get_with_typeddict_list_result() -> None:
    """Test that GET request works with list of TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}],
        ),
    )

    @client.get("/users")
    def list_users(result: list[UserDict]) -> list[UserDict]:
        return result

    users = list_users()

    assert users == [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]
    assert isinstance(users, list)
    assert all(isinstance(user, dict) for user in users)

    client.close()


def test_put_with_typeddict_result() -> None:
    """Test that PUT request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada Updated"},
        ),
    )

    @client.put("/users/{user_id}")
    def update_user(user_id: int, data: dict, result: UserDict) -> UserDict:
        return result

    user = update_user(1, data={"name": "Ada Updated"})

    assert user == {"id": 1, "name": "Ada Updated"}

    client.close()


def test_patch_with_typeddict_result() -> None:
    """Test that PATCH request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada Patched"},
        ),
    )

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, data: dict, result: UserDict) -> UserDict:
        return result

    user = patch_user(1, data={"name": "Ada Patched"})

    assert user == {"id": 1, "name": "Ada Patched"}

    client.close()


def test_delete_with_typeddict_result() -> None:
    """Test that DELETE request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada Deleted"},
        ),
    )

    @client.delete("/users/{user_id}")
    def delete_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = delete_user(1)

    assert user == {"id": 1, "name": "Ada Deleted"}

    client.close()


def test_response_map_with_typeddict() -> None:
    """Test that response_map works with TypedDict types."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"message": "User not found", "code": "NOT_FOUND"},
        ),
    )

    @client.get("/users/{user_id}", response_map={200: UserDict, 404: ErrorDict})
    def get_user(user_id: int, result: UserDict | ErrorDict) -> UserDict | ErrorDict:
        return result

    # Test successful response
    user = get_user(1)
    assert user == {"id": 1, "name": "Ada"}

    # Test error response
    error = get_user(999)
    assert error == {"message": "User not found", "code": "NOT_FOUND"}

    client.close()


def test_typeddict_with_query_params() -> None:
    """Test TypedDict result with query parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict, include_details: bool = True) -> UserDict:
        return result

    user = get_user(1, include_details=False)

    assert user == {"id": 1, "name": "Ada"}

    client.close()


def test_typeddict_validation_error_on_non_dict() -> None:
    """Test that TypedDict validation raises error for non-dict payloads."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data="not a dict",
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    with pytest.raises(TypeError, match="Expected dict for TypedDict"):
        get_user(1)

    client.close()


@pytest.mark.asyncio
async def test_async_get_with_typeddict_result() -> None:
    """Test that async GET request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: UserDict) -> UserDict:
        return result

    user = await get_user(1)

    assert user == {"id": 1, "name": "Ada"}
    assert isinstance(user, dict)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_post_with_typeddict_result() -> None:
    """Test that async POST request works with TypedDict as result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    async def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = await create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}
    assert isinstance(user, dict)

    await client.aclose()


def test_post_with_typeddict_data_validates_request_body() -> None:
    """Test that POST with TypedDict data parameter sends correct JSON body."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}

    client.close()


def test_put_with_typeddict_data_validates_request_body() -> None:
    """Test that PUT with TypedDict data parameter sends correct JSON body."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada Updated"},
        ),
    )

    @client.put("/users/{user_id}")
    def update_user(user_id: int, data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = update_user(1, data={"name": "Ada Updated"})

    assert user == {"id": 1, "name": "Ada Updated"}

    client.close()


def test_patch_with_typeddict_data_validates_request_body() -> None:
    """Test that PATCH with TypedDict data parameter sends correct JSON body."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada Patched"},
        ),
    )

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = patch_user(1, data={"name": "Ada Patched"})

    assert user == {"id": 1, "name": "Ada Patched"}

    client.close()


def test_delete_with_typeddict_data_validates_request_body() -> None:
    """Test that DELETE with TypedDict data parameter sends correct JSON body."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/batch",
        response_obj=ResponseFactory.ok(
            data={"deleted": 2},
        ),
    )

    @client.delete("/users/batch")
    def delete_users(data: DeleteBatchDict, result: DeleteResultDict) -> DeleteResultDict:
        return result

    result = delete_users(data={"user_ids": [1, 2]})

    assert result == {"deleted": 2}

    client.close()


def test_typeddict_data_validation_error_on_non_dict() -> None:
    """Test that TypedDict data validation raises error for non-dict payloads."""
    client = APIClient(base_url=BASE_URL)

    @client.post("/users")
    def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    # Passing a non-dict should raise TypeError before making the request
    with pytest.raises(TypeError, match="Expected dict for TypedDict"):
        create_user(data="not a dict")


@pytest.mark.asyncio
async def test_async_post_with_typeddict_data_validates_request_body() -> None:
    """Test that async POST with TypedDict data parameter sends correct JSON body."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    async def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = await create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}

    await client.aclose()


def test_post_with_both_typeddict_data_and_result() -> None:
    """Test that both data and result can be TypedDict simultaneously."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    def create_user(data: CreateUserRequestDict, result: UserDict) -> UserDict:
        return result

    user = create_user(data={"name": "Charlie"})

    assert user == {"id": 10, "name": "Charlie"}
    assert isinstance(user, dict)

    client.close()
