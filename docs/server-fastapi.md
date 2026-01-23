# ⚡️ Using Clientele with FastAPI

This guide shows you how to scaffold a Python client for a FastAPI application using Clientele.

> **💡 Working Example**: See a real FastAPI application with code examples from this guide in [`server_examples/fastapi/`](https://github.com/phalt/clientele/tree/main/server_examples/fastapi)

## Prerequisites

- A FastAPI application with API endpoints
- FastAPI's automatic OpenAPI schema generation enabled (enabled by default)

## Step 1: Get Your OpenAPI Schema

FastAPI automatically generates an OpenAPI schema for your API. You can access it at:

```sh
http://your-api-domain/openapi.json
```

For example, if your FastAPI app is running locally on port 8000:

```sh
http://localhost:8000/openapi.json
```

### Downloading the Schema

You can either:

**Option A: Use the URL directly** (if the API is accessible):

```sh
clientele start-api -u http://localhost:8000/openapi.json -o my_client/
```

**Option B: Download the schema file first**:

```sh
curl http://localhost:8000/openapi.json > openapi.json
clientele start-api -f openapi.json -o my_client/
```

## Step 2: Scaffold the Client

```sh
clientele start-api -u http://localhost:8000/openapi.json -o my_client/
```

### Async Client

If your FastAPI app uses async endpoints and you want an async client:

```sh
clientele start-api -u http://localhost:8000/openapi.json -o my_client/ --asyncio
```

## Step 3: Use the scaffolded Client

### Usage Example

```python
from my_client import client, schemas

# Call a simple GET endpoint
response = client.get_users_users_get()

# Call a POST endpoint with data
user_data = schemas.CreateUserRequest(
    name="Alice",
    email="alice@example.com"
)
response = client.create_user_users_post(data=user_data)

# Handle different response types
match response:
    case schemas.UserResponse():
        print(f"User created: {response.name}")
    case schemas.HTTPValidationError():
        print(f"Validation error: {response.detail}")
```

### Async usage Example

```python
from my_async_client import client, schemas

async def create_user():
    user_data = schemas.CreateUserRequest(
        name="Alice",
        email="alice@example.com"
    )
    response = await client.create_user_users_post(data=user_data)
    return response
```

## Working with operationId

FastAPI generates `operationId` values for each endpoint, which Clientele uses to create function names.

### Default operationId Generation

By default, FastAPI creates operation IDs like: `{function_name}_{path}_{method}`

For example:

- Function `get_users()` at path `/users` with GET → `get_users_users_get`
- Function `create_user()` at path `/users` with POST → `create_user_users_post`

### Custom operationId

You can customize the operation ID in FastAPI to get cleaner function names:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users", operation_id="list_users")
def get_users():
    return []

@app.post("/users", operation_id="create_user")
def create_user(user: UserCreate):
    return user
```

This generates:

- `client.list_users()` instead of `client.get_users_users_get()`
- `client.create_user()` instead of `client.create_user_users_post()`

## Authentication

See [api authentication](api-authentication.md).

## Path and Query Parameters

FastAPI's path and query parameters are automatically converted to function arguments:

**FastAPI Endpoint**

```python
@app.get("/users/{user_id}")
def get_user(user_id: int, include_posts: bool = False):
    return {"user_id": user_id, "include_posts": include_posts}
```

**Client Usage**

```python
# Required path parameter, optional query parameter
response = client.get_user_users_user_id_get(
    user_id=123,
    include_posts=True
)
```

## Response Models

FastAPI's response models become Pydantic schemas in the client:

**FastAPI Endpoint**

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    return User(id=user_id, name="Alice", email="alice@example.com")
```

**Generated Client Usage**

```python
response = client.get_user_users_user_id_get(user_id=123)
# response is typed as schemas.User
print(response.name)
```

## Best Practices

1. **Use custom operationId** values for cleaner function names
2. **Keep schemas in sync** by regenerating after API changes
3. **Version your generated client** in git to track changes
4. **Test thoroughly** after regenerating
5. **Use the same Python version** for both API and client when possible

## Next Steps

- [Configure authentication](api-authentication.md)
- [Set up testing](api-testing.md)
