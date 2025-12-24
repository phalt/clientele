# Django Ninja Server Example

This is a working Django Ninja application that demonstrates the code examples from the [Clientele Django Ninja documentation](../../docs/framework-django-ninja.md).

## Setup

1. Install dependencies (from the root of the clientele repository):

```sh
uv sync --dev
```

2. Run migrations:

```sh
cd server_examples/django-ninja
python manage.py migrate
```

3. Run the server:

```sh
python manage.py runserver
```

The server will start at `http://localhost:8000`.

## Accessing the OpenAPI Schema

- **OpenAPI JSON**: http://localhost:8000/api/openapi.json
- **Interactive Docs**: http://localhost:8000/api/docs

## Generate a Client

From the root of the repository:

```sh
# Generate a client into the client/ directory
uv run clientele generate -u http://localhost:8000/api/openapi.json -o server_examples/django-ninja/client/
```

## API Endpoints

This example includes:

- `GET /api/users` - List users (operation_id: `list_users`)
- `POST /api/users` - Create a user (operation_id: `create_user`)
- `GET /api/users/{user_id}` - Get a user (operation_id: `get_user`)

## Code Structure

- `manage.py` - Django management script
- `example_project/` - Django project settings
- `api.py` - Django Ninja API definition with endpoints
- `client/` - Directory for generated Clientele client (initially empty)
