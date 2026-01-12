# 🔄 Retries

In reality, networks can fail. Sometimes we want to be able to apply retry logic to handle this.

Clientele does not have any built-in retry logic because there are many well tested options available that already work well. 

However, we are considering introducing a comfortable abstraction, [add your opinion here](https://github.com/phalt/clientele/issues/158).

## Transport configuration

You can set a retry transport, such as [httpx-retries](https://will-ockmore.github.io/httpx-retries/), using Clientele's configuration:

```python
from clientele import api
from httpx_retries import RetryTransport

config = api.BaseConfig(base_url="https://myapi.com", transport=RetryTransport())

client = api.APIClient(config=config)
```

## Custom HTTPX Client

Alternatively you can use a retry transport with a custom `httpx.Client`:

```python
import httpx
from clientele import api
from httpx_retries import RetryTransport

httpx_client = httpx.Client(transport=RetryTransport())

client = api.APIClient(base_url="https://myapi.com", httpx_client=httpx_client)
```

## Decorator

A good alternative approach is to use [stamina](https://stamina.hynek.me/en/stable/), a popular and versatile retry logic decorator.

Stamina "just works" with Clientele:

```python
from clientele import api
import stamina
import httpx

client = api.APIClient(base_url="https://httpbin.org/")

@stamina.retry(on=httpx.HTTPError, attempts=3)
@client.get("/status/{status_code}")
def get_status(status_code: int, result: dict) -> dict:
    return result
```
