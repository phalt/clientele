# 🔄 Retries

Clientele provides a built-in decorator for handling HTTP request retries.

## Example

```python
from clientele import api, retries

client = api.APIClient(api.BaseConfig(base_url="https://httpbin.org/"))

@retries.retry(attempts=3)
@client.get("/status/{status_code}")
def get_status(status_code: int, result: dict) -> dict:
    return result
```

## Declare status codes to retry

```python
from clientele import api, retries

client = api.APIClient(api.BaseConfig(base_url="https://httpbin.org/"))

@retries.retry(attempts=3, on_status=[400, 403, 500])
@client.get("/status/{status_code}")
def get_status(status_code: int, result: dict) -> dict:
    return result
```

## How it works

- Clientele's decorator is a small wrapper for [stamina](https://stamina.hynek.me/en/stable/), a popular and versatile retry logic decorator.
- We have configured the `retries.retry` decorator to work with Clientele specific exception behaviour.
- A default status that is 500 or higher will be retried using Stamina's [backoff and jitter](https://stamina.hynek.me/en/stable/motivation.html) approach.
- If you supply `on_status` then it will only retry for those specific statuses.
- If you want more granular control then you can swap to `stamina.retry` and configure yourself.
