# Clientele framework

Clientele framework is a decorator-driven http client that can create elegant API integrations.

It intentionally works similar to FastAPI route decorators, which has taught us that:

- Functions are a popular unit for encapsulating endpoint behaviour
- Decorators are popular for declaring the configuration for those endpoints
- Types are amazing for documentation and validation

With Clientele we can follow these same rules but flip around who is sending and receiving data:

- the decorator issues the http request with the validated payload
- the decorator parses the http response and returns a typed object back to the function.
- The function becomes the high-level abstraction for the endpoint and defines the typed input and typed output for the rest of your application.

## GET example

```python
from pydantic import BaseModel
from clientele import framework
import httpx

client = framework.Client(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str
    email: str

@client.get("/users/{user_id}")
def get_user(user_id: int, include_details: bool = True, result: User) -> User:
    return result

user = get_user(42)
```

How it works:

- Path parameters inside `{}` are filled from the function arguments (e.g. `user_id`).
- Any remaining keyword arguments (like `include_details` above) become query parameters, but you can also provide a dict parameter `query={...}`.
- The return type (`-> User`) drives response parsing.
- Your function is injected with a `result` parameter - the response payload hydrated into your function's return type.

## POST example

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
def create_user(*, data: CreateUserRequest, result: User) -> User:
    return result

user = create_user(data=CreateUserRequest(name="Ada"))

```

How body-based methods (POST, PUT, PATCH, DELETE) work:

- The request body must be supplied via the `data` keyword argument.
- The `data` object must be a Pydantic model.
- Before being sent it will be validated and serialized to JSON automatically.

## PUT, PATCH, and DELETE examples

```python
from pydantic import BaseModel
from clientele import Client

client = Client(base_url="https://api.example.com")

class UpdateUser(BaseModel):
    name: str
    email: str

class PatchNameUser(BaseModel):
    name: str

class User(BaseModel):
    id: int
    name: str

# PUT with a full body
@client.put("/users/{user_id}")
def update_user(user_id: int, *, data: UpdateUser, result: User) -> User:
    return result

updated = update_user(1, data=UpdateUser(name="New Name", email="test@foo.com"))

# PATCH with partial data
@client.patch("/users/{user_id}")
def patch_user_name(user_id: int, *, data: PatchNameUser, result: User) -> User:
    return result

patched = patch_user_name(1, data=PatchUserName(name="New Name"))

# DELETE that returns an empty response body
@client.delete("/users/{user_id}")
def delete_user(user_id: int, *, result: None) -> None:
    return result

delete_user(1)
```

## Injected parameters

Clientele will inject the following parameters into your function once an http response is returned:

- `result`: an instance of return type of the function. This **must** be returned by the function for the decorator to work.
- `response`: the `httpx.Response` - useful for logging, debugging etc.

## Response parsing rules

- If the response has a JSON content type, the payload is decoded from JSON.
- If the response type is not JSON then a `str` is returned.
- Empty body responses return `None`.
- Return annotations drive response data validation with the `model_validate` method on pydantic models.

## Handling multiple response bodies and status codes

Real APIs often return different response models based on the HTTP status code. This is also a common feature of OpenAPI schemas.

The `response_map` parameter allows you to map status codes to specific Pydantic models, enabling proper type handling for success and error responses.

```python
from pydantic import BaseModel
from clientele.framework import Client, APIException

client = Client(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str

class NotFoundError(BaseModel):
    error: str
    code: int

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
match user:
    case User():
        print(f"Found user: {user.name}")
    case NotFoundError() :
        print(f"Error: {user.error}")

# For unexpected status codes, clientele.framework.APIException is raised
try:
    get_user(-999)  # imagine the server returns 500
except APIException as e:
    print(f"Unexpected status: {e.response.status_code}")
    print(f"Reason: {e.reason}")
```

### `response_map` requirements

1. **Keys must be valid HTTP status codes**: Use the `codes` enum from `clientele.framework` for reference, or any standard HTTP status code integers (100-599).
2. **Values must be Pydantic models**: Each value must be a `BaseModel` subclass.
3. **Return type must include all models**: The function's return type annotation must be a Union containing all the Pydantic models used in `response_map`.
4. **Unexpected status codes raise `APIException`**: If the server returns a status code not in the `response_map`, an `APIException` is raised with details about the unexpected status.

#### Multi-status example with POST

If multiple statuses return the same response it is easy enough to extend the map:

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
    data: User, result: User | ValidationError
) -> User | ValidationError:
    return result

# Handle different responses
response = create_user(data=User(name="Alice"))
match response:
    case User():
        print(f"Created user {response.id}")
    case ValidationError():
        print(f"Validation failed: {response.errors}")
```
