# ⚜️ Clientele 

![https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_header.png](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_header.png)

[![Package version](https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version)](https://pypi.org/project/clientele)
![Python versions](https://img.shields.io/badge/python-3.10+-blue)
![PyPI - License](https://img.shields.io/pypi/l/clientele)
[![codecov](https://codecov.io/github/phalt/clientele/graph/badge.svg?token=7OH7QLCGBM)](https://codecov.io/github/phalt/clientele)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/clientele?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads)](https://pepy.tech/projects/clientele)

![Works with](https://img.shields.io/badge/Works_with-FastAPI,_DRF,_Django_Ninja-green)
![OpenAPI Compatibility](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json)

## Example code

```python
from clientele import api
from .schemas import Pokemon

client = api.APIClient(base_url="https://pokeapi.co/api/v2/")

@client.get("/pokemon/{id}")
def get_pokemon_name(id: int, result: Pokemon) -> str:
    return result.name
```

[See more examples](https://docs.clientele.dev/api-examples/).

## Why use Clientele?

- **Just modern Python** - [Types](https://fastapi.tiangolo.com/python-types/), [Pydantic](https://docs.pydantic.dev/latest/), and [HTTPX](https://www.python-httpx.org/), that's it.
- **Easy to learn** - Clientele is visually similar to popular python API server frameworks.
- **Easy to test** - Works with existing tools like [respx](https://lundberg.github.io/respx/) and [pytest-httpx](https://pypi.org/project/pytest-httpx/).
- **Easy to configure** - Clientele has sensible defaults and plenty of hooks for customisation.
- **A comfortable abstraction** - Focus on the data and the functionality, not the connectivity.
- **OpenAPI support** - Build your own client, or scaffold one from an OpenAPI schema.

## Async support

```python
@client.get("/pokemon/{id}")
async def get_pokemon_name(id: int, result: Pokemon) -> str:
    return result.name
```

## Automatic data validation

```python
from clientele import api as clientele_api
from .my_pydantic_models import CreateBookRequest, CreateBookResponse

client = clientele_api.APIClient(base_url="http://localhost:8000")


@client.post("/books")
def create_book(data: CreateBookRequest, result: CreateBookReponse) -> CreateBookResponse:
    return result
```

## Works with Python API frameworks

Built and tested to be 100% compatible with the OpenAPI schemas generated from:

- **FastAPI**
- **Django REST Framework** via **drf-spectacular**
- **Django Ninja**

See the working demos in our [`server_examples/`](https://github.com/phalt/clientele/tree/main/server_examples) directory.

## OpenAPI support

Clientele can create scaffolding for an API client from an OpenAPI schema with:

- **Pydantic models** generated from the schema objects.
- **Smart function signatures** generated from schema operations.
- **Async support** if you want a client with concurrency.
- **A tiny output** that is only 3 files big.
- **Regeneration-friendly** - update your API, regenerate, review the git diff, then ship it!
- **Formatted code** thanks to [Ruff](https://docs.astral.sh/ruff/).

![generate_gif](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_generate.gif)

## API Client explorer

Clientele has an `explore` mode for quickly testing and debugging APIs through an interactive REPL:

```sh
# Explore an existing clientele-compatible client
uvx clientele explore -c my_clientele_client/

# Or generate a temporary client from any OpenAPI service on the web
uvx clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
# 🤫 Pssst! Copy and paste this right now to try it!
```

![repl demo](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele.gif)

- **Autocomplete** for operations and schemas.
- **Execute API operations** to test the API.
- **Inspect schemas** to see what the objects look like.
- **Modify configuration** within the REPL as you're testing.

## Getting Started

👉 Read the [full documentation](https://docs.clientele.dev/) for all documentation.
