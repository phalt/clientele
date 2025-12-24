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
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`.

## Accessing the OpenAPI Schema

- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Interactive Docs**: http://localhost:8000/docs

## Generate a Client

From the root of the repository:

```sh
# Generate a client into the client/ directory
uv run clientele generate -u http://localhost:8000/openapi.json -o server_examples/fastapi/client/
```

## API Endpoints

This example includes:

- `GET /users` - List all users (operation_id: `list_users`)
- `POST /users` - Create a new user (operation_id: `create_user`)
- `GET /users/{user_id}` - Get a specific user (operation_id: `get_user`)

## Code Structure

- `main.py` - The FastAPI application with endpoints
- `client/` - Directory for generated Clientele client (initially empty)
