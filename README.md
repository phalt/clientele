#  ⚜️ Clientele

### Typed API Clients from OpenAPI specs

![clientele_logo](https://github.com/beckett-software/clientele/blob/main/docs/clientele.jpeg?raw=true)

Clientele lets you generate fully-typed, functional, API Clients from OpenAPI specs.

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
poetry add clientele
```

## Usage

### From URLs

```sh
clientele generate -u URL_TO_OPEN_API.json -o output/
```

### From files

```sh
clientele generate -f path/to/file.json -o output/
```

### Async Client

```sh
clientele generate -f path/to/file.json -o output/ --async t
```