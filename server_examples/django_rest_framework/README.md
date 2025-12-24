# Django REST Framework Server Example

This is a working Django REST Framework application with drf-spectacular that demonstrates the code examples from the [Clientele DRF documentation](../../docs/framework-drf.md).

## Setup

1. Install dependencies (from the root of the clientele repository):

```sh
uv sync --dev
```

2. Run migrations:

```sh
cd server_examples/django-rest-framework
uv run python manage.py migrate
```

3. Run the server:

```sh
uv run python manage.py runserver
```

The server will start at `http://localhost:8000`.

## Accessing the OpenAPI Schema

- **OpenAPI Schema**: http://localhost:8000/api/schema/
- **Interactive Docs**: http://localhost:8000/api/docs/

## Generate a Client

From the root of the repository:

```sh
# Generate a client into the client/ directory
uv run clientele generate -f server_examples/django_rest_framework/openapi.yaml -o server_examples/django_rest_framework/client/
```

## API Endpoints

This example includes:

- `GET /api/users/` - List users (operation_id: `list_users`)
- `POST /api/users/` - Create a user (operation_id: `create_user`)
- `GET /api/users/{id}/` - Retrieve a user (operation_id: `get_user`)

## Code Structure

- `manage.py` - Django management script
- `example_project/` - Django project settings
- `users/` - Users app with ViewSet and serializers
- `client/` - Directory for generated Clientele client (initially empty)
