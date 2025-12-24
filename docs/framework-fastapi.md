# Using Clientele with FastAPI

This guide shows you how to generate a Python client for a FastAPI application using Clientele.

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
clientele generate -u http://localhost:8000/openapi.json -o my_client/
```

**Option B: Download the schema file first**:

```sh
curl http://localhost:8000/openapi.json > openapi.json
clientele generate -f openapi.json -o my_client/
```

## Step 2: Generate the Client

### Basic Generation

Generate a function-based client (recommended for most use cases):

```sh
clientele generate -u http://localhost:8000/openapi.json -o my_client/
```

### Class-Based Client

If you prefer an object-oriented approach:

```sh
clientele generate-class -u http://localhost:8000/openapi.json -o my_client/
```

### Async Client

If your FastAPI app uses async endpoints and you want an async client:

```sh
clientele generate -u http://localhost:8000/openapi.json -o my_client/ --asyncio t
```

## Step 3: Use the Generated Client

### Function-Based Client Example

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

### Async Client Example

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

### HTTP Bearer Authentication

If your FastAPI app uses HTTP Bearer authentication:

```python
# FastAPI app
from fastapi import Depends, FastAPI
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
def protected_route(token: str = Depends(security)):
    return {"message": "authenticated"}
```

Configure the client's `config.py`:

```python
def get_bearer_token() -> str:
    """
    Provide your authentication token here.
    Does not require the "Bearer" prefix.
    """
    from os import environ
    return environ.get("API_TOKEN", "your-token-here")
```

### HTTP Basic Authentication

For HTTP Basic auth in FastAPI:

```python
# FastAPI app
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/protected")
def protected_route(credentials: HTTPBasicCredentials = Depends(security)):
    return {"username": credentials.username}
```

Configure the client's `config.py`:

```python
def get_user_key() -> str:
    return "your-username"

def get_pass_key() -> str:
    return "your-password"
```

## Regenerating the Client

When you update your FastAPI endpoints, regenerate the client:

```sh
clientele generate -u http://localhost:8000/openapi.json -o my_client/ --regen t
```

The `--regen t` flag tells Clientele to regenerate the client. Your `config.py` will not be overwritten.

### Workflow Integration

1. Update your FastAPI endpoints
2. Run `clientele generate` with `--regen t`
3. Review the changes with `git diff`
4. Run your tests to ensure everything still works
5. Commit the updated client

## Path and Query Parameters

FastAPI's path and query parameters are automatically converted to function arguments:

### FastAPI Endpoint

```python
@app.get("/users/{user_id}")
def get_user(user_id: int, include_posts: bool = False):
    return {"user_id": user_id, "include_posts": include_posts}
```

### Generated Client Usage

```python
# Required path parameter, optional query parameter
response = client.get_user_users_user_id_get(
    user_id=123,
    include_posts=True
)
```

## Response Models

FastAPI's response models become Pydantic schemas in the client:

### FastAPI Endpoint

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

### Generated Client Usage

```python
response = client.get_user_users_user_id_get(user_id=123)
# response is typed as schemas.User
print(response.name)
```

## Known Limitations

### OpenAPI Version

- **Supported**: FastAPI's default OpenAPI 3.0.x schemas work perfectly
- **Partial Support**: Some OpenAPI 3.1 features may not be fully supported yet
- **Not Supported**: OpenAPI 2.0 (Swagger) is not supported

### Complex Schema Features

- Most FastAPI/Pydantic features work out of the box
- `oneOf`, `anyOf`, and `nullable` are fully supported
- Some exotic schema combinations may require manual adjustment

### File Uploads

File upload endpoints may require manual customization of the generated client code.

### Callbacks and Webhooks

Clientele specifically focuses on calling an API and doesn't handle callbacks or webhooks - these are features usually seen in a web server.

## Best Practices

1. **Use custom operationId** values for cleaner function names
2. **Keep schemas in sync** by regenerating after API changes
3. **Version your generated client** in git to track changes
4. **Test thoroughly** after regenerating
5. **Use the same Python version** for both API and client when possible

## Next Steps

- [Learn about regeneration workflow](usage.md#regenerating)
- [Configure authentication](examples.md#authentication)
- [Set up testing with respx](testing.md)
- [Understand client structure](examples.md)
