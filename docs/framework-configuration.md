# Client configuration

## base url

You can configure Clientele with just a `base_url` and let it use sensible defaults for the client:

```python
from clientele import framework

client = framework.client(base_url="https://myapi.com/v1")
```

## Standard configuration

We recommend subclassing `BaseConfig` and managing your own config:

```python
from clientele import framework

config = framework.BaseConfig(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer <token>"},
    timeout=10.0,
)
client = framework.Client(config=config)
```

The `BaseConfig` class is powered by [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) that automatically loads values from environment variables, `.env` files or just plain hard coded configuration.

## Custom httpx client

You can supply your own `httpx.Client` and `httpx.AsyncClient` if you prefer full control:

```python

from clientele import framework
import httpx

client = framework.Client(
    base_url="https://api.example.com",
    httpx_client=httpx.Client(), 
    httpx_async_client=httpx.AsyncClient()
)
```
