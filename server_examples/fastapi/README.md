# FastAPI Server Example

This is a working FastAPI application that demonstrates the code examples from the [Clientele FastAPI documentation](../../docs/framework-fastapi.md).

## Setup

1. Install dependencies (from the root of the clientele repository):

```sh
uv sync --dev
```

2. Run the server:

```sh
cd server_examples/fastapi
uv run fastapi dev main.py
```

The server will start at `http://localhost:8000`.

## Accessing the OpenAPI Schema

- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Interactive Docs**: http://localhost:8000/docs

## Explore the client

From the root of the repository:

```sh
# Run clientele explore to use the client
uv run clientele explore -c server_examples/fastapi/client/


═══════════════════════════════════════════════════════════
  Clientele Interactive API Explorer v1.0.0
═══════════════════════════════════════════════════════════

Type /help or ? for commands, /exit or Ctrl+D to quit
Type /list to see available operations

Press TAB for autocomplete

>>> get_user(user_id=1)
✓ Success in 0.01s
{ 
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
>>>
```

## API Endpoints

This example includes:

- `GET /users` - List all users (operation_id: `list_users`)
- `POST /users` - Create a new user (operation_id: `create_user`)
- `GET /users/{user_id}` - Get a specific user (operation_id: `get_user`)

## Code Structure

- `main.py` - The FastAPI application with endpoints
- `client/` - Directory for generated Clientele client (initially empty)
