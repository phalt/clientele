from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele import Client, Config, Routes

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
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}, headers={"x-source": "mock"})
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, include_details: bool = True, *, result: User, response: httpx.Response) -> User:
        assert response is not None
        assert response.headers["x-source"] == "mock"
        assert include_details is True
        return result

    user = get_user(1)

    assert user == User(id=1, name="Ada")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/1"
    assert call.request.url.params.get("include_details") == "true"


@pytest.mark.respx(base_url=BASE_URL)
def test_get_respects_query_override_and_list_validation(respx_mock: MockRouter) -> None:
    client = Client(config=Config(base_url=BASE_URL, headers={"Authorization": "Bearer token"}))

    respx_mock.get("/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}])
    )

    @client.get("/users")
    def list_users(query: dict[str, str], result: list[User]) -> list[User]:
        return result

    users = list_users(query={"search": "dev"})

    assert [user.name for user in users] == ["Ada", "Bob"]
    call = respx_mock.calls[0]
    assert call.request.headers["Authorization"] == "Bearer token"
    assert call.request.url.params.get("search") == "dev"


@pytest.mark.respx(base_url=BASE_URL)
def test_post_accepts_model_instance_and_dict(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "Charlie"}))

    @client.post("/users")
    def create_user(*, data: CreateUserRequest, result: User) -> User:
        return result

    user = create_user(data=CreateUserRequest(name="Charlie"))
    assert user.id == 10

    dict_user = create_user(data={"name": "Charlie"})
    assert dict_user.name == "Charlie"

    call = respx_mock.calls[0]
    assert json.loads(call.request.content) == {"name": "Charlie"}


@pytest.mark.respx(base_url=BASE_URL)
def test_post_leftover_kwargs_become_query_params(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users/active").mock(return_value=httpx.Response(200, json={"id": 5, "name": "Eve"}))

    @client.post("/users/{state}")
    def promote_user(state: str, *, data: CreateUserRequest, result: User) -> User:
        return result

    promote_user("active", data={"name": "Eve"}, notify=True)

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/active"
    assert call.request.url.params.get("notify") == "true"


@pytest.mark.respx(base_url=BASE_URL)
def test_non_json_and_empty_response_handling(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

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

    client = Client(base_url=BASE_URL)

    respx_mock.get("/request-data/some-id").mock(
        return_value=httpx.Response(
            200, json={"path_parameter": "some-id", "your_query": "hello"}, headers={"X-Example": "spec"}
        )
    )

    @client.get("/request-data/{path_parameter}")
    def fetch_request_data(
        path_parameter: str, *, result: RequestDataAndParameterResponse, response: httpx.Response
    ) -> RequestDataAndParameterResponse:
        assert response.headers["X-Example"] == "spec"
        return result

    response = fetch_request_data("some-id", query={"your_query": "hello"})

    assert response == RequestDataAndParameterResponse(path_parameter="some-id", your_query="hello")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/request-data/some-id"
    assert call.request.url.params["your_query"] == "hello"


@pytest.mark.respx(base_url=BASE_URL)
def test_put_serializes_model_and_merges_headers(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.put("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Updated"}))

    @client.put("/users/{user_id}")
    def update_user(user_id: int, *, data: UpdateUserRequest, result: User) -> User:
        return result

    updated = update_user(2, data=UpdateUserRequest(name="Updated"), headers={"X-Trace": "abc"})

    assert updated.name == "Updated"
    call = respx_mock.calls[0]
    assert call.request.headers["X-Trace"] == "abc"
    assert json.loads(call.request.content) == {"name": "Updated"}


@pytest.mark.respx(base_url=BASE_URL)
def test_patch_validates_dict_body(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.patch("/users/3").mock(return_value=httpx.Response(200, json={"id": 3, "name": "Partial"}))

    @client.patch("/users/{user_id}")
    def patch_user(user_id: int, *, data: UpdateUserRequest, result: User) -> User:
        return result

    patched = patch_user(3, data={"name": "Partial"})

    assert patched == User(id=3, name="Partial")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/3"
    assert json.loads(call.request.content) == {"name": "Partial"}


@pytest.mark.respx(base_url=BASE_URL)
def test_delete_supports_query_and_response_injection(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.delete("/users/4").mock(return_value=httpx.Response(204))

    @client.delete("/users/{user_id}")
    def delete_user(user_id: int, *, response: httpx.Response, query: dict[str, str] | None = None) -> None:
        assert response.status_code == 204
        return None

    delete_user(4, query={"hard": "false"})

    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/4"
    assert call.request.url.params.get("hard") == "false"


def test_routes_enable_per_instance_clients() -> None:
    routes = Routes()

    class API:
        def __init__(self, base_url: str) -> None:
            self._client = Client(base_url=base_url)

        @routes.get("/users/{user_id}")
        def get_user(self, user_id: int, result: User) -> User:
            return result

        @routes.post("/users")
        def create_user(self, *, data: CreateUserRequest, result: User) -> User:
            return result

    api_one = API("https://one.example")
    api_two = API("https://two.example")

    router_one = MockRouter(base_url="https://one.example")
    router_two = MockRouter(base_url="https://two.example")

    with router_one, router_two:
        router_one.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "One"}))
        router_two.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Two"}))

        assert router_one.calls == [] and router_two.calls == []

        one_user = api_one.get_user(1)
        two_user = api_two.get_user(1)

        assert one_user.name == "One"
        assert two_user.name == "Two"
        assert router_one.calls[0].request.url.host == "one.example"
        assert router_two.calls[0].request.url.host == "two.example"

        router_one.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "Uno"}))
        created = api_one.create_user(data={"name": "Uno"})

        assert created == User(id=10, name="Uno")
        assert json.loads(router_one.calls[-1].request.content) == {"name": "Uno"}


def test_routes_require_client_attribute() -> None:
    routes = Routes()

    class API:
        @routes.get("/ping")
        def ping(self, result: str) -> str:
            return result

    api = API()

    with pytest.raises(AttributeError):
        api.ping()


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_async_get_validates_response(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Async"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, *, result: User) -> User:
        return result

    user = await get_user(2)

    assert user == User(id=2, name="Async")
    call = respx_mock.calls[0]
    assert call.request.url.path == "/users/2"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_async_post_validates_body_and_query(respx_mock: MockRouter) -> None:
    client = Client(base_url=BASE_URL)

    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 9, "name": "Zoe"}))

    @client.post("/users")
    async def create_user(*, data: CreateUserRequest, result: User) -> User:
        return result

    created = await create_user(data={"name": "Zoe"}, query={"lang": "en"})

    assert created == User(id=9, name="Zoe")
    call = respx_mock.calls[0]
    assert call.request.url.params["lang"] == "en"
    assert json.loads(call.request.content) == {"name": "Zoe"}


@pytest.mark.asyncio
async def test_routes_support_async_methods() -> None:
    routes = Routes()

    class API:
        def __init__(self, base_url: str) -> None:
            self._client = Client(base_url=base_url)

        @routes.get("/users/{user_id}")
        async def get_user(self, user_id: int, result: User) -> User:
            return result

        @routes.post("/users")
        async def create_user(self, *, data: CreateUserRequest, result: User) -> User:
            return result

    api_one = API("https://async-one.example")
    api_two = API("https://async-two.example")

    router_one = MockRouter(base_url="https://async-one.example")
    router_two = MockRouter(base_url="https://async-two.example")

    with router_one, router_two:
        router_one.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "One"}))
        router_two.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Two"}))

        one_user = await api_one.get_user(1)
        two_user = await api_two.get_user(1)

        assert one_user.name == "One"
        assert two_user.name == "Two"

        router_one.post("/users").mock(return_value=httpx.Response(201, json={"id": 10, "name": "Uno"}))
        created = await api_one.create_user(data={"name": "Uno"})

        assert created == User(id=10, name="Uno")
        assert json.loads(router_one.calls[-1].request.content) == {"name": "Uno"}


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


@pytest.mark.respx(base_url=BASE_URL)
def test_response_map_basic_sync(respx_mock: MockRouter) -> None:
    """Test basic response_map functionality with sync function."""

    client = Client(base_url=BASE_URL)

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

    client = Client(base_url=BASE_URL)

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
    from clientele import APIException

    client = Client(base_url=BASE_URL)

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
    client = Client(base_url=BASE_URL)

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
    ) -> SuccessResponse | ErrorResponse | ValidationErrorResponse:
        return result

    # Test 201 response
    user = create_user(data={"name": "Bob"})
    assert isinstance(user, SuccessResponse)
    assert user.id == 1


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_response_map_basic_async(respx_mock: MockRouter) -> None:
    """Test basic response_map functionality with async function."""
    client = Client(base_url=BASE_URL)

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
    client = Client(base_url=BASE_URL)

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
    from clientele import APIException

    client = Client(base_url=BASE_URL)

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
    client = Client(base_url=BASE_URL)

    with pytest.raises(ValueError, match="Invalid status code 999"):

        @client.get(
            "/users/{user_id}",
            response_map={
                999: SuccessResponse,  # Invalid status code
            },
        )
        def get_user(user_id: int, result: SuccessResponse) -> SuccessResponse:
            return result


def test_response_map_non_pydantic_model_raises_error() -> None:
    """Test that non-Pydantic model in response_map raises ValueError."""
    client = Client(base_url=BASE_URL)

    class NotAModel:
        pass

    with pytest.raises(ValueError, match="must be a Pydantic BaseModel subclass"):

        @client.get(
            "/users/{user_id}",
            response_map={
                200: NotAModel,  # type: ignore
            },
        )
        def get_user(user_id: int, result: NotAModel) -> NotAModel:  # type: ignore
            return result


def test_response_map_missing_return_type_raises_error() -> None:
    """Test that missing model in return type raises ValueError."""
    client = Client(base_url=BASE_URL)

    with pytest.raises(ValueError, match="Response model 'ErrorResponse' for status code 404"):

        @client.get(
            "/users/{user_id}",
            response_map={
                200: SuccessResponse,
                404: ErrorResponse,
            },
        )
        def get_user(user_id: int, result: SuccessResponse) -> SuccessResponse:  # Missing ErrorResponse
            return result


def test_response_map_no_return_annotation_raises_error() -> None:
    """Test that function without return annotation raises ValueError."""
    client = Client(base_url=BASE_URL)

    with pytest.raises(ValueError, match="must have a return type annotation"):

        @client.get(
            "/users/{user_id}",
            response_map={
                200: SuccessResponse,
            },
        )
        def get_user(user_id: int, result: SuccessResponse):  # No return annotation
            return result


@pytest.mark.respx(base_url=BASE_URL)
def test_routes_response_map_sync(respx_mock: MockRouter) -> None:
    """Test response_map with Routes (sync)."""
    routes = Routes()

    class API:
        def __init__(self, base_url: str) -> None:
            self._client = Client(base_url=base_url)

        @routes.get(
            "/users/{user_id}",
            response_map={
                200: SuccessResponse,
                404: ErrorResponse,
            },
        )
        def get_user(self, user_id: int, result: SuccessResponse | ErrorResponse) -> SuccessResponse | ErrorResponse:
            return result

    api = API(BASE_URL)

    respx_mock.get("/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Dave", "status": "success"})
    )

    user = api.get_user(1)
    assert isinstance(user, SuccessResponse)
    assert user.name == "Dave"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_routes_response_map_async(respx_mock: MockRouter) -> None:
    """Test response_map with Routes (async)."""
    routes = Routes()

    class API:
        def __init__(self, base_url: str) -> None:
            self._client = Client(base_url=base_url)

        @routes.get(
            "/users/{user_id}",
            response_map={
                200: SuccessResponse,
                404: ErrorResponse,
            },
        )
        async def get_user(
            self, user_id: int, result: SuccessResponse | ErrorResponse
        ) -> SuccessResponse | ErrorResponse:
            return result

    api = API(BASE_URL)

    respx_mock.get("/users/2").mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "Eve", "status": "success"})
    )

    user = await api.get_user(2)
    assert isinstance(user, SuccessResponse)
    assert user.name == "Eve"
