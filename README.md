#  ⚜️ Beckett-API

### Typed API Clients from OpenAPI specs

![beckett_api_logo](https://github.com/beckett-software/beckett-api/blob/main/docs/beckett_api.jpeg?raw=true)

Beckett-API lets you generate fully-typed, functional, API Clients from OpenAPI specs.

It uses modern tools to be blazing fast and type safe. 

Plus - there is no complex boilerplate and the generated code is very small.

## Features

* Fully typed API Client using Pydantic.
* Minimalist and easy to use - the generated code is tiny.
* Choose either sync (default) or async - we support both.
* Written entirely in Python - no need to install other languages to use OpenAPI.

We're built on:

* [Pydantic 2.0](https://docs.pydantic.dev/latest/)
* [httpx](https://www.python-httpx.org/)
* [openapi-core](https://openapi-core.readthedocs.io/en/latest/)

## Install

```sh
poetry add beckett-api
```

## Use

```sh
beckett-api generate -u URL_TO_OPEN_API.json -o output/ --async t
```

Inspect the `output/` folder when it has finished to see your new API client!