# 🎪 Clientele by example

All these examples can be copied and pasted into a file and run in a python application.

## Simple GET request

```python
from clientele import api

client = api.APIClient(base_url="https://pokeapi.co/api/v2")

@client.get("/pokemon/{pokemon_name}")
def get_pokemon_info(pokemon_name: str, result: dict) -> dict:
    return result
```

- The simplest logic you can do with Clientele.
- No validation will be ran on the data.

## Receive specific data in result

```python
from clientele import api
from pydantic import BaseModel

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


class PokemonInfo(BaseModel):
    name: str
    id: int


@client.get("/pokemon/{pokemon_name}")
def get_pokemon_info(pokemon_name: str, result: PokemonInfo) -> PokemonInfo:
    return result
```

- Use Pydantic `BaseModel` to return only the data you want in the `result` parameter.
- Pydantic's `model_validate` will be ran against the `reponse.json`.
- Only values explicitly declared in the `BaseModel` will be returned.

## Return specific data after result

```python
from clientele import api

client = api.APIClient(base_url="https://pokeapi.co/api/v2")

@client.get("/pokemon/{pokemon_name}")
def get_pokemon_info(pokemon_name: str, result: dict) -> str:
    return result.get("name")
```

- The return type of the decorated function does not need to match the `result` parameter.
- You can return whatever you like.
- This is also a good time to do logging, persistence of results, dispatching post-request actions, etc.

## Simple POST request

```python
from clientele import api

client = api.APIClient(base_url="https://httpbin.org")


@client.post("/post")
def post_input_data(data: dict, result: dict) -> dict:
    return result
```

- The `data` parameter is serialized to JSON and sent in an HTTP POST request.
- This pattern is identical in `PUT` / `PATCH` / `DELETE` decorators functions.

## Data validation

```python
from clientele import api
from pydantic import BaseModel

client = api.APIClient(base_url="https://httpbin.org")


class InputData(BaseModel):
    name: str
    email: str


@client.post("/post")
def post_input_data(data: InputData, result: dict) -> InputData:
    return result
```

- Pydantic will run `model_validate` on the `data` parameter before sending the HTTP POST request.
- This pattern is identical in `PUT` / `PATCH` / `DELETE` decorators functions.

## Inspect HTTP responses

```python
from clientele import api
import httpx

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


@client.get("/pokemon/{pokemon_name}")
def get_pokemon_info(pokemon_name: str, result: dict, response: httpx.Response) -> dict:
    print(response.headers)
    return result

```

- Pass the `response` parameter to the decorated function to recive the `httpx.Response` object.

## Control response parsing

### Using a callback

```python
from clientele import api
import httpx

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


def parse_response_myself(response: httpx.Response) -> dict:
    data = response.json()
    return {
        "my_custom_key": data["name"],
    }


@client.get("/pokemon/{pokemon_name}", response_parser=parse_response_myself)
def get_pokemon_info(pokemon_name: str, result: dict) -> str:
    return result["my_custom_key"]
```

- Pass a callable to the `response_parser` parameter to control how http responses are parsed.
- Clientele will no longer handle any data validation for you, but you have compelete control.
- The return type of this callback must match the type of the `result` parameter.

### Using strong types

```python
from clientele import api
import httpx
from pydantic import BaseModel

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


class MyResult(BaseModel):
    custom_key: str


def parse_response_myself(response: httpx.Response) -> MyResult:
    data = response.json()
    return MyResult(
        custom_key=data["name"],
    )


@client.get("/pokemon/{pokemon_name}", response_parser=parse_response_myself)
def get_pokemon_info(pokemon_name: str, result: MyResult) -> str:
    return result.custom_key
```

### Using a map

```python
import httpx
from pydantic import BaseModel

from clientele import api

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


class OkResult(BaseModel):
    name: str

class NotFoundResult(BaseModel):
    name: str


@client.get("/pokemon/{pokemon_name}", response_map={200: OkResult, 404: NotFoundResult})
def get_pokemon_info(pokemon_name: str, result: OkResult | NotFoundResult) -> str:
    return result.name
```

- The `response_map` accepts `{int: ResponseModel}`.
- The HTTP response status code will be matched against the model and used as validation.
- If the http response does not match any status codes in the `response_map` then an `clientele.api.APIException` exception will be raised.

## Handling errors

```python
from pydantic import BaseModel

from clientele import api

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


class OnlyErroResult(BaseModel):
    name: str


@client.get("/pokemon/{pokemon_name}", response_map={500: OnlyErroResult})
def get_pokemon_info(pokemon_name: str, result: OnlyErroResult) -> str:
    return result.name


try:
    get_pokemon_info("pikachu")
except api.APIException as e:
    print(f"Error occurred: {e.reason}")
    print(f"Response details: {e.response}")
```

- Unexpected response statuses will throw an `clientele.api.APIException` exception.
- If there is no `response_map` provided then Clientele will call `raise_for_status` on the `httpx.Response` object.
- If `response_map` is provided then the `httpx.Response` status code must match one of the keys.
- The `APIException` will have a human readable `reason`.
- The `APIException` will also have the `httpx.Response` that raised the exception for inspection.

## Configuration

### Using BaseConfig

```python
from clientele import api
import httpx

my_config = api.BaseConfig(base_url="https://httpbin.org")

client = api.APIClient(config=my_config)


@client.get("/get")
def my_function(result: dict) -> dict:
    return result
```

- Instead of providing `base_url` to `APIClient` you can instead provide a `BaseConfig` object.
- This gives you simplified access to common http configuration options.

### Custom headers

```python
from clientele import api
import httpx

my_config = api.BaseConfig(
    base_url="https://httpbin.org", 
    headers={"Custom-Header": "Hello, Clientele!"}
)

client = api.APIClient(config=my_config)


@client.get("/get")
def return_headers(result: dict) -> str:
    """httpbin returns the headers it received."""
    return result["headers"]["Custom-Header"]
```

- Headers can be configured through `BaseConfig`.
- See full configuration options [here](api-configuration.md).

## Async

### Make multiple requests in parallel

```python
import asyncio
from clientele import api

client = api.APIClient(base_url="https://pokeapi.co/api/v2")


@client.get("/pokemon/{pokemon_id}")
async def get_pokemon_name(pokemon_id: int, result: dict) -> str:
    return result["name"]


async def gather():
    async_tasks = [get_pokemon_name(pokemon_id=i) for i in range(1, 152)]
    return await asyncio.gather(*async_tasks)


def get_all_pokemon_names():
    return asyncio.run(gather())

```

- Use the common `gather` / `run` pattern to build modular API calls with Clientele.
- This example executes 151 HTTP requests in parallel.
