# ⚜️ Clientele

# Typed API Clients from OpenAPI schemas

![clientele_logo](https://github.com/beckett-software/clientele/blob/main/docs/clientele.jpeg?raw=true)

Clientele lets you generate fully-typed, functional, API Clients from OpenAPI schemas.

It uses modern tools to be blazing fast and type safe.

Plus - there is no complex boilerplate and the generated code is very small.

## Features

* Fully typed API Client using Pydantic.
* Minimalist and easy to use - the generated code is designed for readability.
* Choose either sync or async - we support both, and you can switch between them easily.
* Supports authentication (curently only HTTP Bearer and HTTP Basic auth).
* Written entirely in Python - no need to install other languages to use OpenAPI.
* The client footprint is minimal - it only requires `httpx` and `pydantic`.
* Supports your own configuration - we provide an entry point that will never be overwritten.

We're built on:

* [Pydantic 2.0](https://docs.pydantic.dev/latest/)
* [httpx](https://www.python-httpx.org/)
* [openapi-core](https://openapi-core.readthedocs.io/en/latest/)

## Install

```sh
poetry add clientele
```

## Usage

```sh
clientele generate -f path/to/file.json -o my_client/ --asyncio t
```

[Read the docs](https://beckett-software.github.io/clientele/)
