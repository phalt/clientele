# ⚜️ Clientele

<div style="text-align: center;">
    <img src="https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_header.png">
</div>

[![Package version](https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version)](https://pypi.org/project/clientele)
![Python versions](https://img.shields.io/badge/python-3.10+-blue)
[![codecov](https://codecov.io/github/phalt/clientele/graph/badge.svg?token=7OH7QLCGBM)](https://codecov.io/github/phalt/clientele)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/clientele?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads)](https://pepy.tech/projects/clientele)
![PyPI - License](https://img.shields.io/pypi/l/clientele)
![OpenAPI Compatibility](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json)

Clientele is a different way to think about Python API Clients.

## Clientele framework

Clientele lets your write API clients as easily as you would write API servers:

```python
from clientele import framework
from .my_config import Config
from .my_models import BookResponse, CreateBookReponse, CreateBookRequest

client = framework.Client(config=Config())

@client.post("/books")
def create_user(
    data: CreateBookReponse,
    result: CreateBookReponse,
) -> CreateBookReponse:
    return result


# Mix sync and async functions in the same client
@client.get("/book/{book_id}")
async def get_book(book_id: int, result: BookResponse) -> BookResponse:
    return result
```

The developer experience using the client is elegant:

```python
from my_clientele_client import client, schemas

response = client.create_book(
    data=schemas.CreateBookRequest(title="My awesome book")
)

match response:
    case schemas.CreateBookResponse():
        # handle valid response
    case schemas.ValidationError():
        # handle errors

# Handle async requests
book_response = await client.get_book(book_id=123)
```

## OpenAPI client generator

Clientele can scaffold an API client from an OpenAPI schema with:

- **A developer-first approach** designed for a loveable developer experience.
- **Pydantic models** for request and response validation.
- **Fully-typed function signatures** for IDE autocomplete and type checking.
- **Async support** if you want a client with concurrency.
- **A tiny output** - clientele is readable, debuggable Python.
- **Regeneration-friendly** - update your API, regenerate, review the git diff, then ship it!
- **Configuration**: that's never overwritten on regeneration.
- **Testing**: that is easy via [respx](https://lundberg.github.io/respx/).
- **Formatted output**: via [Ruff](https://docs.astral.sh/ruff/).

![generate_gif](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_generate.gif)

## API REPL

Clientele has an `explore` mode for quickly testing and debugging APIs through an interactive REPL:

```sh
# Explore an existing clientele-compatible client
uvx clientele explore -c my_clientele_client/

# Or generate a temporary client from any OpenAPI service on the web
uvx clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
# 🤫 Pssst! Copy and paste this right now to try it!
```

![repl demo](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele.gif)

### Explorer Features

- **Autocomplete** for operations and schemas.
- **Execute API operations** with Python-like syntax.
- **Syntax-highlighted** JSON responses.
- **Navigate previous commands** like a python shell.
- **Modify configuration** within the REPL as you're testing.
- **Run debug mode** to see diagnostics and errors.

## OpenAPI Compatibility

Clientele can scaffold clients by traversing OpenAPI 3.0+ schemas.

### Verified Compatibility

We test Clientele against 2000+ real-world OpenAPI schemas from the [APIs.guru OpenAPI Directory](https://github.com/APIs-guru/openapi-directory) through a CI cron job.

As of our latest run, we successfully generate clients for **95.39%** of schemas in the directory.

![OpenAPI Compatibility](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json)

We have specifically built and tested Clientele to be 100% compatible with OpenAPI schemas generated from:

- **FastAPI**
- **Django REST Framework** via **drf-spectacular**
- **Django Ninja**

#### Server Examples

We have working example servers in the [`server_examples/`](https://github.com/phalt/clientele/tree/main/server_examples) directory. Read more about each in our documentation:

- **FastAPI** - See [`server_examples/fastapi/`](https://phalt.github.io/clientele/framework-fastapi/)
- **Django REST Framework** - See [`server_examples/django-rest-framework/`](https://phalt.github.io/clientele/framework-drf/)
- **Django Ninja** - See [`server_examples/django-ninja/`](https://phalt.github.io/clientele/framework-django-ninja/)

These examples match the code shown in our framework-specific documentation and provide real, working servers you can run locally to test Clientele's client generation.

## Getting Started

👉 See our [framework-specific guides](https://phalt.github.io/clientele/framework-fastapi/) for FastAPI, Django REST Framework, and Django Ninja

👉 Read the [full documentation](https://phalt.github.io/clientele/) for advanced usage
