
# 📝 Use Clientele

!!! note

    You can type `clientele COMMAND --help` at anytime to see explicit information about the available arguments.

## Client Types

Clientele offers three types of client generators:

1. **`generate`** - Standard function-based client (recommended for most use cases)
2. **`generate-class`** - Class-based client with methods
3. **`generate-basic`** - Basic file structure with no generated code

## `generate`

Generate a Python HTTP Client from an OpenAPI Schema.

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generated client.

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

!!! note

    The example above uses one of our test schemas, and will work if you copy/paste it!

### From a file

Alternatively you can provide a local file using the `-f` or `--file` argument.

```sh
clientele generate -f path/to/file.json -o my_client/
```

### Async.io

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio t` to your command.

```sh
clientele generate -f path/to/file.json -o my_client/ --asyncio t
```

## `generate-class`

Generate a class-based Python HTTP Client from an OpenAPI Schema. This generator creates a `Client` class with methods for each API endpoint.

### Usage

The `generate-class` command accepts the same arguments as `generate`:

```sh
clientele generate-class -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### Example Usage

With a class-based client, you instantiate the `Client` class and call methods:

```python
from my_client.client import Client
from my_client import schemas

# Create a client instance with default configuration
client = Client()

# Call API methods
data = schemas.RequestDataRequest(my_input="test")
response = client.request_data_request_data_post(data=data)

# Handle responses
match response:
    case schemas.RequestDataResponse():
        print(f"Success: {response}")
    case schemas.ValidationError():
        print(f"Validation error: {response}")
```

### Dynamic Configuration

Class-based clients support dynamic configuration, allowing you to create multiple clients with different settings:

```python
from my_client.client import Client
from my_client import config

# Create a client with custom configuration
custom_config = config.Config(
    api_base_url="https://api.example.com",
    bearer_token="my-auth-token",
    additional_headers={"X-Custom-Header": "value"}
)
client = Client(config=custom_config)

# Create multiple clients with different configurations
prod_config = config.Config(
    api_base_url="https://api.production.com",
    bearer_token="prod-token"
)
dev_config = config.Config(
    api_base_url="https://api.development.com",
    bearer_token="dev-token"
)

prod_client = Client(config=prod_config)
dev_client = Client(config=dev_config)

# Each client uses its own configuration
prod_response = prod_client.get_data()
dev_response = dev_client.get_data()
```

The `Config` class supports the following parameters:

- `api_base_url`: Base URL for the API (default: `"http://localhost"`)
- `additional_headers`: Additional headers to include in all requests (default: `{}`)
- `user_key`: Username for HTTP Basic authentication (default: `"user"`)
- `pass_key`: Password for HTTP Basic authentication (default: `"password"`)
- `bearer_token`: Token for HTTP Bearer authentication (default: `"token"`)
- `timeout`: Request timeout in seconds (default: `5.0`)
- `follow_redirects`: Whether to automatically follow HTTP redirects (default: `False`)
- `verify_ssl`: Whether to verify SSL certificates (default: `True`)
- `http2`: Whether to enable HTTP/2 support (default: `False`)
- `max_redirects`: Maximum number of redirects to follow (default: `20`)

This makes it easy to:
- Switch between different API environments (dev, staging, production)
- Use different authentication tokens for different users or sessions
- Add custom headers per client instance
- Configure timeout and retry behavior
- Control SSL verification for development environments
- Enable HTTP/2 for improved performance
- Test your code with mock configurations

### Async Class-Based Client

You can generate an async class-based client as well:

```sh
clientele generate-class -f path/to/file.json -o my_client/ --asyncio t
```

Then use it with async/await:

```python
from my_async_client.client import Client
from my_async_client import config

# With default configuration
client = Client()
response = await client.simple_request_simple_request_get()

# With custom configuration
custom_config = config.Config(api_base_url="https://api.example.com")
client = Client(config=custom_config)
response = await client.simple_request_simple_request_get()
```

### When to Use Class-Based Clients

Use class-based clients when:

- You prefer object-oriented programming style
- You want to easily mock the client for testing
- You need to maintain state or configuration in the client instance
- You want to subclass and extend the client behavior
- **You need dynamic configuration or multiple clients with different settings**

Use function-based clients (`generate`) when:

- You prefer functional programming style
- You want the simplest possible client with no boilerplate
- You don't need to maintain state between requests
- You only need a single static configuration

## Client Configuration

Both function-based and class-based clients support extensive configuration options to customize HTTP client behavior.

### Configuration Options

All generated clients support the following configuration options:

#### Authentication
- `api_base_url`: Base URL for the API (default: `"http://localhost"`)
- `user_key`: Username for HTTP Basic authentication (default: `"user"`)
- `pass_key`: Password for HTTP Basic authentication (default: `"password"`)
- `bearer_token`: Token for HTTP Bearer authentication (default: `"token"`)
- `additional_headers`: Additional headers to include in all requests (default: `{}`)

#### HTTP Behavior
- `timeout`: Request timeout in seconds (default: `5.0`)
- `follow_redirects`: Whether to automatically follow HTTP redirects (default: `False`)
- `max_redirects`: Maximum number of redirects to follow (default: `20`)

#### Security
- `verify_ssl`: Whether to verify SSL certificates (default: `True`)

#### Performance
- `http2`: Whether to enable HTTP/2 support (default: `False`)
- `limits`: Connection pool limits via `httpx.Limits` (default: `None`)
- `transport`: Custom transport via `httpx.HTTPTransport` or `httpx.AsyncHTTPTransport` (default: `None`)

### Function-Based Client Configuration

Function-based clients use a `Config` object (similar to class-based clients) that supports loading values from environment variables using pydantic-settings:

```python
# In your generated client's config.py file
from pydantic_settings import BaseSettings

class Config(BaseSettings):
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

**Setting Values:**

1. **Environment Variables** (recommended for production):
```bash
export API_BASE_URL="https://api.production.com"
export BEARER_TOKEN="your-secret-token"
export TIMEOUT=30.0
export HTTP2=true
```

2. **Direct Modification** (for testing/development):
```python
# Modify the default values in config.py
config = Config(
    api_base_url="https://api.example.com",
    bearer_token="my-token",
    timeout=30.0,
    http2=True
)
```

3. **.env File** (requires python-dotenv):
```
# .env file
API_BASE_URL=https://api.example.com
BEARER_TOKEN=my-token
TIMEOUT=30.0
```

### Class-Based Client Configuration

For class-based clients, pass configuration options when creating the client:

```python
from my_client.client import Client
from my_client import config

# Custom configuration
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

### Configuration Examples

#### Increase Timeout for Slow APIs

```python
# Function-based client (via environment variable)
export TIMEOUT=60.0

# Function-based client (via code)
from my_client import config
config.config = config.Config(timeout=60.0)

# Class-based client
config = Config(timeout=60.0)
client = Client(config=config)
```

#### Enable HTTP/2 for Better Performance

```python
# Function-based client (via environment variable)
export HTTP2=true

# Function-based client (via code)
from my_client import config
config.config = config.Config(http2=True)

# Class-based client
config = Config(http2=True)
client = Client(config=config)
```

#### Development Environment (Disable SSL Verification)

!!! warning
    
    Only disable SSL verification in development environments. Never disable it in production!

```python
# Function-based client (via environment variable)
export VERIFY_SSL=false

# Function-based client (via code)
from my_client import config
config.config = config.Config(verify_ssl=False)

# Class-based client
config = Config(verify_ssl=False)
client = Client(config=config)
```

#### Follow Redirects

```python
# Function-based client (via environment variables)
export FOLLOW_REDIRECTS=true
export MAX_REDIRECTS=5

# Function-based client (via code)
from my_client import config
config.config = config.Config(follow_redirects=True, max_redirects=5)

# Class-based client
config = Config(follow_redirects=True, max_redirects=5)
client = Client(config=config)
```

#### Configure Connection Pool Limits

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
config = Config(
    limits=httpx.Limits(
        max_keepalive_connections=10,
        max_connections=20
    )
)
client = Client(config=config)
```

#### Configure Custom Transport

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
config = Config(
    transport=httpx.HTTPTransport(retries=3)
)
client = Client(config=config)

# Class-based client (async)
config = Config(
    transport=httpx.AsyncHTTPTransport(retries=3)
)
client = AsyncClient(config=config)
```

## generate-basic

The `generate-basic` command can be used to generate a basic file structure for an HTTP client.

It does not require an OpenAPI schema, just a path.

This command serves two purposes:

1. You may have an HTTP API without an OpenAPI schema and you want to keep a consistent file structure with other Clientele clients.
2. The generator for this basic client can be extended for your own client in the future, if you choose.

```sh
clientele generate-basic -o my_client/
```

## `explore`

Run the explorer mode. See [explore](explore.md).


## `version`

Print the current version of Clientele:

```sh
> clientele version
Clientele 1.0.0
```

## Regenerating

At times you may wish to regenerate the client. This could be because the API has updated or you just want to use a newer version of clientele.

To force a regeneration you must pass the `--regen` or `-r` argument, for example:

```sh
clientele generate -f example_openapi_specs/best.json -o my_client/  --regen t
```

!!! note

    You can copy and paste the command from the `MANIFEST.md` file in your previously-generated client for a quick and easy regeneration.

### Understanding Regeneration

When you regenerate a client with `--regen t`, Clientele follows these rules:

**Files that WILL be overwritten:**

- `client.py` - Your API client functions/class
- `schemas.py` - Pydantic models for request/response data
- `http.py` - HTTP handling logic
- `__init__.py` - Package initialization
- `MANIFEST.md` - Metadata about the generated client

**Files that will NOT be overwritten:**

- `config.py` - Your custom configuration (API URL, auth tokens, headers)

This design ensures your customizations in `config.py` are preserved while keeping the client code in sync with the latest API schema.

### The MANIFEST.md File

Every generated client includes a `MANIFEST.md` file that records:

- The exact command used to generate the client
- The OpenAPI version of the source schema
- The Clientele version used
- Generation timestamp

Example `MANIFEST.md`:

```markdown
# Manifest

Generated with [https://github.com/phalt/clientele](https://github.com/phalt/clientele)
Install with pipx:

```sh
pipx install clientele
```

API VERSION: 0.1.0
OPENAPI VERSION: 3.0.2
CLIENTELE VERSION: 1.0.0

Regenerate using this command:

```sh
clientele generate -f example_openapi_specs/best.json -o tests/async_test_client/ --asyncio t --regen t
```

You can copy the command directly from this file to regenerate your client.

### Regeneration Workflow

Here's the recommended workflow for keeping your client in sync:

1. **API Updated**: Your API has new endpoints or changed schemas
2. **Regenerate**: Run `clientele generate` with `--regen t`
   ```sh
   clientele generate -u http://localhost:8000/openapi.json -o my_client/ --regen t
   ```
3. **Review Changes**: Use git to see what changed
   ```sh
   git diff my_client/
   ```
4. **Inspect**: Look at:
   - New functions in `client.py`
   - Modified schemas in `schemas.py`
   - Changes to function signatures
5. **Test**: Run your test suite to catch breaking changes
   ```sh
   pytest tests/
   ```
6. **Commit**: Add the changes to git
   ```sh
   git add my_client/
   git commit -m "Regenerate client for API v2.1"
   ```

### Handling Breaking Changes

When the API introduces breaking changes, regeneration will reflect them:

- **Removed endpoints** → Functions deleted from `client.py`
- **Renamed fields** → Schema properties change
- **New required fields** → Function signatures updated
- **Changed response types** → Schema unions modified

Your tests should catch these issues. If you need to support multiple API versions, consider:

- Generating separate clients for each version
- Using version-specific directories (e.g., `my_client_v1/`, `my_client_v2/`)

### Regenerating vs. Fresh Generation

**Regenerating** (`--regen t`):

- Overwrites most files except `config.py`
- Preserves your configuration
- Intended for updating an existing client

**Fresh Generation** (without `--regen`):

- Will fail if the output directory already exists
- Use for creating a new client from scratch

### Integration with CI/CD

You can automate regeneration in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Regenerate API client
  run: |
    clientele generate \
      -u http://api:8000/openapi.json \
      -o clients/my_api/ \
      --regen t
    
    # Check if client changed
    if ! git diff --quiet clients/my_api/; then
      echo "API client changed - review required"
      git diff clients/my_api/
      exit 1
    fi
```

This keeps your client in sync with the API schema.
