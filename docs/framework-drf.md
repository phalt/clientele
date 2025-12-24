# Using Clientele with Django REST Framework

This guide shows you how to generate a Python client for a Django REST Framework (DRF) API using Clientele and **drf-spectacular**.

> **💡 Working Example**: See a real Django REST Framework application with code examples from this guide in [`server_examples/django-rest-framework/`](https://github.com/phalt/clientele/tree/main/server_examples/django-rest-framework)

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

### Download the Schema

**Option A: Use the URL directly**:

```sh
clientele generate -u http://localhost:8000/api/schema/ -o my_client/
```

**Option B: Download the schema file**:

```sh
curl http://localhost:8000/api/schema/ > openapi.json
clientele generate -f openapi.json -o my_client/
```

**Option C: Generate schema file with Django management command**:

```sh
python manage.py spectacular --file openapi.json
clientele generate -f openapi.json -o my_client/
```

## Step 3: Generate the Client

### Basic Generation

Generate a function-based client:

```sh
clientele generate -u http://localhost:8000/api/schema/ -o my_client/
```

### Class-Based Client

For an object-oriented approach:

```sh
clientele generate-class -u http://localhost:8000/api/schema/ -o my_client/
```

### Async Client

Generate an async client (note: DRF itself is synchronous, but the client can be async):

```sh
clientele generate -u http://localhost:8000/api/schema/ -o my_client/ --asyncio t
```

## Step 4: Use the Generated Client

### Function-Based Client Example

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

### Token Authentication

If your DRF API uses token authentication:

```python
# Django settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authtoken.models.TokenAuthentication',
    ],
}
```

Configure in the client's `config.py`:

```python
def get_bearer_token() -> str:
    """
    Provide your DRF auth token.
    """
    from os import environ
    return environ.get("DRF_AUTH_TOKEN", "your-token-here")
```

### Session Authentication

For session-based auth, you may need to handle cookie management manually in the client's `config.py` using additional headers.

### JWT Authentication

If using JWT (e.g., with djangorestframework-simplejwt):

```python
def get_bearer_token() -> str:
    """
    Provide your JWT access token.
    """
    from os import environ
    return environ.get("JWT_ACCESS_TOKEN", "your-jwt-token")
```

## Regenerating the Client

When your DRF API changes, regenerate the client:

```sh
clientele generate -u http://localhost:8000/api/schema/ -o my_client/ --regen t
```

### Recommended Workflow

1. Update your DRF serializers/views
2. Run migrations if needed
3. Regenerate the schema: `python manage.py spectacular --file openapi.json`
4. Regenerate the client: `clientele generate -f openapi.json -o my_client/ --regen t`
5. Review changes: `git diff`
6. Test the updated client
7. Commit changes

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
assert isinstance(response, schemas.User)
print(response.username)  # Full IDE support
```

## ViewSets and Routers

DRF ViewSets with routers automatically generate appropriate endpoints:

### DRF ViewSet

```python
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
```

### Router Configuration

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet)
```

This generates endpoints like:

- `GET /users/` → `client.list_users()`
- `POST /users/` → `client.create_user(data=...)`
- `GET /users/{id}/` → `client.get_user(id=...)`
- `PUT /users/{id}/` → `client.update_user(id=..., data=...)`
- `DELETE /users/{id}/` → `client.delete_user(id=...)`

## Pagination

DRF pagination is reflected in the schema and client:

### DRF Pagination Setup

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}
```

### Generated Schema

The response will include pagination fields:

```python
response = client.list_users_api_users_get(page=2)
# Response has structure like:
# {
#   "count": 250,
#   "next": "http://...",
#   "previous": "http://...",
#   "results": [...]
# }
```

## Filtering and Query Parameters

Query parameters are automatically converted to function arguments:

### DRF View with Filtering

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = ['is_active', 'username']
```

### Client Usage

```python
# Query parameters become function arguments
response = client.list_users_api_users_get(
    is_active=True,
    username="alice"
)
```

## Known Limitations

### OpenAPI Version

- **Supported**: drf-spectacular generates OpenAPI 3.0 schemas that work perfectly with Clientele
- **Partial Support**: Some complex DRF features may need schema customization
- **Not Supported**: DRF's older CoreAPI schema format is not supported - use drf-spectacular

### Complex Serializers

- Most DRF serializer features work out of the box
- Nested serializers are fully supported
- SerializerMethodField may require manual schema hints with `@extend_schema_field`

### File Uploads

File upload endpoints may require manual customization in the generated client.

## Best Practices

1. **Use `@extend_schema`** to provide clear operation IDs and response types
2. **Document your serializers** - drf-spectacular uses docstrings in schema generation
3. **Regenerate regularly** to keep client in sync with API changes
4. **Use `extend_schema_field`** for SerializerMethodFields to ensure proper typing
5. **Version your generated client** in git

## Helpful drf-spectacular Features

### Documenting Responses

```python
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Invalid request'),
        404: OpenApiResponse(description='User not found'),
    }
)
@api_view(['GET'])
def get_user(request, user_id):
    # ...
```

### Documenting Request Bodies

```python
@extend_schema(
    request=UserSerializer,
    responses={201: UserSerializer}
)
@api_view(['POST'])
def create_user(request):
    # ...
```

## Next Steps

- [drf-spectacular documentation](https://drf-spectacular.readthedocs.io/)
- [Learn about regeneration workflow](usage.md#regenerating)
- [Set up testing with respx](testing.md)
- [Understand client structure](examples.md)
