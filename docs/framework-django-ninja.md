# Using Clientele with Django Ninja

This guide shows you how to generate a Python client for a Django Ninja API using Clientele.

> **💡 Working Example**: See a real Django Ninja application with code examples from this guide in [`server_examples/django-ninja/`](https://github.com/phalt/clientele/tree/main/server_examples/django-ninja)

## Prerequisites

- A Django application with [Django Ninja](https://django-ninja.dev/) installed
- Django Ninja automatically generates OpenAPI schemas (enabled by default)

## Step 1: Get Your OpenAPI Schema

Django Ninja automatically generates an OpenAPI schema for your API. By default, it's available at:

```sh
http://your-api-domain/api/openapi.json
```

For local development:

```sh
http://localhost:8000/api/openapi.json
```

The exact path depends on how you've mounted your Django Ninja API in your URLs.

### Example Django Ninja Setup

```python
# urls.py
from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI()

# Your endpoints here...

urlpatterns = [
    path("api/", api.urls),
]
```

With this setup, the OpenAPI schema is at: `http://localhost:8000/api/openapi.json`

### Downloading the Schema

**Option A: Use the URL directly**:

```sh
clientele generate -u http://localhost:8000/api/openapi.json -o my_client/
```

**Option B: Download the schema file**:

```sh
curl http://localhost:8000/api/openapi.json > openapi.json
clientele generate -f openapi.json -o my_client/
```

## Step 2: Generate the Client

### Basic Generation

Generate a function-based client:

```sh
clientele generate -u http://localhost:8000/api/openapi.json -o my_client/
```

### Class-Based Client

For an object-oriented approach:

```sh
clientele generate-class -u http://localhost:8000/api/openapi.json -o my_client/
```

### Async Client

Django Ninja supports both sync and async views. Generate an async client if needed:

```sh
clientele generate -u http://localhost:8000/api/openapi.json -o my_client/ --asyncio t
```

## Step 3: Use the Generated Client

### Function-Based Client Example

```python
from my_client import client, schemas

# Call a GET endpoint
response = client.list_users_api_users_get()

# Call a POST endpoint with data
user_data = schemas.UserIn(
    username="alice",
    email="alice@example.com"
)
response = client.create_user_api_users_post(data=user_data)

# Handle responses
match response:
    case schemas.UserOut():
        print(f"User created: {response.username}")
    case schemas.Error():
        print(f"Error: {response.message}")
```

### Async Client Example

If your Django Ninja views are async:

```python
from my_async_client import client, schemas

async def create_user():
    user_data = schemas.UserIn(
        username="alice",
        email="alice@example.com"
    )
    response = await client.create_user_api_users_post(data=user_data)
    return response
```

## Working with operation_id

You can customize operation IDs in Django Ninja for cleaner function names.

### Default Operation ID

By default, Django Ninja generates operation IDs from the function name and path:

```python
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/users")
def list_users(request):
    return []
```

This might generate: `list_users_api_users_get`

### Custom operation_id

Use the `operation_id` parameter for cleaner names:

```python
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/users", operation_id="list_users")
def get_users(request):
    return []

@api.post("/users", operation_id="create_user")
def create_user(request, user: UserIn):
    return user
```

This generates:

- `client.list_users()` - clean and simple!
- `client.create_user()` - exactly what you'd expect

## Schemas and Pydantic

Django Ninja uses Pydantic for schemas, which aligns perfectly with Clientele!

### Django Ninja Schema

```python
from ninja import Schema

class UserIn(Schema):
    username: str
    email: str
    age: int

class UserOut(Schema):
    id: int
    username: str
    email: str
    age: int
    created_at: datetime
```

### Generated Client Schemas

Clientele converts these to Pydantic models in the client:

```python
# In my_client/schemas.py
import pydantic
from datetime import datetime

class UserIn(pydantic.BaseModel):
    username: str
    email: str
    age: int

class UserOut(pydantic.BaseModel):
    id: int
    username: str
    email: str
    age: int
    created_at: datetime
```

### Usage

```python
# Create request data
user_data = schemas.UserIn(
    username="alice",
    email="alice@example.com",
    age=30
)

# Get typed response
response = client.create_user(data=user_data)
# response is typed as schemas.UserOut
print(response.id)  # Full IDE autocomplete!
```

## Authentication

### HTTP Bearer Authentication

Django Ninja supports various authentication methods. For token/bearer authentication:

```python
# Django Ninja API
from ninja.security import HttpBearer

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        # Validate token
        return token

api = NinjaAPI()

@api.get("/protected", auth=AuthBearer())
def protected_endpoint(request):
    return {"message": "authenticated"}
```

Configure the client's `config.py`:

```python
def get_bearer_token() -> str:
    """
    Provide your authentication token.
    Does not require the "Bearer" prefix.
    """
    from os import environ
    return environ.get("API_TOKEN", "your-token-here")
```

### API Key Authentication

For API key authentication:

```python
# Django Ninja API
from ninja.security import APIKeyHeader

class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"
    
    def authenticate(self, request, key):
        # Validate key
        return key

@api.get("/protected", auth=ApiKey())
def protected_endpoint(request):
    return {"message": "authenticated"}
```

Configure additional headers in `config.py`:

```python
def additional_headers() -> dict:
    """
    Add custom headers to all requests.
    """
    from os import environ
    return {
        "X-API-Key": environ.get("API_KEY", "your-api-key")
    }
```

## Regenerating the Client

When you update your Django Ninja endpoints, regenerate the client:

```sh
clientele generate -u http://localhost:8000/api/openapi.json -o my_client/ --regen t
```

### Recommended Workflow

1. Update your Django Ninja endpoints/schemas
2. Restart your Django development server
3. Regenerate the client with `--regen t`
4. Review changes with `git diff`
5. Run tests
6. Commit the updated client

## Path and Query Parameters

Django Ninja's path and query parameters work seamlessly:

### Django Ninja Endpoint

```python
from ninja import Query

@api.get("/users/{user_id}")
def get_user(request, user_id: int, include_posts: bool = Query(False)):
    return {
        "user_id": user_id,
        "include_posts": include_posts
    }
```

### Generated Client Usage

```python
# Required path parameter, optional query parameter
response = client.get_user_api_users_user_id_get(
    user_id=123,
    include_posts=True
)
```

## Response Models

Django Ninja's response models become typed schemas in the client:

### Django Ninja Endpoint

```python
class UserOut(Schema):
    id: int
    username: str
    email: str

@api.get("/users/{user_id}", response=UserOut)
def get_user(request, user_id: int):
    return UserOut(
        id=user_id,
        username="alice",
        email="alice@example.com"
    )
```

### Generated Client Usage

```python
response = client.get_user_api_users_user_id_get(user_id=123)
# response is typed as schemas.UserOut
assert isinstance(response, schemas.UserOut)
print(response.username)  # IDE knows the type!
```

## Multiple Response Types

Django Ninja supports multiple response types, which Clientele handles:

### Django Ninja Endpoint

```python
@api.post("/users", response={201: UserOut, 400: Error})
def create_user(request, user: UserIn):
    # ...
    return 201, user_data
```

### Generated Client Usage

```python
response = client.create_user_api_users_post(data=user_data)

# Use pattern matching for different responses
match response:
    case schemas.UserOut():
        print(f"Success: {response.username}")
    case schemas.Error():
        print(f"Error: {response.message}")
```

## Pagination

If you implement pagination in Django Ninja:

### Django Ninja with Pagination

```python
from typing import List

class PaginatedResponse(Schema):
    count: int
    next: str | None
    previous: str | None
    results: List[UserOut]

@api.get("/users", response=PaginatedResponse)
def list_users(request, page: int = 1, page_size: int = 20):
    # Pagination logic...
    return {
        "count": total_count,
        "next": next_url,
        "previous": prev_url,
        "results": users
    }
```

### Client Usage

```python
response = client.list_users_api_users_get(page=2, page_size=50)
print(f"Total users: {response.count}")
for user in response.results:
    print(user.username)
```

## Async Endpoints

Django Ninja supports async views. If using async:

### Django Ninja Async Endpoint

```python
@api.get("/users/{user_id}")
async def get_user(request, user_id: int):
    # Async database query...
    user = await User.objects.aget(id=user_id)
    return user
```

### Generate Async Client

```sh
clientele generate -u http://localhost:8000/api/openapi.json -o my_client/ --asyncio t
```

### Client Usage

```python
response = await client.get_user_api_users_user_id_get(user_id=123)
```

## Known Limitations

### OpenAPI Version

- **Supported**: Django Ninja generates OpenAPI 3.0.x schemas that work perfectly with Clientele
- **Works Well**: Most Django Ninja features are well-supported
- **Not Supported**: OpenAPI 2.0 schemas (Django Ninja uses 3.0+ by default)

### File Uploads

File upload endpoints may require manual customization in the generated client.

### Complex Schema Features

- Most Pydantic features work seamlessly since Django Ninja uses Pydantic
- Nested schemas are fully supported
- `oneOf`, `anyOf`, and nullable fields work correctly

## Best Practices

1. **Use custom `operation_id`** for readable function names
2. **Keep schemas separate** from view logic for clarity
3. **Regenerate regularly** when the API changes
4. **Use meaningful schema names** (UserIn, UserOut, etc.)
5. **Version your client** in git to track changes
6. **Document your endpoints** - Django Ninja includes docstrings in the schema

## Django Ninja Features in Generated Clients

### Router Support

Django Ninja routers work perfectly:

```python
from ninja import Router

users_router = Router()

@users_router.get("/", operation_id="list_users")
def list_users(request):
    return []

@users_router.post("/", operation_id="create_user")
def create_user(request, user: UserIn):
    return user

api.add_router("/users", users_router)
```

All endpoints are included in the generated client.

### Versioning

Django Ninja's versioning is reflected in the schema:

```python
api_v1 = NinjaAPI(version="1.0.0")
api_v2 = NinjaAPI(version="2.0.0")
```

Generate separate clients for each version if needed.

## Next Steps

- [Django Ninja documentation](https://django-ninja.dev/)
- [Learn about regeneration workflow](usage.md#regenerating)
- [Set up testing with respx](testing.md)
- [Understand client structure](examples.md)
