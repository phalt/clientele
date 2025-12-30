# 🗺️ Tour of a Generated Client

When you generate a client with Clientele, it creates several files that work together to provide a complete HTTP API client. 

This guide explains each file's purpose and which ones you'll interact with as a developer.

## What gets generated?

Running `clientele generate` creates this file structure:

```sh
my_client/
    MANIFEST.md
    client.py
    config.py
    http.py
    schemas.py
```

Let's explore each file.

## MANIFEST.md

**Purpose:** Metadata and regeneration tracking

The `MANIFEST.md` file contains metadata about your generated client:

- The Clientele version used to generate it
- The OpenAPI version of the source schema
- The API version
- The exact command to regenerate the client

**Should you edit it?** No, this file is regenerated each time.

**Example:**

```markdown
# Manifest

Generated with https://github.com/phalt/clientele

API VERSION: 1.0.0
OPENAPI VERSION: 3.0.2
CLIENTELE VERSION: 1.2.0

Regenerate using this command:

clientele generate -f openapi.json -o my_client/ --regen t
```

This file is particularly useful when you need to regenerate the client after API changes. See [Regenerating](regeneration.md) for details.

## client.py

**Purpose:** API endpoint functions or class

This is the main file you'll import and use. 

It contains a function (or method if using `generate-class`) for each API endpoint.

**Should you edit it?** No, this file is regenerated each time. Your usage code should import from it, not modify it.

**Function-based client example:**

```py title="my_client/client.py"
from my_client import http, schemas


def get_user(user_id: int) -> schemas.User:
    """Get user by ID"""
    response = http.get(url=f"/users/{user_id}")
    return http.handle_response(get_user, response)


def create_user(data: schemas.CreateUserRequest) -> schemas.User:
    """Create a new user"""
    response = http.post(url="/users", data=data.model_dump())
    return http.handle_response(create_user, response)
```

**Class-based client example:**

```py title="my_client/client.py"
from my_client import config, http, schemas


class Client:
    """API Client for making requests"""
    
    def __init__(self, config: config.Config | None = None):
        self.config = config or config.Config()
        self._http_client = http.HTTPClient(self.config)
    
    def get_user(self, user_id: int) -> schemas.User:
        """Get user by ID"""
        response = self._http_client.get(url=f"/users/{user_id}")
        return http.handle_response(self.get_user, response)
```

Each function/method is fully typed and includes:

- Type hints for all parameters
- Return type annotations with all possible response types
- The endpoint's description as a docstring

See the [Usage](usage.md) guide for more on function-based vs class-based clients.

## schemas.py

**Purpose:** Pydantic models for requests and responses

The `schemas.py` file contains Pydantic models for all request bodies, response bodies, and enums defined in your OpenAPI schema.

**Should you edit it?** No, this file is regenerated each time. You use these schemas in your code but don't modify them.

**Example:**

```py title="my_client/schemas.py"
import pydantic
from enum import Enum


class User(pydantic.BaseModel):
    id: int
    username: str
    email: str


class CreateUserRequest(pydantic.BaseModel):
    username: str
    email: str
    password: str


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"
```

These schemas provide:

- **Type safety:** Your IDE can autocomplete fields and catch type errors
- **Validation:** Pydantic validates data at runtime
- **Serialisation:** Easy conversion to/from JSON

**Usage example:**

```py
from my_client import client, schemas

# Create request data with validation
user_data = schemas.CreateUserRequest(
    username="alice",
    email="alice@example.com",
    password="secret123"
)

# Get a validated response
user = client.create_user(data=user_data)
assert isinstance(user, schemas.User)
```

## config.py

**Purpose:** Client configuration and settings

The `config.py` file contains a `Config` class that manages all client settings like API URL, authentication, timeouts, and HTTP behavior.

**Should you edit it?** Yes! This is the one file that **won't** be overwritten when you regenerate. Customise it to suit your needs.

**Example:**

```py title="my_client/config.py"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
    
    api_base_url: str = "http://localhost"
    bearer_token: str = "token"
    timeout: float = 5.0
    verify_ssl: bool = True
    # ... more settings


config = Config()
```

The `Config` class uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load values from environment variables or `.env` files.

For detailed configuration options and examples, see the [Configuration Guide](configuration.md).

## http.py

**Purpose:** HTTP client implementation and response handling

This file contains the low-level HTTP logic: making requests with `httpx`, handling responses, parsing errors, and managing the response-to-schema mapping.

**Should you edit it?** No. This file is regenerated each time and is **not intended to be used by developers**. You are welcome to read it and understand how it works. There isn't any magic.

**What's inside:**

- `get()`, `post()`, `put()`, `delete()`, `patch()` functions for making HTTP requests
- `handle_response()` for converting HTTP responses to Pydantic models
- `APIException` class for unexpected response codes
- Response code mapping for each endpoint
- HTTP client initialisation with your config settings

**You only need to interact with this file indirectly** when handling API exceptions. See the [Exception Handling](exceptions.md) guide for details.

## Summary

Here's a quick reference of what to do with each file:

| File | Purpose | Edit? | Import? |
|------|---------|-------|---------|
| `MANIFEST.md` | Metadata and regeneration info | ❌ No | ❌ No |
| `client.py` | API functions/class | ❌ No | ✅ Yes |
| `schemas.py` | Pydantic models | ❌ No | ✅ Yes |
| `config.py` | Configuration | ✅ Yes | ✅ Yes |
| `http.py` | HTTP implementation | ❌ No | ⚠️ Rarely |

For more information:

- [Usage & CLI](usage.md) - How to generate clients
- [Configuration](configuration.md) - Configure the client
- [Authentication](authentication.md) - Set up authentication
- [Exception Handling](exceptions.md) - Handle API exceptions
- [Testing](testing.md) - Write tests for your client
