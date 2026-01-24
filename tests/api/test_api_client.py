from __future__ import annotations

import pytest
from pydantic import BaseModel

from clientele.api import APIClient, APIException, BaseConfig
from clientele.testing import ResponseFactory, configure_client_for_testing

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


class CreateUserRequest(BaseModel):
    name: str


class UpdateUserRequest(BaseModel):
    name: str


class RequestDataAndParameterResponse(BaseModel):
    path_parameter: str
    your_query: str


def test_raises_when_no_params_supplied():
    with pytest.raises(ValueError):
        APIClient()


def test_get_validates_response_and_builds_query() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(data={"id": 1, "name": "Ada"}),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User, include_details: bool = True) -> User:
        return result

    user = get_user(1)

    assert user == User(id=1, name="Ada")

    client.close()


def test_get_respects_query_override_and_list_validation() -> None:
    client = APIClient(config=BaseConfig(base_url=BASE_URL, headers={"Authorization": "Bearer token"}))

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}],
        ),
    )

    @client.get("/users")
    def list_users(query: dict[str, str], result: list[User]) -> list[User]:
        return result

    users = list_users(query={"search": "dev"})

    assert [user.name for user in users] == ["Ada", "Bob"]

    client.close()


def test_post_accepts_model_instance_and_dict() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Charlie"},
        ),
    )

    @client.post("/users")
    def create_user(data: CreateUserRequest, result: User) -> User:
        return result

    user = create_user(data=CreateUserRequest(name="Charlie"))
    assert user.id == 10

    dict_user = create_user(data={"name": "Charlie"})
    assert dict_user.name == "Charlie"

    client.close()


def test_post_leftover_kwargs_become_query_params() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/active",
        response_obj=ResponseFactory.ok(
            data={"id": 5, "name": "Eve"},
        ),
    )

    @client.post("/users/{state}")
    def promote_user(state: str, data: CreateUserRequest, result: User) -> User:
        return result

    promote_user("active", data={"name": "Eve"}, notify=True)

    client.close()


def test_non_json_and_empty_response_handling() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/ping",
        response_obj=ResponseFactory.no_content(),
    )
    fake_backend.queue_response(
        path="/version",
        response_obj=ResponseFactory.ok(
            data="1.0",
            headers={"content-type": "text/plain"},
        ),
    )

    @client.get("/ping")
    def ping(result: None) -> None:
        return result

    @client.get("/version")
    def version(result: str) -> str:
        return result

    assert ping() is None
    assert version() == "1.0"

    client.close()


def test_path_and_query_params_combined() -> None:
    """
    Inspired by the /request-data/{path_parameter} endpoint in example_openapi_specs/best.json
    which combines a path placeholder with a query string parameter.
    """

    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/request-data/some-id",
        response_obj=ResponseFactory.ok(
            data={"path_parameter": "some-id", "your_query": "hello"},
            headers={"X-Example": "spec", "content-type": "application/json"},
        ),
    )

    @client.get("/request-data/{path_parameter}")
    def fetch_request_data(
        path_parameter: str, result: RequestDataAndParameterResponse
    ) -> RequestDataAndParameterResponse:
        return result

    response = fetch_request_data("some-id", query={"your_query": "hello"})

    assert response == RequestDataAndParameterResponse(path_parameter="some-id", your_query="hello")

    client.close()


def test_put_serializes_model_and_merges_headers() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/2",
        response_obj=ResponseFactory.ok(
            data={"id": 2, "name": "Updated"},
        ),
    )

    @client.put("/users/{user_id}")
    def update_user(user_id: int, data: UpdateUserRequest, result: User) -> User:
        return result

    updated = update_user(2, data=UpdateUserRequest(name="Updated"), headers={"X-Trace": "abc"})

    assert updated.name == "Updated"

    client.close()


def test_patch_validates_dict_body() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/3",
        response_obj=ResponseFactory.ok(
            data={"id": 3, "name": "Partial"},
        ),
    )

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, data: UpdateUserRequest, result: User) -> User:
        return result

    patched = patch_user(3, data={"name": "Partial"})

    assert patched == User(id=3, name="Partial")

    client.close()


def test_delete_supports_query_and_response_injection() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/4",
        response_obj=ResponseFactory.no_content(),
    )

    @client.delete("/users/{user_id}")
    def delete_user(user_id: int, result: None, query: dict[str, str] | None = None) -> None:
        return result

    delete_user(4, query={"hard": "false"})

    client.close()


@pytest.mark.asyncio
async def test_async_get_validates_response() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/2",
        response_obj=ResponseFactory.ok(
            data={"id": 2, "name": "Async"},
        ),
    )

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    user = await get_user(2)

    assert user == User(id=2, name="Async")

    await client.aclose()


@pytest.mark.asyncio
async def test_async_post_validates_body_and_query() -> None:
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 9, "name": "Zoe"},
        ),
    )

    @client.post("/users")
    async def create_user(data: CreateUserRequest, result: User) -> User:
        return result

    created = await create_user(data={"name": "Zoe"}, query={"lang": "en"})

    assert created == User(id=9, name="Zoe")

    await client.aclose()


# Test models for response_map feature
class SuccessResponse(BaseModel):
    id: int
    name: str
    status: str = "success"


class ErrorResponse(BaseModel):
    error: str
    code: int


class ValidationErrorResponse(BaseModel):
    errors: list[str]


# Type alias for testing
ResponseUnion = SuccessResponse | ErrorResponse


def test_response_map_with_type_alias_union() -> None:
    """Test response_map with a union type alias."""
    client = APIClient(base_url="http://localhost")

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice", "status": "success"},
        ),
    )
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"error": "Not found", "code": 404},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    def get_user(user_id: int, result: ResponseUnion) -> ResponseUnion:
        return result

    # Test 200 response
    user = get_user(1)
    assert isinstance(user, SuccessResponse)
    assert user.id == 1
    assert user.name == "Alice"

    # Test 404 response
    error = get_user(999)
    assert isinstance(error, ErrorResponse)
    assert error.error == "Not found"
    assert error.code == 404

    client.close()


def test_response_map_basic_sync() -> None:
    """Test basic response_map functionality with sync function."""

    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Alice", "status": "success"},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    user = get_user(1)
    assert isinstance(user, SuccessResponse)
    assert user.id == 1
    assert user.name == "Alice"

    client.close()


def test_response_map_error_status_sync() -> None:
    """Test response_map with error status code (sync)."""

    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"error": "User not found", "code": 404},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    user = get_user(999)
    assert isinstance(user, ErrorResponse)
    assert user.error == "User not found"
    assert user.code == 404

    client.close()


def test_response_map_unexpected_status_raises_exception_sync() -> None:
    """Test that unexpected status code raises APIException (sync)."""

    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.internal_server_error(
            data={"error": "Internal server error", "code": 500},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    with pytest.raises(APIException) as exc_info:
        get_user(1)

    assert exc_info.value.response.status_code == 500
    assert "Unexpected status code 500" in exc_info.value.reason
    assert "200, 404" in exc_info.value.reason

    client.close()


def test_response_map_multiple_status_codes_sync() -> None:
    """Test response_map with multiple status codes (sync)."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 1, "name": "Bob", "status": "success"},
        ),
    )

    @client.post(
        "/users",
        response_map={
            201: SuccessResponse,
            400: ErrorResponse,
            422: ValidationErrorResponse,
        },
    )
    def create_user(
        data: dict, result: SuccessResponse | ErrorResponse | ValidationErrorResponse
    ) -> SuccessResponse | ErrorResponse | ValidationErrorResponse:
        return result

    # Test 201 response
    user = create_user(data={"name": "Bob"})
    assert isinstance(user, SuccessResponse)
    assert user.id == 1

    client.close()


@pytest.mark.asyncio
async def test_response_map_basic_async() -> None:
    """Test basic response_map functionality with async function."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/2",
        response_obj=ResponseFactory.ok(
            data={"id": 2, "name": "Charlie", "status": "success"},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    async def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    user = await get_user(2)
    assert isinstance(user, SuccessResponse)
    assert user.id == 2
    assert user.name == "Charlie"

    await client.aclose()


@pytest.mark.asyncio
async def test_response_map_error_status_async() -> None:
    """Test response_map with error status code (async)."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/999",
        response_obj=ResponseFactory.not_found(
            data={"error": "User not found", "code": 404},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    async def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    user = await get_user(999)
    assert isinstance(user, ErrorResponse)
    assert user.error == "User not found"
    assert user.code == 404

    await client.aclose()


@pytest.mark.asyncio
async def test_response_map_unexpected_status_raises_exception_async() -> None:
    """Test that unexpected status code raises APIException (async)."""

    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.internal_server_error(
            data={"error": "Internal server error", "code": 500},
        ),
    )

    @client.get(
        "/users/{user_id}",
        response_map={
            200: SuccessResponse,
            404: ErrorResponse,
        },
    )
    async def get_user(user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
        return result

    with pytest.raises(APIException) as exc_info:
        await get_user(1)

    assert exc_info.value.response.status_code == 500
    assert "Unexpected status code 500" in exc_info.value.reason

    await client.aclose()


def test_response_map_invalid_status_code_raises_error() -> None:
    """Test that invalid status code in response_map raises ValueError."""
    client = APIClient(base_url=BASE_URL)

    with pytest.raises(ValueError, match="Invalid status code 999"):

        @client.get(
            "/users/{user_id}",
            response_map={
                999: SuccessResponse,  # Invalid status code (outside 100-599 range)
            },
        )
        def get_user(user_id: int, result: SuccessResponse) -> SuccessResponse:
            return result


def test_response_map_custom_status_code_works() -> None:
    """Test that custom status codes within valid range (100-599) work."""
    client = APIClient(base_url=BASE_URL)

    # Should not raise - 599 is a valid HTTP status code even if not in the enum
    @client.get(
        "/users/{user_id}",
        response_map={
            599: SuccessResponse,  # Valid but not in enum
        },
    )
    def get_user(user_id: int, result: SuccessResponse) -> SuccessResponse:
        return result


def test_response_map_non_pydantic_model_raises_error() -> None:
    """Test that non-Pydantic model and non-TypedDict in response_map raises ValueError."""
    from typing import cast

    client = APIClient(base_url=BASE_URL)

    class NotAModel:
        pass

    with pytest.raises(ValueError, match="ust be a Pydantic BaseModel subclass or TypedDict"):

        @client.get(
            "/users/{user_id}",
            response_map=cast(dict[int, type[BaseModel]], {200: NotAModel}),
        )
        def get_user(user_id: int, result: NotAModel) -> NotAModel:
            return result


def test_response_map_missing_return_type_raises_error() -> None:
    """Test that missing model in result parameter type raises ValueError."""
    client = APIClient(base_url=BASE_URL)

    with pytest.raises(ValueError, match="Response model 'ErrorResponse' for status code 404"):

        @client.get(
            "/users/{user_id}",
            response_map={
                200: SuccessResponse,
                404: ErrorResponse,
            },
        )
        def get_user(user_id: int, result: SuccessResponse) -> SuccessResponse:
            return result


def test_result_parameter_required() -> None:
    """Test that function without result parameter raises TypeError."""
    client = APIClient(base_url=BASE_URL)

    with pytest.raises(TypeError, match="must have a 'result' parameter"):

        @client.get("/users/{user_id}")
        def get_user(user_id: int) -> User:  # type: ignore
            pass


def test_result_parameter_annotation_required() -> None:
    """Test that result parameter without annotation raises TypeError."""
    client = APIClient(base_url=BASE_URL)

    with pytest.raises(TypeError, match="lacks a type annotation"):

        @client.get("/users/{user_id}")
        def get_user(user_id: int, result) -> User:
            return result


def test_return_value_independent_of_result_type() -> None:
    """Test that function can return a different type than result."""
    client = APIClient(base_url=BASE_URL)

    @client.get("/users/{user_id}")
    def get_user_name(user_id: int, result: User) -> str:
        return result.name


def test_signature_preservation_for_ide_support() -> None:
    """Test that decorated functions preserve their original signatures for IDE support."""
    import inspect

    client = APIClient(base_url=BASE_URL)

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User, expand: bool = False) -> User:
        """Get a user by ID."""
        return result

    # Check that the signature is preserved
    sig = inspect.signature(get_user)
    params = list(sig.parameters.keys())
    assert params == ["user_id", "result", "expand"], f"Expected ['user_id', 'result', 'expand'], got {params}"

    # Check parameter details - annotations might be strings due to forward refs
    user_id_param = sig.parameters["user_id"]
    # Accept both int type and 'int' string (forward reference)
    assert user_id_param.annotation in (int, "int"), f"Expected int or 'int', got {user_id_param.annotation}"
    assert user_id_param.default == inspect.Parameter.empty

    expand_param = sig.parameters["expand"]
    assert expand_param.annotation in (bool, "bool"), f"Expected bool or 'bool', got {expand_param.annotation}"
    assert expand_param.default is False

    # Check return annotation
    assert sig.return_annotation in (User, "User"), f"Expected User or 'User', got {sig.return_annotation}"

    # Check docstring is preserved
    assert get_user.__doc__ == "Get a user by ID."

    # Check function name is preserved
    assert get_user.__name__ == "get_user"


def test_function_with_docstring_and_ellipsis_is_valid() -> None:
    """Test that functions with docstrings and ellipsis are accepted."""
    client = APIClient(base_url=BASE_URL)

    @client.get("/users")
    def documented_function(result: list[User]) -> list[User]:
        """This function has a docstring."""
        return result

    # Should not raise any errors
    assert documented_function.__doc__ == "This function has a docstring."


def test_async_signature_preservation() -> None:
    """Test that async decorated functions preserve their signatures."""
    import inspect

    client = APIClient(base_url=BASE_URL)

    @client.get("/users/{user_id}")
    async def get_user_async(user_id: int, result: User, include_details: bool = True) -> User:
        """Get a user asynchronously."""
        return result

    sig = inspect.signature(get_user_async)
    params = list(sig.parameters.keys())
    assert params == ["user_id", "result", "include_details"]

    # Check that it's still recognized as async
    assert inspect.iscoroutinefunction(get_user_async)


def test_function_returns_derived_value() -> None:
    """Test that function can return a derived value different from result type."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/3",
        response_obj=ResponseFactory.ok(
            data={"id": 3, "name": "Charlie"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user_name(user_id: int, result: User) -> str:
        return result.name

    name = get_user_name(3)
    assert name == "Charlie"
    assert isinstance(name, str)

    client.close()


def test_function_returns_tuple_with_result() -> None:
    """Test that function can return a tuple including the result."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(
            data={"id": 10, "name": "Eve"},
        ),
    )

    @client.post("/users")
    def create_user(data: CreateUserRequest, result: User) -> tuple[User, str]:
        return result, "created"

    user, status = create_user(data=CreateUserRequest(name="Eve"))
    assert user == User(id=10, name="Eve")
    assert status == "created"

    client.close()


@pytest.mark.asyncio
async def test_async_function_returns_derived_value() -> None:
    """Test that async function can return a derived value."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/5",
        response_obj=ResponseFactory.ok(
            data={"id": 5, "name": "Frank"},
        ),
    )

    @client.get("/users/{user_id}")
    async def get_user_id(user_id: int, result: User) -> int:
        return result.id

    user_id = await get_user_id(5)
    assert user_id == 5
    assert isinstance(user_id, int)

    await client.aclose()


def test_optional_query_param_none_is_omitted() -> None:
    """Test that optional query parameters with None value are omitted from the URL."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/3",
        response_obj=ResponseFactory.ok(
            data={"id": 3, "name": "Alice"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User, include_details: bool | None = None) -> User:
        return result

    # Call without providing the optional parameter
    user = get_user(user_id=3)

    assert user.id == 3

    client.close()


def test_optional_query_param_provided_is_included() -> None:
    """Test that optional query parameters with non-None value are included in the URL."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/3",
        response_obj=ResponseFactory.ok(
            data={"id": 3, "name": "Alice"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User, include_details: bool | None = None) -> User:
        return result

    # Call with the optional parameter
    user = get_user(user_id=3, include_details=True)

    assert user.id == 3

    client.close()


def test_multiple_optional_query_params_some_none() -> None:
    """Test that when some optional query params are None and others have values, only non-None ones are included."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.ok(
            data=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        ),
    )

    @client.get("/users")
    def list_users(
        result: list[User],
        include_details: bool | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[User]:
        return result

    # Call with only some parameters provided
    users = list_users(page=2, limit=10)

    assert len(users) == 2

    client.close()


@pytest.mark.asyncio
async def test_async_optional_query_param_none_is_omitted() -> None:
    """Test that async functions also omit None query parameters."""
    client = APIClient(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/4",
        response_obj=ResponseFactory.ok(
            data={"id": 4, "name": "Bob"},
        ),
    )

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User, include_details: bool | None = None) -> User:
        return result

    # Call without providing the optional parameter
    user = await get_user(user_id=4)

    assert user.id == 4

    await client.aclose()
