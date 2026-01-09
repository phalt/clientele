# 📕 Documentation

## HTTP GET example

```python
from pydantic import BaseModel
from clientele import api as clientele_api
import httpx

client = clientele_api.APIClient(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str
    email: str

@client.get("/users/{user_id}")
def get_user(user_id: int, result: User, include_details: bool = True) -> User:
    return result

user = get_user(42)
```

How Clientele works:

- Path parameters inside `{}` are filled from the function arguments (e.g. `user_id`).
- Any remaining keyword arguments (like `include_details` above) become query parameters, but you can also provide a dict function parameter `query={...}` instead.
- The **`result` parameter is mandatory** and its type annotation (`User`) drives response parsing.
- Your function is injected with the `result` parameter - this is the response payload hydrated into your `result` parameter's type.
- The function's return value is independent - you can return the result directly, transform it, or return something completely different.

## HTTP POST example

```python
from typing import TypedDict
from pydantic import BaseModel
from clientele import api as clientele_api

client = clientele_api.APIClient(base_url="https://api.example.com")

# Using Pydantic models
class CreateUserRequest(BaseModel):
    name: str

class User(BaseModel):
    id: int
    name: str

@client.post("/users")
def create_user(*, data: CreateUserRequest, result: User) -> User:
    return result

user = create_user(data=CreateUserRequest(name="Ada"))

# Or use TypedDict for the `data` and `result` parameters
class CreateUserRequestDict(TypedDict):
    name: str

class UserDict(TypedDict):
    id: int
    name: str

@client.post("/users")
def create_user_with_dict(*, data: CreateUserRequestDict, result: UserDict) -> UserDict:
    return result

# Pass dict directly - no instantiation needed
user = create_user_with_dict(data={"name": "Ada"})

```

How body-based methods (POST, PUT, PATCH, DELETE) work with Clientele:

- The request body must be supplied via the `data` keyword argument.
- The `data` parameter can be a Pydantic model or a TypedDict.
- For Pydantic models, the data is validated and serialized to JSON automatically.
- For TypedDict, the data is sent as-is (because TypedDict provides type hints without runtime validation).
- The **`result` parameter is mandatory** and determines how the response is parsed.

## PUT, PATCH, and DELETE examples

```python
from pydantic import BaseModel
from clientele import api as clientele_api

client = clientele_api.APIClient(base_url="https://api.example.com")

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

## Return value independence

The `result` parameter defines **what response you get from the API**, but your function's return value is independent. This gives you flexibility:

```python
# Return the result directly (most common)
@client.get("/users/{user_id}")
def get_user(user_id: int, result: User) -> User:
    return result

# Return a derived value
@client.get("/users/{user_id}")
def get_user_email(user_id: int, result: User) -> str:
    return result.email

# Return multiple values as a tuple
@client.post("/events")
def create_event(data: EventIn, result: EventOut) -> tuple[EventOut, str]:
    log.info("Created event %s", result.id)
    return result, "success"
```

## Injected parameters

Clientele will inject the following parameters into your function once an http response is returned:

- `result`: an instance of the type specified in the `result` parameter annotation. This parameter is **mandatory** and its type annotation determines how the response is parsed. Can be a Pydantic model or a TypedDict.
- `response`: the `httpx.Response` - useful for logging, debugging etc. (optional)

## Response parsing rules

- If the response has a JSON content type, the payload is decoded from JSON.
- If the response type is not JSON then a `str` is returned.
- Empty body responses return `None`.
- The `result` parameter's type annotation drives response data validation. Pydantic models use `model_validate` for runtime validation, while TypedDict provides type hints without runtime validation.

## Custom response parsing

- You can provide a callable `response_parser` to the decorator to handle your own response parsing.
- `response_parser` will receive the `httpx.Response` object.
- The return type of the `response_parser` **must** match the type of the `result` parameter.
- You cannot provide `response_parser` and `response_mapping` (see below) at the same time.

Example:

```python
from clientele import api as clientele_api
import httpx
from pydantic import BaseModel

client = clientele_api.APIClient(base_url="http://localhost:8000")

class CustomResponseParserResponse(BaseModel):
    name: str
    other_value: str

# A custom handler for parsing the response
def custom_parser(response: httpx.Response) -> CustomResponseParserResponse:
    data = response.json()
    return CustomResponseParserResponse(name=data["name"], other_value="other value")

# Annotate the decorate to use, `result` type must match
@client.get("/users/{user_id}", response_parser=custom_parser)
def get_user_custom_response(user_id: int, result: CustomResponseParserResponse) -> str:
    return result.other_value

```

## Handling multiple response bodies and status codes

Real APIs often return different response models based on the HTTP status code. This is also a common feature of OpenAPI schemas.

The `response_map` parameter allows you to map status codes to specific Pydantic models or TypedDict classes, enabling proper type handling for success and error responses.

```python
from pydantic import BaseModel
from clientele import api as clientele_api

client = clientele_api.APIClient(base_url="https://api.example.com")

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

# For unexpected status codes, clientele.api.APIException is raised
try:
    get_user(-999)  # imagine the server returns 500
except clientele_api.APIException as e:
    print(f"Unexpected status: {e.response.status_code}")
    print(f"Reason: {e.reason}")
```

### `response_map` requirements

1. **Keys must be valid HTTP status codes**: Use the `codes` enum from `clientele.api` for reference, or any standard HTTP status code integers (100-599).
2. **Values must be Pydantic models or TypedDict**: Each value must be a `BaseModel` subclass or a `TypedDict` class.
3. **Result parameter type must include all models**: The `result` parameter's type annotation must be a Union containing all the Pydantic models or TypedDict classes used in `response_map`.
4. **Unexpected status codes raise `APIException`**: If the server returns a status code not in the `response_map`, an `APIException` is raised with details about the unexpected status.
5. **Precedence**: If `response_map` provides a model for the actual HTTP status code, that model is used. Otherwise, the `result` parameter annotation is used as the default for 2xx responses.

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

## Connection persistence

Clientele API will generate a singleton instance for the async and sync http clients. When you import the module and issue multiple function calls it will use the same http connection.
