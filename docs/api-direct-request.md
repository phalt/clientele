# 🎯 Direct Requests

Clientele supports making HTTP requests directly without using decorators through the `request()` and `arequest()` methods.

This approach is useful when you need to make ad-hoc API calls or when you don't want to define a decorated function for every endpoint.

## Basic Example

```python
from pydantic import BaseModel
from clientele import api

client = api.APIClient(base_url="https://api.example.com")

class Pokemon(BaseModel):
    id: int
    name: str
    height: int
    weight: int

# Direct GET request
result = client.request(
    "GET",
    "/pokemon/{id}",
    response_map={200: Pokemon},
    id=1
)

print(result.name)  # "bulbasaur"
```

## API Signature

```python
def request(
    method: str,
    path: str,
    *,
    response_map: dict[int, type[Any]],
    data: dict[str, Any] | BaseModel | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    **path_params: Any,
) -> Any
```

**Parameters**:

- `method`: HTTP method string (GET, POST, PUT, PATCH, DELETE)
- `path`: URL path template with optional placeholders like `/users/{user_id}`
- `response_map`: Mapping of HTTP status codes to response models (required)
- `data`: Optional request body for POST/PUT/PATCH/DELETE requests
- `query`: Optional dictionary of query parameters
- `headers`: Optional custom headers for this request
- `**path_params`: Path parameters as keyword arguments (e.g., `id=1`)

## POST Request with Data

```python
from pydantic import BaseModel
from clientele import api

client = api.APIClient(base_url="https://api.example.com")

class CreateUserRequest(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

# POST with Pydantic model
result = client.request(
    "POST",
    "/users",
    response_map={201: User},
    data=CreateUserRequest(name="Alice", email="alice@example.com")
)

# POST with dict
result = client.request(
    "POST",
    "/users",
    response_map={201: User},
    data={"name": "Bob", "email": "bob@example.com"}
)
```

## Multiple Status Codes

Direct requests support `response_map` just like decorator-based requests:

```python
from pydantic import BaseModel
from clientele import api

client = api.APIClient(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str

class NotFoundError(BaseModel):
    error: str
    code: int

result = client.request(
    "GET",
    "/users/{user_id}",
    response_map={
        200: User,
        404: NotFoundError,
    },
    user_id=123
)

# Handle different response types
match result:
    case User():
        print(f"Found: {result.name}")
    case NotFoundError():
        print(f"Error: {result.error}")
```

## Query Parameters and Headers

```python
from clientele import api

client = api.APIClient(base_url="https://api.example.com")

result = client.request(
    "GET",
    "/users/{user_id}",
    response_map={200: User},
    query={"include_details": "true", "format": "json"},
    headers={"X-Custom-Header": "value"},
    user_id=42
)
```

## Async Version

For async code, use `arequest()` instead:

```python
import asyncio
from clientele import api

client = api.APIClient(base_url="https://api.example.com")

async def fetch_user():
    result = await client.arequest(
        "GET",
        "/users/{user_id}",
        response_map={200: User},
        user_id=1
    )
    return result

user = asyncio.run(fetch_user())
```

## All HTTP Methods

Direct requests support all standard HTTP methods:

```python
# GET
result = client.request("GET", "/users/{id}", response_map={200: User}, id=1)

# POST
result = client.request("POST", "/users", response_map={201: User}, data={...})

# PUT
result = client.request("PUT", "/users/{id}", response_map={200: User}, data={...}, id=1)

# PATCH
result = client.request("PATCH", "/users/{id}", response_map={200: User}, data={...}, id=1)

# DELETE
result = client.request("DELETE", "/users/{id}", response_map={204: None}, id=1)
```

## Trade-offs

### What You Lose

When using direct requests instead of decorated functions, you lose several benefits:

**1. Strong typing for inputs**

With decorators, your IDE and type checkers know exactly what parameters are expected:

```python
# Decorator: IDE knows about user_id, name, email
@client.get("/users/{user_id}")
def get_user(user_id: int, name: str, email: str, result: User) -> User:
    return result

# Direct request: No type checking for parameters
result = client.request("GET", "/users/{user_id}", response_map={200: User}, user_id="oops")
```

**2. Strong typing for responses**

With decorators, the return type is explicitly declared in the function signature:

```python
# Decorator: Return type is clear
@client.get("/users/{user_id}")
def get_user(user_id: int, result: User) -> User:  # Returns User
    return result

# Direct request: Return type is Any
result = client.request(...)  # Type is Any, requires manual type narrowing
```

**3. Well-defined integration boundary**

Decorators create clear, reusable API client methods:

```python
# Decorator: Clear, reusable function
user = get_user(user_id=1)
user = get_user(user_id=2)

# Direct request: Repeated logic
user1 = client.request("GET", "/users/{id}", response_map={200: User}, id=1)
user2 = client.request("GET", "/users/{id}", response_map={200: User}, id=2)
```

**4. No streaming support**

Direct requests do not support Server-Sent Events or streaming responses. For streaming, you must use the decorator approach with `streaming_response=True`.

### What You Keep

Despite these trade-offs, direct requests retain important features:

**1. Response hydration and validation**

The `response_map` still drives response parsing and validation:

```python
# Response is parsed and validated into User model
result = client.request("GET", "/users/{id}", response_map={200: User}, id=1)
assert isinstance(result, User)
```

**2. Request data validation**

When using Pydantic models for `data`, validation still occurs:

```python
# CreateUserRequest is validated before sending
result = client.request(
    "POST",
    "/users",
    response_map={201: User},
    data=CreateUserRequest(name="Alice", email="invalid")  # Raises ValidationError
)
```

**3. Multiple status code handling**

Full `response_map` support with union types:

```python
result = client.request(
    "GET",
    "/users/{id}",
    response_map={200: User, 404: NotFoundError, 500: ServerError},
    id=1
)
# result type is User | NotFoundError | ServerError
```

## When to Use Direct Requests

**Good use cases**:

- Quick scripts and one-off API calls
- Prototyping and exploration
- Dynamic endpoints where the path or method changes
- Simple CRUD operations without complex logic

**Better with decorators**:

- Building a reusable API client library
- When you need strong typing throughout your codebase
- Complex workflows with multiple endpoints
- When you need streaming responses
- Production applications with strict type safety requirements

## Comparison Example

**With decorator (recommended for production)**:

```python
@client.get("/users/{user_id}", response_map={200: User, 404: NotFoundError})
def get_user(user_id: int, result: User | NotFoundError) -> User | NotFoundError:
    return result

# IDE autocomplete, type checking, clear interface
user = get_user(user_id=1)
```

**With direct request (good for quick tasks)**:

```python
# More verbose, less type safety, but flexible
user = client.request(
    "GET",
    "/users/{user_id}",
    response_map={200: User, 404: NotFoundError},
    user_id=1
)
```

Both approaches use the same underlying infrastructure and provide the same response hydration and validation capabilities.
