# Authentication

Clientele supports multiple authentication methods through the client configuration.

## Supported Authentication Types

### Bearer Token

Bearer token authentication adds an `Authorization` header with a token to all requests.

**Configuration:**

```python
from my_client import config

# Via code
cfg = config.Config(bearer_token="your-secret-token")

# Via environment variable
export BEARER_TOKEN="your-secret-token"
```

**What happens under the hood:**

Clientele sets the `Authorization` header on every request:

```
Authorization: Bearer your-secret-token
```

### HTTP Basic Authentication

Basic authentication uses a username and password.

**Configuration:**

```python
from my_client import config

# Via code
cfg = config.Config(
    user_key="username",
    pass_key="password"
)

# Via environment variables
export USER_KEY="username"
export PASS_KEY="password"
```

**What happens under the hood:**

Clientele encodes the credentials and sets the `Authorization` header:

```
Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
```

**Optional authentication:**

If both `user_key` and `pass_key` are empty or `None`, authentication is disabled:

```python
cfg = config.Config(user_key="", pass_key="")  # No auth
```

### Custom Headers

For APIs that use custom authentication headers (like API keys), use `additional_headers`:

**Configuration:**

```python
from my_client import config

cfg = config.Config(
    additional_headers={
        "X-API-Key": "your-api-key",
        "X-Client-ID": "your-client-id"
    }
)

# Via environment (requires custom config.py setup)
export ADDITIONAL_HEADERS='{"X-API-Key": "your-api-key"}'
```

**What happens under the hood:**

These headers are added to every request alongside any authentication headers.

## Multiple Authentication Methods

Some APIs support multiple authentication methods. Configure all applicable options:

```python
cfg = config.Config(
    bearer_token="fallback-token",
    additional_headers={
        "X-API-Key": "preferred-key"
    }
)
```

Both headers will be sent with each request.

## Environment-Specific Configuration

### Development

```python
# config.py
class Config(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    bearer_token: str = "dev-token-12345"
```

### Production

```bash
# .env file
API_BASE_URL=https://api.production.com
BEARER_TOKEN=prod-***-secret-token-***
```

```python
# Code stays the same
from my_client import config
client = Client(config=config.config)  # Loads from environment
```

## Class-Based Clients

For class-based clients, pass the configured object when creating the client:

```python
from my_client.client import Client
from my_client import config

# Custom config
cfg = config.Config(
    api_base_url="https://api.example.com",
    bearer_token="secret-token"
)

client = Client(config=cfg)
```

## Function-Based Clients

For function-based clients, update the singleton config:

```python
from my_client import config

# Update the global config
config.config = config.Config(
    api_base_url="https://api.example.com",
    bearer_token="secret-token"
)

# All function calls now use this config
from my_client import client
response = client.get_user(user_id=123)
```

## Debugging Authentication

If you're getting authentication errors:

1. **Check the headers** being sent:

```python
from my_client import http

# The headers are stored in http.client_headers
print(http.client_headers)
```

2. **Verify the token format** matches what the API expects
3. **Test manually** with curl to confirm the authentication works:

```bash
curl -H "Authorization: Bearer your-token" https://api.example.com/endpoint
```

## See Also

- [Configuration Guide](configuration.md) - Full list of configuration options
- [Exception Handling](exceptions.md) - Handle authentication errors
