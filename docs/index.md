# ⚜️ Clientele

## The Python API Client Generator for FastAPI, Django REST Framework, and Django Ninja

[![Package version](https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version)](https://pypi.org/project/clientele)
[![codecov](https://codecov.io/github/phalt/clientele/graph/badge.svg?token=7OH7QLCGBM)](https://codecov.io/github/phalt/clientele)
![PyPI - Downloads](https://img.shields.io/pypi/dm/clientele)
![PyPI - License](https://img.shields.io/pypi/l/clientele)

Clientele generates fully-typed, pythonic HTTP API clients from OpenAPI 3.0+ schemas. 

Built by Python developers for Python developers, it works seamlessly with:

- **[FastAPI](https://fastapi.tiangolo.com/)** - First-class support for FastAPI's auto-generated OpenAPI schemas
- **[Django REST Framework](https://www.django-rest-framework.org/)** via **[drf-spectacular](https://github.com/tfranzel/drf-spectacular)** - Full compatibility with DRF's OpenAPI schema generation
- **[Django Ninja](https://django-ninja.dev/)** - Native support for Django Ninja's OpenAPI output

### What Clientele Does

Clientele transforms your OpenAPI schema into a clean, maintainable Python client with:

- **Pydantic models** for request/response validation
- **Fully-typed function signatures** for IDE autocomplete and type checking
- **Simple regeneration** - just re-run the same command when your API changes
- **No runtime magic** - generated code is readable, debuggable Python

### When to Use Clientele

Use Clientele when you:

- Have a Web API that generates OpenAPI schemas
- Want to consume that API from another Python service or application
- Need type safety and validation without manual schema maintenance
- Want generated code that is readable and maintainable

### Why Clientele

- **Python-native DX**: Designed around Pydantic, httpx, and modern Python conventions
- **Readable output**: The generated client is clean Python you can understand and debug
- **Minimal dependencies**: Only httpx and Pydantic required in generated code
- **Regeneration-friendly**: Update your API, regenerate, review the git diff
- **Deterministic**: No LLMs, no hallucinations - same input always produces same output

## Installation

Install clientele as a global CLI tool:

### With pipx (Python)

```sh
pipx install clientele
```

### With uv (Python)

```sh
uv tool install clientele
```

## Quick Start

```sh
# Generate a client from the PokeAPI OpenAPI schema
clientele generate -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml -o pokeapi_client/
```

## Generated code

The generated code uses modern tooling and has a great developer experience.

### Function-based client

```py
from my_api import client, schemas

# Pydantic models for inputs and outputs
data = schemas.RequestDataRequest(my_input="test")

# Easy to read client functions
response = client.request_data_request_data_post(data=data)

# Handle responses elegantly
match response:
    case schemas.RequestDataResponse():
        # Handle valid response
        ...
    case schemas.ValidationError():
        # Handle validation error
        ...
```

### Class-based client

Prefer object-oriented programming? Use `clientele generate-class` to generate a client with a `Client` class:

```py
from my_api.client import Client
from my_api import schemas

# Instantiate the client
client = Client()

# Pydantic models for inputs and outputs
data = schemas.RequestDataRequest(my_input="test")

# Call API methods on the client instance
response = client.request_data_request_data_post(data=data)

# Handle responses elegantly
match response:
    case schemas.RequestDataResponse():
        # Handle valid response
        ...
    case schemas.ValidationError():
        # Handle validation error
        ...
```

The generated code is tiny - the [example schema](https://github.com/phalt/clientele/blob/main/example_openapi_specs/best.json) we use for documentation and testing only requires [250 lines of code](https://github.com/phalt/clientele/tree/main/tests/test_client) and 5 files.

## Async support

You can choose to generate either a sync or an async client - we support both:

```py
from my_async_api import client

# Async client functions
response = await client.simple_request_simple_request_get()
```

## Interactive API Explorer

Clientele includes an **interactive REPL** that lets you explore and test APIs without writing any code:

```sh
# Explore an existing client
clientele explore -c pokeapi_client/

# Or generate a temporary client and explore directly from a schema
clientele explore -f pokeapi_openapi.yml
clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
```

### Explorer Features

- **Autocomplete**: Press TAB to discover operations and parameters with type hints
- **Execute instantly**: Test API operations with Python-like syntax
- **Beautiful output**: Syntax-highlighted JSON responses with timing information
- **Command history**: Navigate previous commands with UP/DOWN arrows
- **Special commands**: Built-in helpers like `/list`, `/help`, and more

The explore command is perfect for:

- **API Discovery**: Quickly learn what operations are available
- **Testing**: Try out API calls before writing code


## Framework Compatibility

Clientele works by consuming OpenAPI 3.0+ schemas. 

Any framework or tool that generates standard-compliant OpenAPI schemas will work with Clientele.

### Verified Compatibility

We test Clientele against 4000+ real-world OpenAPI schemas from the [APIs.guru OpenAPI Directory](https://github.com/APIs-guru/openapi-directory). As of our latest run, we successfully generate clients for **93.86%** of schemas in the directory.

We specifically test and support:

- **FastAPI** - 100% compatibility with FastAPI's built-in OpenAPI schema generation
- **Django REST Framework** with **drf-spectacular** - Full support for DRF's OpenAPI schemas
- **Django Ninja** - Works with Django Ninja's OpenAPI output

### How It Works

1. Your Python framework generates an OpenAPI schema (usually available at `/openapi.json` or `/docs/openapi.json`)
2. Clientele reads the schema and generates typed Python client code
3. The generated client uses your schema's `operationId` fields to create method names
4. All request/response models become Pydantic classes with full validation

**Important**: Clientele currently focuses on OpenAPI 3.0.x schemas. While many OpenAPI 3.1 schemas work, some advanced 3.1-specific features may not be fully supported yet.

## Additional Features

- **Authentication**: HTTP Basic and HTTP Bearer authentication built-in
- **Configuration**: `config.py` entry point that's never overwritten on regeneration
- **Testing**: Designed for easy mocking with [respx](https://lundberg.github.io/respx/)
- **Regeneration**: Run the same command again when your API updates - review changes in git
- **Formatting**: Automatically formats generated code with [Ruff](https://docs.astral.sh/ruff/)

## Why not use an LLM to do this?

- Clientele is deterministic - the same input always produces the same output. No hallucinations.
- Clientele is designed by Python developers, for Python developers.
- It's a tiny, focused tool that does one thing well.
- It's not carbon intensive for the problem it's solving.
- LLM compute would be wasteful overkill for this task.

## Getting Started

👉 See our [framework-specific guides](https://phalt.github.io/clientele/) for FastAPI, Django REST Framework, and Django Ninja

👉 Read the [full documentation](https://phalt.github.io/clientele/) for advanced usage
