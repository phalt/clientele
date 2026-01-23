# 🦄 Using Clientele with Django REST Framework

This guide shows you how to scaffold a Python client for a Django REST Framework (DRF) API using Clientele and **drf-spectacular**.

> **💡 Working Example**: See a real Django REST Framework application with code examples from this guide in [`server_examples/django_rest_framework/`](https://github.com/phalt/clientele/tree/main/server_examples/django_rest_framework)

## Prerequisites

- A Django REST Framework application
- [drf-spectacular](https://github.com/tfranzel/drf-spectacular) installed and configured

## Why drf-spectacular?

Django REST Framework doesn't include built-in OpenAPI schema generation. **drf-spectacular** is the recommended solution for generating OpenAPI 3.0 schemas from DRF applications. It's actively maintained and provides excellent OpenAPI support.

## Step 1: Install and Configure drf-spectacular

If you haven't already set up drf-spectacular, follow these steps:

### Install drf-spectacular

```sh
pip install drf-spectacular
```

### Configure Django Settings

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'drf_spectacular',
    # ...
]

REST_FRAMEWORK = {
    # ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'Your API description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

### Add URL Patterns

In your `urls.py`:

```python
from drf_spectacular.views import SpectacularAPIView
from django.urls import path

urlpatterns = [
    # ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]
```

## Step 2: Get Your OpenAPI Schema

After configuring drf-spectacular, your OpenAPI schema is available at:

```sh
http://your-api-domain/api/schema/
```

For local development:

```sh
http://localhost:8000/api/schema/
```

### Downloading the Schema

You can either:

**Option A: Use the URL directly** (if the API is accessible):

```sh
clientele start-api -u http://localhost:8000/api/schema/ -o my_client/
```

**Option B: Download the schema file first**:

```sh
curl http://localhost:8000/api/schema/ > openapi.json
clientele start-api -f openapi.json -o my_client/
```

**Option C: Generate schema file with Django management command**:

```sh
python manage.py spectacular --file openapi.json
clientele start-api -f openapi.json -o my_client/
```

## Step 3: Scaffold the Client

```sh
clientele start-api -u http://localhost:8000/api/schema/ -o my_client/
```

### Async Client

If you want an async client (note: DRF itself is synchronous, but the client can be async):

```sh
clientele start-api -u http://localhost:8000/api/schema/ -o my_client/ --asyncio
```

## Step 4: Use the scaffolded Client

### Usage Example

```python
from my_client import client, schemas

# List resources
response = client.list_users_api_users_get()

# Create a resource
user_data = schemas.UserRequest(
    username="alice",
    email="alice@example.com"
)
response = client.create_user_api_users_post(data=user_data)

# Handle responses
match response:
    case schemas.User():
        print(f"User created: {response.username}")
    case schemas.ValidationError():
        print(f"Validation failed: {response.detail}")
```

### Async usage Example

```python
from my_async_client import client, schemas

async def create_user():
    user_data = schemas.UserRequest(
        username="alice",
        email="alice@example.com"
    )
    response = await client.create_user_api_users_post(data=user_data)
    return response
```

## Improving operationId in DRF

By default, drf-spectacular generates operation IDs from view names and paths. You can customize them for cleaner function names.

### Using extend_schema Decorator

```python
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @extend_schema(operation_id="list_users")
    def list(self, request):
        return super().list(request)
    
    @extend_schema(operation_id="create_user")
    def create(self, request):
        return super().create(request)
    
    @extend_schema(operation_id="get_user")
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)
```

This generates:

- `client.list_users()` instead of a generic operation ID
- `client.create_user()` instead of verbose auto-generated names
- `client.get_user()` for clean, readable function names

### For Function-Based Views

```python
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view

@extend_schema(
    operation_id="get_user_stats",
    responses={200: UserStatsSerializer}
)
@api_view(['GET'])
def user_stats(request, user_id):
    # ...
    return Response(data)
```

## Authentication

See [api authentication](api-authentication.md).

## Serializers and Schemas

DRF serializers become Pydantic models in the generated client:

### DRF Serializer

```python
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active']
```

### Generated Pydantic Schema

```python
# In my_client/schemas.py
import pydantic

class User(pydantic.BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
```

### Usage

```python
# The client returns properly typed responses
response = client.get_user_api_users_id_get(id=123)
# response is typed as schemas.User
print(response.username)
```

## Path and Query Parameters

Query parameters are automatically converted to function arguments:

**DRF View with Filtering**

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['is_active', 'username']
```

**Client Usage**

```python
# Query parameters become function arguments
response = client.list_users_api_users_get(
    is_active=True,
    username="alice"
)
```

## Response Models

DRF's serializers become response models in the client:

**DRF ViewSet**

```python
from rest_framework import serializers, viewsets

class User(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email']

class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = User
```

**Generated Client Usage**

```python
response = client.get_user_api_users_id_get(id=123)
# response is typed as schemas.User
print(response.username)
```

## Best Practices

1. **Use `@extend_schema`** to provide clear operation IDs and response types
2. **Keep schemas in sync** by regenerating after API changes
3. **Version your generated client** in git to track changes
4. **Test thoroughly** after regenerating
5. **Document your serializers** - drf-spectacular uses docstrings in schema generation

## Next Steps

- [Configure authentication](api-authentication.md)
- [Set up testing](api-testing.md)
