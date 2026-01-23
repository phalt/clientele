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

## Creating Custom Backends

Example: psuedocode `aiohttp` async HTTP backend

```python
from clientele.http import backends, response
import aiohttp

class AiohttpHTTPBackend(backends.HTTPBackend):
    def __init__(self):
        self._session: aiohttp.ClientSession | None = None
    
    def build_client(self):
        # For sync, return a placeholder or raise NotImplementedError
        raise NotImplementedError("Use async_client for aiohttp")
    
    def build_async_client(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @staticmethod
    def convert_to_response(native_response: aiohttp.ClientResponse) -> response.Response:
        """Convert aiohttp.ClientResponse to generic Response"""
        return response.Response(
            status_code=native_response.status,
            headers=dict(native_response.headers),
            content=native_response._body,
            text=native_response._body.decode('utf-8'),
            request_method=native_response.method,
            request_url=str(native_response.url),
        )
    
    def send_sync_request(self, method, url, **kwargs):
        raise NotImplementedError("Use async backend")
    
    async def send_async_request(self, method, url, **kwargs):
        async with self._session.request(method, url, **kwargs) as resp:
            await resp.read()
            return self.convert_to_response(resp)
    
    def close(self):
        pass  # aiohttp doesn't need sync close
    
    async def aclose(self):
        if self._session:
            await self._session.close()
```

### Default Behavior

If no backend is provided, clientele uses httpx as the backend:

```python
# This still works and uses httpx internally
cfg = config.BaseConfig(base_url="https://api.example.com")
api_client = client.APIClient(config=cfg)
```
