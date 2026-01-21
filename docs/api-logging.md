# 🪵 Logging

Clientele supports debug logging.

## Example

```python
import logging

from clientele import api
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)

config = api.BaseConfig(base_url="https://httpbin.org", logger=logging.getLogger("my_pokeapi_client"))

client = api.APIClient(config=config)


class InputData(BaseModel):
    name: str


@client.post("/anything")
def send_post_data(data: InputData, result: dict) -> str:
    return result["json"]
```

- With the logger set you will see debug information about the prepared request and the response.
- The time it took for a request to return will also be printed.

```python
>>> send_post_data(data={"name": "hello!"})
DEBUG:my_pokeapi_client:HTTP Request: POST /anything
DEBUG:my_pokeapi_client:Request Query Params: {}
DEBUG:my_pokeapi_client:Request Payload: {'name': 'hello!'}
DEBUG:my_pokeapi_client:Request Headers: {}
DEBUG:my_pokeapi_client:HTTP Response: POST /anything -> 200 (0.567s)
DEBUG:my_pokeapi_client:Response Content: {
  ...,
  "json": {
    "name": "hello!"
  }, 
}
DEBUG:my_pokeapi_client:Response Headers: {...}
>>> {'name': 'hello!'}
```
