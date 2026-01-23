# 🥷 Using Clientele with Django Ninja

This guide shows you how to scaffold a Python client for a Django Ninja API using Clientele.

> **💡 Working Example**: See a real Django Ninja application with code examples from this guide in [`server_examples/django_ninja/`](https://github.com/phalt/clientele/tree/main/server_examples/django_ninja)

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

You can either:

**Option A: Use the URL directly** (if the API is accessible):

```sh
clientele start-api -u http://localhost:8000/api/openapi.json -o my_client/
```

**Option B: Download the schema file first**:

```sh
curl http://localhost:8000/api/openapi.json > openapi.json
clientele start-api -f openapi.json -o my_client/
```

## Step 2: Scaffold the Client

```sh
clientele start-api -u http://localhost:8000/api/openapi.json -o my_client/
```

### Async Client

Django Ninja supports both sync and async views. If you want an async client:

```sh
clientele start-api -u http://localhost:8000/api/openapi.json -o my_client/ --asyncio
```

## Step 3: Use the scaffolded Client

### Usage Example

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

### Async usage Example

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

Django Ninja generates `operation_id` values for each endpoint, which Clientele uses to create function names.

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

You can customize the operation ID in Django Ninja to get cleaner function names:

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

- `client.list_users()` instead of `client.list_users_api_users_get()`
- `client.create_user()` instead of `client.create_user_api_users_post()`

## Authentication

See [api authentication](api-authentication.md).

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
print(response.id)
```

## Path and Query Parameters

Django Ninja's path and query parameters are automatically converted to function arguments:

**Django Ninja Endpoint**

```python
from ninja import Query

@api.get("/users/{user_id}")
def get_user(request, user_id: int, include_posts: bool = Query(False)):
    return {
        "user_id": user_id,
        "include_posts": include_posts
    }
```

**Client Usage**

```python
# Required path parameter, optional query parameter
response = client.get_user_api_users_user_id_get(
    user_id=123,
    include_posts=True
)
```

## Response Models

Django Ninja's response models become Pydantic schemas in the client:

**Django Ninja Endpoint**

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

**Generated Client Usage**

```python
response = client.get_user_api_users_user_id_get(user_id=123)
# response is typed as schemas.UserOut
print(response.username)
```

## Best Practices

1. **Use custom `operation_id`** values for cleaner function names
2. **Keep schemas in sync** by regenerating after API changes
3. **Version your generated client** in git to track changes
4. **Test thoroughly** after regenerating
5. **Document your endpoints** - Django Ninja includes docstrings in the schema

## Next Steps

- [Configure authentication](api-authentication.md)
- [Set up testing](api-testing.md)
