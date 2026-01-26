# ⚜️ Clientele

![https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_header.png](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_header.png)

[![Package version](https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version)](https://pypi.org/project/clientele)
![Python versions](https://img.shields.io/badge/python-3.10+-blue)
![PyPI - License](https://img.shields.io/pypi/l/clientele)
[![codecov](https://codecov.io/github/phalt/clientele/graph/badge.svg?token=7OH7QLCGBM)](https://codecov.io/github/phalt/clientele)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/clientele?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads)](https://pepy.tech/projects/clientele)

![Pydantic Badge](https://img.shields.io/badge/Data_validation-pydantic-violet?style=flat)
![Http Badge](https://img.shields.io/badge/HTTP-Customisable-blue?style=flat)

## Example code

```python
from clientele import api
from pydantic import BaseModel

client = api.APIClient(base_url="https://pokeapi.co/api/v2/")

class Pokemon(BaseModel):
    name: str

@client.get("/pokemon/{id}")
def get_pokemon_name(id: int, result: Pokemon) -> str:
    return result.name
```

[See more examples](https://docs.clientele.dev/api-examples/)

## Why use Clientele?

- **A comfortable abstraction** - Encourages consistency and focus on the functionality.
- **Easy to learn** - Clientele is visually similar to popular python API server frameworks.
- **Easy to test** - All the testing tools you need to maintain API integrations.
- **Easy to configure** - Sensible HTTP defaults and plenty of hooks for customisation.
- **Easy data validation** - Built in data validation using [Pydantic](https://docs.pydantic.dev/latest/).
- **Core built-ins** - Caching, Network, and Retry handling built specifically for HTTP.
- **Use your own HTTP** - Clientele can support any Python HTTP library.
- **OpenAPI support** - Build your own client, or scaffold one from an OpenAPI schema.
- **GraphQL support** - Clientele has a GraphQLClient tailored for GraphQL APIs.

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
def create_book(data: CreateBookRequest, result: CreateBookResponse) -> CreateBookResponse:
    return result
```

## GraphQL support

```python
from pydantic import BaseModel
from clientele.graphql import GraphQLClient

client = GraphQLClient(base_url="https://api.github.com/graphql")

class Repository(BaseModel):
    name: str
    stargazerCount: int

class RepositoryQueryData(BaseModel):
    repository: Repository

class RepositoryQueryResponse(BaseModel):
    data: RepositoryQueryData

@client.query("""
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
            stargazerCount
        }
    }
""")
def get_repo(owner: str, name: str, result: RepositoryQueryResponse) -> Repository:
    return result.data.repository
```

## Works with Python API frameworks

Building an API service in Python? Clientele can build you a client library in seconds.

Clientele is built and tested to be 100% compatible with the OpenAPI schemas generated from:

- **FastAPI**
- **Django REST Framework** via **drf-spectacular**
- **Django Ninja**

See the working demos in our [`server_examples/`](https://github.com/phalt/clientele/tree/main/server_examples) directory.

## OpenAPI support

Clientele can create scaffolding for an API client from an OpenAPI schema with:

- **Pydantic models** generated from the schema objects.
- **Decorated function signatures** generated from schema operations.
- **Async support** if you want a client with concurrency.
- **A tiny output** that is only 3 files big.
- **Regeneration-friendly** - update your API, regenerate, review the git diff, then ship it!
- **Formatted code** thanks to [Ruff](https://docs.astral.sh/ruff/).

![generate_gif](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_generate.gif)

## Getting Started

👉 Read the [full documentation](https://docs.clientele.dev/) for all documentation.
