# 🎯 Direct requests

Clientele allows you to make direct requests without decorating functions.

This approach is useful if you want to make ad-hoc requests but still want the data validation and response hydration.

## GET requests

```python
from clientele import api
from pydantic import BaseModel

client = api.APIClient(base_url="https://pokeapi.co/api/v2")

class Pokemon(BaseModel):
    name: str
    height: int
    weight: int

result = client.request(
    "GET",
    "/pokemon/{pokemon_id}",
    response_map={200: Pokemon},
    pokemon_id=1
)
```

- The `response_map` parameter is required
- Additional kwargs are mapped to the path parameter

## POST requests

```python
result = client.request(
    "POST",
    "/pokemon",
    response_map={201: Pokemon},
    data=CreatePokemonRequest(name="PikachuTew")
)
```

## Async

The `arequest` method provides an identical interface but in an async context.

## Trade-offs

This approach is intended for smaller ad-hoc requests.

This approach misses all of the benefits of binding to a decorated function:

- Strongly typed inputs for input parameters
- An abstract functional interface to the API
- Streaming responses are not supported

This approach still retains:

- Strongly typed responses
- Data validation on the responses
- Hydration of the responses
