from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import APIClient, APIException, BaseConfig

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


@pytest.mark.respx(base_url=BASE_URL)
def test_get_validates_response_and_builds_query(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}, headers={"x-source": "mock"})
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User, include_details: bool = True) -> User:
        return result

    user = get_user(1)

    assert user == User(id=1, name="Ada")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/1"
    assert call.request.url.params.get("include_details") == "true"


@pytest.mark.respx(base_url=BASE_URL)
def test_get_respects_query_override_and_list_validation(respx_mock: MockRouter) -> None:
    client = APIClient(config=BaseConfig(base_url=BASE_URL, headers={"Authorization": "Bearer token"}))

    respx_mock.get("/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}])
    )

    @client.get("/users")
    def list_users(query: dict[str, str], result: list[User]) -> list[User]:  # type: ignore[return]
        return result

    users = list_users(query={"search": "dev"})

    assert [user.name for user in users] == ["Ada", "Bob"]
    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer token"
    assert call.request.url.params.get("search") == "dev"


@pytest.mark.respx(base_url=BASE_URL)
def test_post_accepts_model_instance_and_dict(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "Charlie"}))

    @client.post("/users")
    def create_user(data: CreateUserRequest, result: User) -> User:  # type: ignore[return]
        return result

    user = create_user(data=CreateUserRequest(name="Charlie"))
    assert user.id == 10

    dict_user = create_user(data={"name": "Charlie"})
    assert dict_user.name == "Charlie"

    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "Charlie"}


@pytest.mark.respx(base_url=BASE_URL)
def test_post_leftover_kwargs_become_query_params(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users/active").mock(return_value=httpx.Response(200, json={"id": 5, "name": "Eve"}))

    @client.post("/users/{state}")
    def promote_user(state: str, data: CreateUserRequest, result: User) -> User:
        return result

    promote_user("active", data={"name": "Eve"}, notify=True)

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/active"
    assert call.request.url.params.get("notify") == "true"


@pytest.mark.respx(base_url=BASE_URL)
def test_non_json_and_empty_response_handling(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/ping").mock(return_value=httpx.Response(204))
    respx_mock.get("/version").mock(return_value=httpx.Response(200, text="1.0"))

    @client.get("/ping")
    def ping(result: None) -> None:
        return result

    @client.get("/version")
    def version(result: str) -> str:
        return result

    assert ping() is None
    assert version() == "1.0"


@pytest.mark.respx(base_url=BASE_URL)
def test_path_and_query_params_combined(respx_mock: MockRouter) -> None:
    """
    Inspired by the /request-data/{path_parameter} endpoint in example_openapi_specs/best.json
    which combines a path placeholder with a query string parameter.
    """

    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/request-data/some-id").mock(
        return_value=httpx.Response(
            200, json={"path_parameter": "some-id", "your_query": "hello"}, headers={"X-Example": "spec"}
        )
    )

    @client.get("/request-data/{path_parameter}")
    def fetch_request_data(
        path_parameter: str, result: RequestDataAndParameterResponse
    ) -> RequestDataAndParameterResponse:
        return result

    response = fetch_request_data("some-id", query={"your_query": "hello"})

    assert response == RequestDataAndParameterResponse(path_parameter="some-id", your_query="hello")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/request-data/some-id"
    assert call.request.url.params["your_query"] == "hello"


@pytest.mark.respx(base_url=BASE_URL)
def test_put_serializes_model_and_merges_headers(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.put("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Updated"}))

    @client.put("/users/{user_id}")
    def update_user(user_id: int, data: UpdateUserRequest, result: User) -> User:
        return result

    updated = update_user(2, data=UpdateUserRequest(name="Updated"), headers={"X-Trace": "abc"})

    assert updated.name == "Updated"
    call = respx_mock.calls[0]
    assert call.request.headers["X-Trace"] == "abc"
    assert json.loads(call.request.content) == {"name": "Updated"}


@pytest.mark.respx(base_url=BASE_URL)
def test_patch_validates_dict_body(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.patch("/users/3").mock(return_value=httpx.Response(200, json={"id": 3, "name": "Partial"}))

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, data: UpdateUserRequest, result: User) -> User:
        return result

    patched = patch_user(3, data={"name": "Partial"})

    assert patched == User(id=3, name="Partial")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/3"
    assert json.loads(call.request.content) == {"name": "Partial"}


@pytest.mark.respx(base_url=BASE_URL)
def test_delete_supports_query_and_response_injection(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.delete("/users/4").mock(return_value=httpx.Response(204))

    @client.delete("/users/{user_id}")
    def delete_user(user_id: int, result: None, query: dict[str, str] | None = None) -> None:
        return result

    delete_user(4, query={"hard": "false"})

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/4"
    assert call.request.url.params.get("hard") == "false"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_async_get_validates_response(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Async"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    user = await get_user(2)

    assert user == User(id=2, name="Async")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/2"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_async_post_validates_body_and_query(respx_mock: MockRouter) -> None:
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 9, "name": "Zoe"}))

    @client.post("/users")
    async def create_user(data: CreateUserRequest, result: User) -> User:
        return result

    created = await create_user(data={"name": "Zoe"}, query={"lang": "en"})

    assert created == User(id=9, name="Zoe")
    call = respx_mock.calls[0]
    assert call.request.url.params["lang"] == "en"
    assert json.loads(call.request.content) == {"name": "Zoe"}


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


@pytest.mark.respx(base_url="http://localhost")
def test_response_map_with_type_alias_union(respx_mock: MockRouter) -> None:
    """Test response_map with a union type alias."""
    client = APIClient(base_url="http://localhost")

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alice", "status": "success"})
    )
    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "Not found", "code": 404}))

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


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_basic_sync(respx_mock: MockRouter) -> None:
    """Test basic response_map functionality with sync function."""

    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alice", "status": "success"})
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


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_error_status_sync(respx_mock: MockRouter) -> None:
    """Test response_map with error status code (sync)."""

    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "User not found", "code": 404}))

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


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_unexpected_status_raises_exception_sync(respx_mock: MockRouter) -> None:
    """Test that unexpected status code raises APIException (sync)."""

    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error", "code": 500})
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


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_multiple_status_codes_sync(respx_mock: MockRouter) -> None:
    """Test response_map with multiple status codes (sync)."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 1, "name": "Bob", "status": "success"}))

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
    ) -> SuccessResponse | ErrorResponse | ValidationErrorResponse:  # type: ignore[return]
        return result

    # Test 201 response
    user = create_user(data={"name": "Bob"})
    assert isinstance(user, SuccessResponse)
    assert user.id == 1


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_response_map_basic_async(respx_mock: MockRouter) -> None:
    """Test basic response_map functionality with async function."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/2").mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "Charlie", "status": "success"})
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


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_response_map_error_status_async(respx_mock: MockRouter) -> None:
    """Test response_map with error status code (async)."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/999").mock(return_value=httpx.Response(404, json={"error": "User not found", "code": 404}))

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


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_response_map_unexpected_status_raises_exception_async(respx_mock: MockRouter) -> None:
    """Test that unexpected status code raises APIException (async)."""

    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error", "code": 500})
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
        def get_user(user_id: int, result) -> User:  # type: ignore[no-untyped-def]  # result without annotation
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
    def get_user(user_id: int, result: User, expand: bool = False) -> User:  # type: ignore[return]
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


@pytest.mark.respx(base_url=BASE_URL)
def test_function_returns_derived_value(respx_mock: MockRouter) -> None:
    """Test that function can return a derived value different from result type."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/3").mock(return_value=httpx.Response(200, json={"id": 3, "name": "Charlie"}))

    @client.get("/users/{user_id}")
    def get_user_name(user_id: int, result: User) -> str:
        return result.name

    name = get_user_name(3)
    assert name == "Charlie"
    assert isinstance(name, str)


@pytest.mark.respx(base_url=BASE_URL)
def test_function_returns_tuple_with_result(respx_mock: MockRouter) -> None:
    """Test that function can return a tuple including the result."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "Eve"}))

    @client.post("/users")
    def create_user(data: CreateUserRequest, result: User) -> tuple[User, str]:
        return result, "created"

    user, status = create_user(data=CreateUserRequest(name="Eve"))
    assert user == User(id=10, name="Eve")
    assert status == "created"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_async_function_returns_derived_value(respx_mock: MockRouter) -> None:
    """Test that async function can return a derived value."""
    client = APIClient(base_url=BASE_URL)

    respx_mock.get("/users/5").mock(return_value=httpx.Response(200, json={"id": 5, "name": "Frank"}))

    @client.get("/users/{user_id}")
    async def get_user_id(user_id: int, result: User) -> int:
        return result.id

    user_id = await get_user_id(5)
    assert user_id == 5
    assert isinstance(user_id, int)
