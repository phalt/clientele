# ⚙️ Configuration

## base url

You can configure Clientele with just a `base_url` and let it use sensible defaults for the client:

```python
from clientele import api as clientele_api

client = clientele_api.APIClient(base_url="https://myapi.com/v1")
```

## Standard configuration

We recommend subclassing `BaseConfig` and managing your own config:

```python
from clientele import api as clientele_api

config = clientele_api.BaseConfig(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer <token>"},
    timeout=10.0,
)
client = clientele_api.APIClient(config=config)
```

The `BaseConfig` class is powered by [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) that automatically loads values from environment variables, `.env` files or just plain hard coded configuration.

### Configuration options

- `base_url: str` - the url for the API server
- `headers: dict[str, str]` - headers that you want to send with http requests.
- `timeout: float | None = 5.0` - the time to wait for an HTTP response before closing the connection.
- `follow_redirects: bool = False` - if redirects should be followed.
- `verify: bool | str = True` - if SSL connections should be verified.
- `http2: bool = False` - if http2 should be used for making requests.
- `cache_backend` - the [cache backend](api-cache.md) you want to use when caching results.
- `http_backend` - the [http backend](api-http-backends.md) you want to use when making HTTP requests.

## Reconfiguration

You can reconfigure an existing client (`APIClient`) at any time using the `configure` method. This is useful when you want to change options at runtime based on application specific configuration or logic:

```python
from clientele import api as clientele_api
from application.config import app_config

# standard configuration
base_config = clientele_api.BaseConfig(
    base_url="https://api.example.com",
    timeout=10.0,
)
client = clientele_api.APIClient(config=base_config)

@client.get("/users/{user_id}")
def get_user(result: User, user_id: int) -> User:
    return result

class MyApplication:
    def __init__(self, api_client: clientele_api.APIClient):
        self.api_client = api_client

    def run(self):
        # get configuration from application settings
        url = app_config.url
        token = app_config.token

        # reconfigure the client with new settings
        self.api_client.configure(
            clientele_api.BaseConfig(
                base_url=url,
                headers={"Authorization": f"Bearer {token}"},
            )
        )
        # proceed with using the api client as usual after reconfiguration
        get_user(user_id=123)


if __name__ == "__main__":
    app = MyApplication(api_client=client)
    app.run()
```

The `configure` method accepts the same parameters as the `APIClient` constructor.
