#  Beckett-API

## Typed Python OpenAPI Clients

Beckett-API lets you generate fully-typed, minimalist API Clients from OpenAPI specs.

It uses modern tools to be blazing fast and type safe.

## Features

* Fully typed API Client using Pydantic.
* Minimalist and easy to use - the generated code is tiny.
* Choose either sync (default) or async - we support both.

We're built on:

* Pydantic 2.0
* httpx
* openapi-core

## Install

```sh
poetry add beckett-api
```

## Use

```sh
beckett-api generate -u URL_TO_OPEN_API.json -o output/ --async t
```

Inspect the `output/` folder when it has finished to see your new API client!