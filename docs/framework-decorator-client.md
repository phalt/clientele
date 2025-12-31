# Decorator-Based Runtime Client

Clientele now ships with a lightweight, decorator-driven HTTP client that you can use without generating code. It feels similar to Flask/FastAPI route decorators, but it is designed for outgoing requests. The same client works for both synchronous and ``async`` functions—no separate classes to import.

!!! warning "Real function bodies required"

    Decorated functions must have a real body. The HTTP request runs when the decorated function is called, and the parsed response is injected into the function.

## Importing and configuring

```python
from clientele import Client, Config

config = Config(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer <token>"},
    timeout=10.0,
)
client = Client(config=config)

# Convenience shortcut
client = Client(base_url="https://api.example.com")
```

The `Config` mirrors the familiar options from generated clients (base URL, headers, timeout, authentication, redirects, etc.) so you can keep the same mental model for HTTP behavior.

Use the same client instance for sync or async handlers:

```python
client = Client(base_url="https://api.example.com")

# sync
@client.get("/ping")
def ping(result: str) -> str:
    return result

# async
@client.get("/version")
async def version(result: str) -> str:
    return result

assert ping() == "pong"
version_string = await version()
```

## GET example

```python
from typing import Optional
from pydantic import BaseModel
from clientele import Client

client = Client(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str
    email: Optional[str]

@client.get("/users/{user_id}")
def get_user(user_id: int, include_details: bool = True, result: User, response=None) -> User:
    assert response.status_code == 200
    return result

user = get_user(42)
```

How it works:

- Path parameters inside `{}` are filled from the function arguments (e.g. `user_id`).
- Any remaining keyword arguments become query parameters unless you provide `query={...}`.
- The return type (`-> User`) drives response parsing; there is no need for a separate `response_model` argument.
- If your function accepts a `result` parameter, the parsed payload is injected. If your function accepts a `response` parameter, the underlying `httpx.Response` is injected.

### Path + query together

Borrowing from the example OpenAPI spec at `example_openapi_specs/best.json` (the `/request-data/{path_parameter}` path), you can blend path substitution with explicit query parameters:

```python
from pydantic import BaseModel
from clientele import Client

client = Client(base_url="https://api.example.com")

class RequestDataResponse(BaseModel):
    path_parameter: str
    your_query: str

@client.get("/request-data/{path_parameter}")
def fetch_request_data(path_parameter: str, *, result: RequestDataResponse) -> RequestDataResponse:
    return result

response = fetch_request_data("some-id", query={"your_query": "hello"})
assert response.path_parameter == "some-id"
assert response.your_query == "hello"
```

## Class-based APIs (Pattern A)

The functional decorator style above still works as-is. If you prefer class-based APIs with per-instance configuration, use ``Routes`` to declare endpoints at import time and attach a ``Client`` to each instance:

```python
from clientele import Client, Config, Routes
from pydantic import BaseModel

routes = Routes()


class User(BaseModel):
    id: int
    name: str


class UsersAPI:
    def __init__(self, base_url: str):
        self._client = Client(config=Config(base_url=base_url))

    @routes.get("/users/{user_id}")
    def get_user(self, user_id: int, *, result: User) -> User:
        return result

    @routes.post("/users")
    async def create_user(self, *, data: dict[str, str], result: User) -> User:
        return result


api_one = UsersAPI("https://api-one.example")
api_two = UsersAPI("https://api-two.example")

first = api_one.get_user(1)  # hits https://api-one.example
second = await api_two.get_user(1)  # hits https://api-two.example
```

Notes:

- ``Routes`` decorators only record metadata; the HTTP request runs when the method is called.
- The instance must expose a ``_client`` attribute (or override ``Routes(client_attribute="...")``) containing a ``Client``.
- Decorated methods still need real bodies (no ``...``) and reuse the same request/response parsing rules as the functional style.

## POST example with request validation

```python
from pydantic import BaseModel
from clientele import Client

client = Client(base_url="https://api.example.com")

class CreateUserRequest(BaseModel):
    name: str

class User(BaseModel):
    id: int
    name: str

@client.post("/users")
def create_user(*, data: CreateUserRequest, notify: bool = False, result: User) -> User:
    # `data` can be a model instance or a dict; it is validated and serialized to JSON.
    return result

# Pass a model instance
user = create_user(data=CreateUserRequest(name="Ada"))

# Or pass a plain dict, which will be validated into the annotated model
user = create_user(data={"name": "Ada"}, query={"notify": "true"})
```

Body-based methods (POST, PUT, PATCH, DELETE) specifics:

- The request body must be supplied via the `data` keyword argument.
- If `data` is annotated with a Pydantic model, you can pass either a model instance or a `dict`; it will be validated and serialized to JSON automatically.
- Remaining keyword arguments become query parameters unless you supply an explicit `query={...}` override.

## PUT, PATCH, and DELETE examples

```python
from pydantic import BaseModel
from clientele import Client

client = Client(base_url="https://api.example.com")

class UpdateUser(BaseModel):
    name: str

class User(BaseModel):
    id: int
    name: str

# PUT with a full body
@client.put("/users/{user_id}")
def update_user(user_id: int, *, data: UpdateUser, result: User) -> User:
    return result

updated = update_user(1, data={"name": "New Name"})

# PATCH with partial data
@client.patch("/users/{user_id}")
def patch_user(user_id: int, *, data: dict[str, str], result: User) -> User:
    return result

patched = patch_user(1, data={"name": "Another Name"})

# DELETE with path params and optional query
@client.delete("/users/{user_id}")
def delete_user(user_id: int, *, query: dict[str, str] | None = None, response=None) -> None:
    assert response.status_code == 204

delete_user(1, query={"hard": "false"})
```

## Response parsing rules

- If the response has a JSON content type, the payload is decoded from JSON; otherwise the raw text is returned. Empty responses yield `None`.
- Return annotations drive validation:
    - `BaseModel` subclasses use `model_validate` (Pydantic v2) or `parse_obj` (Pydantic v1).
    - Collections and other annotated types use `TypeAdapter` (Pydantic v2) or `parse_obj_as` (Pydantic v1).
    - If no return annotation is present, the raw payload is returned without validation.

## Handling multiple response types with `response_map`

Real APIs often return different response models based on the HTTP status code. The `response_map` parameter allows you to map status codes to specific Pydantic models, enabling proper type handling for success and error responses.

```python
from pydantic import BaseModel
from clientele import Client, APIException

client = Client(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str

class NotFoundError(BaseModel):
    error: str
    code: int

class ValidationError(BaseModel):
    errors: list[str]

@client.get(
    "/users/{user_id}",
    response_map={
        200: User,
        404: NotFoundError,
    }
)
def get_user(user_id: int, result: User | NotFoundError) -> User | NotFoundError:
    return result

# Returns User for 200 responses
user = get_user(1)
if isinstance(user, User):
    print(f"Found user: {user.name}")
elif isinstance(user, NotFoundError):
    print(f"Error: {user.error}")

# For unexpected status codes, APIException is raised
try:
    get_user(999)  # If server returns 500
except APIException as e:
    print(f"Unexpected status: {e.response.status_code}")
    print(f"Reason: {e.reason}")
```

### `response_map` requirements

1. **Keys must be valid HTTP status codes**: Use the `codes` enum from `clientele` for reference, or any standard HTTP status code (100-599).
2. **Values must be Pydantic models**: Each value must be a `BaseModel` subclass.
3. **Return type must include all models**: The function's return type annotation must be a Union containing all the Pydantic models used in `response_map`.
4. **Unexpected status codes raise `APIException`**: If the server returns a status code not in the `response_map`, an `APIException` is raised with details about the unexpected status.

### Multi-status example with POST

```python
@client.post(
    "/users",
    response_map={
        201: User,
        400: ValidationError,
        422: ValidationError,
    }
)
def create_user(
    data: dict, result: User | ValidationError
) -> User | ValidationError:
    return result

# Handle different responses
response = create_user(data={"name": "Alice"})
if isinstance(response, User):
    print(f"Created user {response.id}")
elif isinstance(response, ValidationError):
    print(f"Validation failed: {response.errors}")
```

### Works with Routes too

The `response_map` parameter works seamlessly with the `Routes` decorator for class-based APIs:

```python
from clientele import Client, Routes

routes = Routes()

class UsersAPI:
    def __init__(self, base_url: str):
        self._client = Client(base_url=base_url)
    
    @routes.get(
        "/users/{user_id}",
        response_map={
            200: User,
            404: NotFoundError,
        }
    )
    def get_user(self, user_id: int, result: User | NotFoundError) -> User | NotFoundError:
        return result

api = UsersAPI("https://api.example.com")
user = api.get_user(1)
```

### OpenAPI compatibility

The `response_map` feature is designed to work well with OpenAPI schemas. When generating clients from OpenAPI specifications, similar response mapping is used automatically. This decorator-based approach gives you the same flexibility when hand-authoring API clients.

## When to use the decorator client

- You want to hand-author a few calls without generating a full client.
- You prefer a framework-like, decorator-based style for outgoing requests.
- You still want strong typing and Pydantic validation driven by your function annotations.

For large APIs or when you want all operations generated for you, the existing code generation flow remains the best fit. Use whichever mode matches your workflow.
