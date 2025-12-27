# ⚙️ Client Configuration

Both function-based and class-based clients support extensive configuration options to customize HTTP client behavior using [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

## Configuration Options

All generated clients support the following configuration options:

### Authentication

- `api_base_url`: Base URL for the API (default: `"http://localhost"`)
- `user_key`: Username for HTTP Basic authentication (default: `"user"`)
- `pass_key`: Password for HTTP Basic authentication (default: `"password"`)
- `bearer_token`: Token for HTTP Bearer authentication (default: `"token"`)
- `additional_headers`: Additional headers to include in all requests (default: `{}`)

!!! note "Optional Authentication"
    
    For clients with HTTP Basic authentication, if both `user_key` and `pass_key` are empty or `None`, authentication will be disabled. This allows you to optionally disable authentication when needed.

### HTTP Behavior

- `timeout`: Request timeout in seconds (default: `5.0`)
- `follow_redirects`: Whether to automatically follow HTTP redirects (default: `False`)
- `max_redirects`: Maximum number of redirects to follow (default: `20`)

### Security

- `verify_ssl`: Whether to verify SSL certificates (default: `True`)

### Performance

- `http2`: Whether to enable HTTP/2 support (default: `False`)
- `limits`: Connection pool limits via `httpx.Limits` (default: `None`)
- `transport`: Custom transport via `httpx.HTTPTransport` or `httpx.AsyncHTTPTransport` (default: `None`)

## Function-Based Client Configuration

Function-based clients use a `Config` object powered by [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) that automatically loads values from environment variables:

```python
# In your generated client's config.py file
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    api_base_url: str = "http://localhost"
    bearer_token: str = "token"
    timeout: float = 5.0
    follow_redirects: bool = False
    verify_ssl: bool = True
    http2: bool = False
    # ... other configuration options

# Create a singleton instance
config = Config()
```

### Setting Values

There are three ways to configure function-based clients:

#### 1. Environment Variables (Recommended for Production)

```bash
export API_BASE_URL="https://api.production.com"
export BEARER_TOKEN="your-secret-token"
export TIMEOUT=30.0
export HTTP2=true
export FOLLOW_REDIRECTS=true
```

#### 2. Direct Instantiation (For Testing/Development)

```python
# Modify the default values in config.py
from my_client import config

config.config = config.Config(
    api_base_url="https://api.example.com",
    bearer_token="my-token",
    timeout=30.0,
    http2=True
)
```

#### 3. .env File (Requires python-dotenv)

```
# .env file in your project root
API_BASE_URL=https://api.example.com
BEARER_TOKEN=my-token
TIMEOUT=30.0
VERIFY_SSL=false
```

#### 4. Custom Environment Variable Names

If the default environment variable names are too generic for your use case, you can customize them using pydantic's `Field` with the `validation_alias` parameter:

```python
# In your generated client's config.py file
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    api_base_url: str = Field(
        default="http://localhost",
        validation_alias="MY_APP_API_BASE_URL"
    )
    bearer_token: str = Field(
        default="token",
        validation_alias="MY_APP_BEARER_TOKEN"
    )
    timeout: float = Field(
        default=5.0,
        validation_alias="MY_APP_TIMEOUT"
    )
    # ... other configuration options

config = Config()
```

Now you can use custom environment variable names:

```bash
export MY_APP_API_BASE_URL="https://api.production.com"
export MY_APP_BEARER_TOKEN="your-secret-token"
export MY_APP_TIMEOUT=30.0
```

This is particularly useful when:

- You have multiple API clients in the same application
- You want to avoid naming conflicts with other environment variables
- Your organization has specific naming conventions for environment variables

## Class-Based Client Configuration

Class-based clients use the same `Config` class with the same pydantic-settings support. Pass configuration options when creating the client:

```python
from my_client.client import Client
from my_client import config

# From environment variables
cfg = config.Config()  # Automatically loads from env vars
client = Client(config=cfg)

# Or with explicit values
custom_config = config.Config(
    api_base_url="https://api.production.com",
    bearer_token="your-api-token",
    timeout=30.0,
    follow_redirects=True,
    verify_ssl=True,
    http2=True,
    max_redirects=10,
)

client = Client(config=custom_config)
```

## Configuration Examples

### Increase Timeout for Slow APIs

```python
# Function-based client (via environment variable)
export TIMEOUT=60.0

# Function-based client (via code)
from my_client import config
config.config = config.Config(timeout=60.0)

# Class-based client
from my_client import config
cfg = config.Config(timeout=60.0)
client = Client(config=cfg)
```

### Enable HTTP/2 for Better Performance

```python
# Function-based client (via environment variable)
export HTTP2=true

# Function-based client (via code)
from my_client import config
config.config = config.Config(http2=True)

# Class-based client
from my_client import config
cfg = config.Config(http2=True)
client = Client(config=cfg)
```

### Development Environment (Disable SSL Verification)

!!! warning
    
    Only disable SSL verification in development environments. Never disable it in production!

```python
# Function-based client (via environment variable)
export VERIFY_SSL=false

# Function-based client (via code)
from my_client import config
config.config = config.Config(verify_ssl=False)

# Class-based client
from my_client import config
cfg = config.Config(verify_ssl=False)
client = Client(config=cfg)
```

### Follow Redirects

```python
# Function-based client (via environment variables)
export FOLLOW_REDIRECTS=true
export MAX_REDIRECTS=5

# Function-based client (via code)
from my_client import config
config.config = config.Config(follow_redirects=True, max_redirects=5)

# Class-based client
from my_client import config
cfg = config.Config(follow_redirects=True, max_redirects=5)
client = Client(config=cfg)
```

### Configure Connection Pool Limits

Control connection pooling behavior with `httpx.Limits`:

```python
import httpx

# Function-based client
# Note: Complex objects like httpx.Limits must be set in code, not env vars
from my_client import config
config.config = config.Config(
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=20,
        keepalive_expiry=5.0
    )
)

# Class-based client
from my_client import config
cfg = config.Config(
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=20
    )
)
client = Client(config=cfg)
```

### Configure Custom Transport

Customize low-level HTTP behavior with a custom transport:

```python
import httpx

# Function-based client (sync)
# Note: Complex objects like httpx.HTTPTransport must be set in code
from my_client import config
config.config = config.Config(
    transport=httpx.HTTPTransport(
        retries=3,
        local_address="0.0.0.0"
    )
)

# Function-based client (async)
from my_async_client import config
config.config = config.Config(
    transport=httpx.AsyncHTTPTransport(retries=3)
)

# Class-based client (sync)
from my_client import config
cfg = config.Config(
    transport=httpx.HTTPTransport(retries=3)
)
client = Client(config=cfg)

# Class-based client (async)
from my_client import config
cfg = config.Config(
    transport=httpx.AsyncHTTPTransport(retries=3)
)
client = AsyncClient(config=cfg)
```

## Advanced Configuration

### Mixing Environment Variables and Code

You can load base configuration from environment variables and override specific values in code:

```python
import httpx
from my_client import config

# Loads API_BASE_URL, BEARER_TOKEN, etc. from environment
# But overrides timeout and adds custom limits
cfg = config.Config(
    timeout=60.0,  # Override env var if present
    limits=httpx.Limits(max_connections=50)  # Can't be set via env
)
client = Client(config=cfg)
```

### Multiple Clients with Different Configurations

Class-based clients make it easy to create multiple clients with different configurations:

```python
from my_client.client import Client
from my_client import config

# Production client
prod_config = config.Config(
    api_base_url="https://api.production.com",
    bearer_token="prod-token",
    verify_ssl=True
)
prod_client = Client(config=prod_config)

# Staging client
staging_config = config.Config(
    api_base_url="https://api.staging.com",
    bearer_token="staging-token",
    verify_ssl=False
)
staging_client = Client(config=staging_config)

# Use both clients in the same application
prod_response = prod_client.get_user(user_id=123)
staging_response = staging_client.get_user(user_id=123)
```
