# 🔐 Authentication

Clientele API supports multiple authentication methods through the client configuration.

## Generated from your OpenAPI schema

When you generate a client with `clientele start-api`, the generator reads `components.securitySchemes` from the schema and adds typed credential fields to the generated `Config` class. Credentials can then be set directly, via environment variables, or via a `.env` file — and they are automatically sent as headers on every request.

| Security scheme | Generated fields | Header sent |
| --------------- | ---------------- | ----------- |
| `http` / `bearer` | `bearer_token` | `Authorization: Bearer <token>` |
| `http` / `basic` | `basic_username`, `basic_password` | `Authorization: Basic <base64 credentials>` |
| `apiKey` in `header` | `api_key` | The header named by the scheme (e.g. `X-API-Key`) |

For example, a schema with a bearer scheme generates:

```python
# config.py (generated)
class Config(clientele_api.BaseConfig):
    base_url: str = "https://api.example.com"

    # HTTP bearer authentication ("bearerAuth" in the OpenAPI spec).
    # When set, sends the "Authorization: Bearer <token>" header.
    bearer_token: str = ""
    ...
```

Which you can configure in any of the usual ways:

```python
# Direct instantiation
config = Config(bearer_token="my-secret-token")
```

```sh
# Or from the environment (or a .env file)
export BEARER_TOKEN="my-secret-token"
```

Credentials are only injected when they are set, and they never override a header you provide explicitly via the `headers` field.

Some schemes cannot be generated automatically — `oauth2`, `openIdConnect`, and API keys sent in a query parameter or cookie. The generator leaves a comment in `config.py` for each one, and `clientele validate` reports them as warnings. Configure these manually using the approaches below.

!!! note

    `config.py` is never overwritten on regeneration, so generated auth fields only appear in fresh clients. If you regenerate an existing client after the API adds auth, copy the fields in manually.

## Manual configuration

### Bearer Token

Bearer token authentication can be configured by adding an `Authorization` header.

**Configuration:**

```python
# config.py
from clientele import api as clientele_api

class Config(clientele_api.BaseConfig):
    ...
    headers = {"Authorization": "MY_SECRET_TOKEN"}
    ...
```

### HTTP Basic Authentication

Basic authentication can be configured using [httpx.Auth](https://www.python-httpx.org/advanced/authentication/#basic-authentication):

**Configuration:**

```python
# config.py
import httpx
from clientele import api as clientele_api
from my_settings import AUTH_TOKEN

class Config(clientele_api.BaseConfig):
    ...
    auth = httpx.BasicAuth("username", "password")
    ...
```
