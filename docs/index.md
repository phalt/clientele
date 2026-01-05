# ⚜️ Clientele

<style>
  .ascii { max-width: 900px; margin: 48px auto; padding: 2px; }
  .ascii pre { white-space: pre; font-family: ui-monospace, Menlo, Consolas, monospace;
              font-size: 14px; line-height: 1.1; padding: 20px; border-radius: 12px;
              background: #0b0f14; color: #e6edf3; overflow-x: auto; }
  .ascii p { margin: 14px 2px 0; font-family: system-ui, sans-serif; }
</style>

<div style="text-align: center;">
<div class="ascii">
<pre>
___ _ _            _       _
    / __\ (_) ___ _ __ | |_ ___| | ___
    / /  | | |/ _ \ '_ \| __/ _ \ |/ _ \
   / /___| | |  __/ | | | ||  __/ |  __/
   \____/|_|_|\___|_| |_|\__\___|_|\___|</pre>
<p>⚜️ Clientele is a different way to think about Python API Clients</p>
</div>
<p>
    <a href="https://pypi.org/project/clientele">
    <img alt="Package version" src="https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version">
    </a>
    <img alt="Python versions" src="https://img.shields.io/badge/python-3.10+-blue">
    <img alt="PyPI - License" src="https://img.shields.io/pypi/l/clientele">
    <a href="https://codecov.io/github/phalt/clientele">
    <img alt="codecov" src="https://codecov.io/github/phalt/clientele/graph/badge.svg?token=7OH7QLCGBM">
    </a>
    <a href="https://pepy.tech/projects/clientele">
    <img alt="PyPI Downloads" src="https://static.pepy.tech/personalized-badge/clientele?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=GREEN&left_text=Downloads">
    </a>
</p>
<p>
    <img alt="Works with" src="https://img.shields.io/badge/Works_with-FastAPI,_DRF,_Django_Ninja-green">
    <img alt="OpenAPI Compatibility" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json">
</p>
</div>

## Why use Clientele?

- **Inspired by FastAPI** - write API clients as easily as you would write API servers.
- **A neat abstraction** - Focus on the data, let Clientele manage everything else.
- **Modern python** - [Python Types](https://fastapi.tiangolo.com/python-types/), [Pydantic](https://docs.pydantic.dev/latest/), and [httpx](https://www.python-httpx.org/), that's it.
- **Easy to learn** - No complexity, beautiful developer experience, easy to read.
- **Easy to configure** - sane defaults, but plenty of hooks for customisation and control.

## A Simple Example

```python
from clientele import api as clientele_api
from .my_pydantic_models import Book

client = clientele_api.APIClient(base_url="http://localhost:8000")

@client.get("/book/{book_id}")
def get_book(book_id: int, result: Book) -> Book:
    return result

# Or just return the data you want!
@client.get("/book/{book_id}")
def get_book_title(book_id: int, result: Book) -> str:
    return result.title
```

## Async support

```python
from clientele import api as clientele_api
from .my_pydantic_models import Book

client = clientele_api.APIClient(base_url="http://localhost:8000")


# Note: mix sync and async in one client if you want!
@client.get("/book/{book_id}")
async def get_book(book_id: int, result: Book) -> Book:
    return result

```

## Input and output validation with Pydantic

```python
from clientele import api as clientele_api
from .my_pydantic_models import CreateBookRequest, CreateBookResponse

client = clientele_api.APIClient(base_url="http://localhost:8000")


# Strongly typed inputs and outputs
@client.post("/books")
def create_book(data: CreateBookRequest, result: CreateBookReponse) -> CreateBookResponse:
    return result
```

## API Client generator

Clientele can create scaffolding for an API client from an OpenAPI schema with:

- **A developer-first approach** designed for a loveable developer experience.
- **Pydantic models** for request and response validation.
- **Fully-typed function signatures** for IDE autocomplete and type checking.
- **Async support** if you want a client with concurrency.
- **A tiny output** - clientele is readable, debuggable Python.
- **Regeneration-friendly** - update your API, regenerate, review the git diff, then ship it!
- **Configuration**: that's never overwritten on regeneration.
- **Testing** is easy peasy with [respx](https://lundberg.github.io/respx/).
- **Formatted output** with [Ruff](https://docs.astral.sh/ruff/).

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

**Explorer Features**

- **Autocomplete** for operations and schemas.
- **Execute API operations** with Python-like syntax.
- **Syntax-highlighted** JSON responses.
- **Navigate previous commands** like a python shell.
- **Modify configuration** within the REPL as you're testing.
- **Run debug mode** to see diagnostics and errors.

## Works with your favourite Python API Servers

We have specifically built and tested Clientele to be 100% compatible with OpenAPI schemas generated from:

- **FastAPI**
- **Django REST Framework** via **drf-spectacular**
- **Django Ninja**

We have working example servers in the [`server_examples/`](https://github.com/phalt/clientele/tree/main/server_examples) directory.

These examples match the code shown in our documentation and provide real, working servers you can run locally to test out Clientele.

## OpenAPI Compatibility

Clientele is compatible with OpenAPI 3.0+ schemas.

We test Clientele against 2000+ real-world OpenAPI schemas from the [APIs.guru OpenAPI Directory](https://github.com/APIs-guru/openapi-directory) through a CI cron job.

As of our latest run, we successfully generate clients for **95.39%** of schemas in the directory.

![OpenAPI Compatibility](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/phalt/clientele/main/.github/compatibility.json)

## Getting Started

👉 Read the [full documentation](https://phalt.github.io/clientele/) for all documentation.
