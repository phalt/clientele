# HTTP Backends

## Overview

Clientele supports pluggable HTTP backends.

## Architecture

### Core Components

1. **`clientele.http.response.Response`** - Generic HTTP response abstraction
2. **`clientele.http.backends.HTTPBackend`** - Abstract base class for backends
3. **`clientele.http.httpx.HttpxHTTPBackend`** - Default httpx implementation
4. **`clientele.http.fake.FakeHTTPBackend`** - Testing/mocking backend

### Design Principles

The backend abstraction follows these key principles:

1. **Library Agnostic**: The core APIClient doesn't depend on any library-specific implementation.
2. **Generic Response**: All backends return `clientele.http.Response`, not library-specific responses.
3. **Simple Interface**: Backends only need to implement 6 methods.
4. **Conversion Layer**: Each backend converts its native response to the generic format.

## Generic Response

The `clientele.http.response.Response` class provides a library-agnostic interface:

```python
class Response:
    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    
    def json(self) -> Any: ...
    def raise_for_status(self) -> None: ...
    def iter_lines(self) -> Iterator[str]: ...
    def aiter_lines(self) -> AsyncIterator[str]: ...
```

## HTTPBackend Interface

All backends must implement:

```python
class HTTPBackend(abc.ABC):
    @abc.abstractmethod
    def build_client(self) -> Any:
        """Build synchronous HTTP client"""
        
    @abc.abstractmethod
    def build_async_client(self) -> Any:
        """Build asynchronous HTTP client"""
        
    @abc.abstractmethod
    def send_sync_request(self, method: str, url: str, **kwargs) -> typing.Any:
        """Send sync request"""
        
    @abc.abstractmethod
    async def send_async_request(self, method: str, url: str, **kwargs) -> typing.Any:
        """Send async request"""

    @abc.abstractmethod
    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
        """ Handle streaming responses """

    @abc.abstractmethod
    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        """ Handle async streaming responses """

    @staticmethod
    @abc.abstractmethod
    def convert_to_response(native_response: typing.Any) -> Response:
        """Convert a native HTTP response to a generic clientele Response."""
        
    @abc.abstractmethod
    def close(self) -> None:
        """Close sync resources"""
        
    @abc.abstractmethod
    async def aclose(self) -> None:
        """Close async resources"""
```

## Built-in Backends

### HttpxHTTPBackend (Default)

The default backend using httpx:

```python
from clientele.http import httpx_backend
from clientele.api import config

# Note: this will be configured by default,
# this example is just a demonstration.
http_backend = httpx_backend.HttpxHTTPBackend(
    client_options={
        "timeout": 30.0,
        "http2": True,
    }
)

cfg = config.BaseConfig(
    base_url="https://api.example.com",
    http_backend=http_backend,
)
```

### FakeHTTPBackend

A testing backend that captures requests and returns fake responses:

```python
from clientele.http import fake

backend = fake.FakeHTTPBackend(
    default_status=200,
    default_content={"message": "success"},
)

# Queue specific responses
backend.queue_response(
    status=201,
    content={"id": 123, "created": True},
)

# All requests are captured
print(backend.requests)  # [{"method": "POST", "url": "...", "kwargs": {...}}]

# Reset for next test
backend.reset()
```

**Use cases:**

- Unit testing without network calls
- Integration tests with predictable responses
- Demonstrations and examples
- Development mode with fake data

### RequestsHTTPBackend

A synchronous-only backend using the popular [requests](https://requests.readthedocs.io/) library.

!!! note "requests is not installed by default"
    This backend requires `requests` to be installed separately:
    ```
    pip install requests
    ```
    Importing `clientele.http.requests_backend` without `requests` installed will raise an `ImportError` with instructions.

!!! warning "Async not supported"
    `RequestsHTTPBackend` only supports synchronous requests. Calling any async method
    (`send_async_request`, `handle_async_stream`, `build_async_client`) will raise
    `NotImplementedError`. Use `HttpxHTTPBackend` if you need async support.

#### Usage

```python
from clientele.http.requests_backend import RequestsHTTPBackend
from clientele.api import config, client

http_backend = RequestsHTTPBackend(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer my-token"},
    timeout=30.0,
    follow_redirects=True,
    verify=True,
)

cfg = config.BaseConfig(
    base_url="https://api.example.com",
    http_backend=http_backend,
)

api = client.APIClient(config=cfg)

@api.get("/users/{user_id}")
def get_user(result: dict, user_id: int) -> dict:
    return result
```

#### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `""` | Base URL prepended to all relative paths |
| `headers` | `dict` | `{}` | Default headers sent on every request |
| `timeout` | `float \| None` | `5.0` | Timeout in seconds. `None` disables timeout |
| `follow_redirects` | `bool` | `False` | Whether to follow HTTP redirects |
| `verify` | `bool \| str` | `True` | SSL verification. `False` to disable, or path to CA bundle |

#### Limitations

- **Sync only** — async methods raise `NotImplementedError`
- **No HTTP/2** — `requests` does not support HTTP/2; use `HttpxHTTPBackend` with `http2=True` if needed

### AiohttpHTTPBackend

An asynchronous-only backend using the popular [aiohttp](https://docs.aiohttp.org/) library.

!!! note "aiohttp is not installed by default"
    This backend requires `aiohttp` to be installed separately:
    ```
    pip install aiohttp
    ```
    Importing `clientele.http.aiohttp_backend` without `aiohttp` installed will raise an `ImportError` with instructions.

!!! warning "Sync not supported"
    `AiohttpHTTPBackend` only supports asynchronous requests. Calling any sync method
    (`send_sync_request`, `handle_sync_stream`, `build_client`) will raise
    `NotImplementedError`. Use `HttpxHTTPBackend` if you need sync support.

#### Usage

```python
from clientele.http.aiohttp_backend import AiohttpHTTPBackend
from clientele.api import config, client

http_backend = AiohttpHTTPBackend(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer my-token"},
    timeout=30.0,
    follow_redirects=True,
    verify=True,
)

cfg = config.BaseConfig(
    base_url="https://api.example.com",
    http_backend=http_backend,
)

api = client.APIClient(config=cfg)

@api.get("/users/{user_id}")
async def get_user(result: dict, user_id: int) -> dict:
    return result
```

#### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `""` | Base URL prepended to all relative paths |
| `headers` | `dict` | `{}` | Default headers sent on every request |
| `timeout` | `float \| None` | `5.0` | Timeout in seconds. `None` disables timeout |
| `follow_redirects` | `bool` | `False` | Whether to follow HTTP redirects |
| `verify` | `bool` | `True` | SSL verification. `False` to disable |

#### Limitations

- **Async only** — sync methods raise `NotImplementedError`
- **No CA bundle path** — `verify` only accepts `bool`; to use a custom CA bundle, pass a custom `ssl.SSLContext` via a connector directly on the session
- **No HTTP/2** — `aiohttp` does not support HTTP/2 natively

## Creating Custom Backends

To implement your own backend, subclass `clientele.http.backends.HTTPBackend` and implement all abstract methods. Backends that only support one mode (sync or async) should raise `NotImplementedError` in the unsupported methods — see `RequestsHTTPBackend` (sync-only) and `AiohttpHTTPBackend` (async-only) in the source for reference implementations.

### Default Behavior

If no backend is provided, clientele uses httpx as the backend:

```python
# This still works and uses httpx internally
cfg = config.BaseConfig(base_url="https://api.example.com")
api_client = client.APIClient(config=cfg)
```
