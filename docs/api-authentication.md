# 🔐 Authentication

Clientele API supports multiple authentication methods through the client configuration.

## Bearer Token

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
