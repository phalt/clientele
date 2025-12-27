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

Clientele generates fully-typed, idiomatic python HTTP API clients from OpenAPI 3.0+ schemas.

It is designed and tested to work perfectly with the most popular Python API frameworks:

- **[FastAPI](https://fastapi.tiangolo.com/)**
- **[Django REST Framework](https://www.django-rest-framework.org/)** via **[drf-spectacular](https://github.com/tfranzel/drf-spectacular)**
- **[Django Ninja](https://django-ninja.dev/)**

## What Clientele Does

Clientele transforms your OpenAPI schema into a clean, maintainable Python HTTP client with:

- **Developer first approach** designed for a loveable developer experience.
- **Pydantic models** for request and response validation.
- **Fully-typed function signatures** for IDE autocomplete and type checking.
- **Async support** if you want a concurrent client.
- **Multiple formats** - class-based or functional, you can choose.
- **Tiny output** - the generated code is readable, debuggable Python with only two dependencies.
- **Regeneration-friendly** - update your API, regenerate, review the git diff, then ship it!
- **API REPL** - a dedicated REPL for exploring and testing the client.
- **Deterministic**: No exepensive LLMs, no hallucinations - same input always produces same output.

### When to Use Clientele

#### Consumer

- You want to use an HTTP API that has an OpenAPI schema
- And you want to consume that API from a Python application
- And you want type safety and validation without manual schema maintenance
- And you want code that is readable, maintainable, and extendable to suit your project

#### Publisher

- You have an HTTP API that has an OpenAPI schema
- And you want to offer a client library in Python
- And you want developers to love using the client

## Quick Start

```sh
# Best installed as a tool
uv tool install clientele
# Generate a client from the PokeAPI OpenAPI schema
clientele generate -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml -o pokeapi_client/
# Load the REPL to start testing with the generated code immediately
clientele explore -c pokeapi_client/
```

![generate_gif](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele_generate.gif)

## The generated code

We offer many different flavours of client to suit your needs:

### Function-based client

```py
from my_api import client, schemas

# Pydantic models for inputs and outputs
data = schemas.CreateBookRequest(title="My awesome book")

# Easy to read client functions
response = client.create_book(data=data)

# Handle responses elegantly
match response:
    case schemas.CreateBookResponse():
        # Handle valid response
        ...
    case schemas.ValidationError():
        # Handle validation error
        ...
```

### Class-based client

```py
from my_api.client import Client
from my_api import schemas

# Instantiate the client
client = Client()

# Pydantic models for inputs and outputs
data = schemas.CreateBookRequest(title="My awesome book")

# Call API methods on the client instance
response = client.create_book(data=data)

# Handle responses elegantly
match response:
    case schemas.CreateBookResponse():
        # Handle valid response
        ...
    case schemas.ValidationError():
        # Handle validation error
        ...
```

## Async support

For both class-based and functional clients we can produce async versions:

```py
from my_async_api import client

# Async client functions
response = await client.list_books()
```

## API Explorer

![repl demo](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele.gif)

Clientele includes an **interactive REPL** that lets you explore and test APIs without writing any code:

```sh
# Explore an existing client
clientele explore -c pokeapi_client/

# Or generate a temporary client from any OpenAPI service on the web and start using it immediately
clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml

═══════════════════════════════════════════════════════════
  Clientele Interactive API Explorer v1.0.0
═══════════════════════════════════════════════════════════

Type /help or ? for commands, /exit or Ctrl+D to quit
Type /list to see available operations

Press TAB for autocomplete

>>>

```

### Explorer Features

- **Autocomplete**: Press TAB to discover operations and parameters with type hints.
- **Execute instantly**: Execute API operations with Python-like syntax.
- **Beautiful output**: Syntax-highlighted JSON responses.
- **Command history**: Navigate previous commands with UP/DOWN arrows.
- **Local config**: Modify configuration locally as you're testing.
- **Debug mode**: Run debug mode to see diagnostics and errors.

## OpenAPI Compatibility

Clientele works by traversing OpenAPI 3.0+ schemas.

Any framework or tool that generates standards-compliant OpenAPI schemas should work with Clientele.

### Verified Compatibility

We test Clientele against 2000+ real-world OpenAPI schemas from the [APIs.guru OpenAPI Directory](https://github.com/APIs-guru/openapi-directory) through a CI cron job.

As of our latest run, we successfully generate clients for **95.39%** of schemas in the directory.

![OpenAPI Compatibility](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json)

Additionally we have specifically built and tested Clientele to support:

- **FastAPI** - 100% compatibility with FastAPI's built-in OpenAPI schema generation.
- **Django REST Framework** with **drf-spectacular** - Full support for DRF's OpenAPI schemas.
- **Django Ninja** - Works with Django Ninja's OpenAPI output.

#### Server Examples

Working example server applications are available in the [`server_examples/`](https://github.com/phalt/clientele/tree/main/server_examples) directory. Read more about each in our documentation:

- **FastAPI** - See [`server_examples/fastapi/`](https://phalt.github.io/clientele/framework-fastapi/)
- **Django REST Framework** - See [`server_examples/django-rest-framework/`](https://phalt.github.io/clientele/framework-drf/)
- **Django Ninja** - See [`server_examples/django-ninja/`](https://phalt.github.io/clientele/framework-django-ninja/)

These examples match the code shown in our framework-specific documentation and provide real, working servers you can run locally to test Clientele's client generation.

## Additional Features

- **Authentication**: HTTP Basic and HTTP Bearer authentication built-in.
- **Configuration**: A `config.py` entry point that's never overwritten on regeneration.
- **Testing**: Designed for easy testing thanks to [respx](https://lundberg.github.io/respx/).
- **Formatting**: Automatically formats generated code with [Ruff](https://docs.astral.sh/ruff/).

## Getting Started

👉 See our [framework-specific guides](https://phalt.github.io/clientele/framework-fastapi/) for FastAPI, Django REST Framework, and Django Ninja

👉 Read the [full documentation](https://phalt.github.io/clientele/) for advanced usage
