# ⚜️ Clientele

## Generate loveable Python HTTP API Clients

[![Package version](https://img.shields.io/pypi/v/clientele?color=%2334D058&label=latest%20version)](https://pypi.org/project/clientele)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/clientele?label=python%20support)
![PyPI - Downloads](https://img.shields.io/pypi/dm/clientele)
![PyPI - License](https://img.shields.io/pypi/l/clientele)

Clientele lets you generate fully-typed, pythonic HTTP API Clients using an OpenAPI schema.

It's easy to use:

```sh
# Install as a global tool - it's not a dependency!
pipx install clientele
# Generate a client
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o api_client/
```

## Generated code

The generated code is designed by python developers, for python developers.

It uses modern tooling and has a great developer experience.

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

The generated code is tiny - the [example schema](https://github.com/phalt/clientele/blob/main/example_openapi_specs/best.json) we use for documentation and testing only requires [250 lines of code](https://github.com/phalt/clientele/tree/main/tests/test_client) and 5 files.

## Async support

You can choose to generate either a sync or an async client - we support both:

```py
from my_async_api import client

# Async client functions
response = await client.simple_request_simple_request_get()
```

## Other features

* Written entirely in Python.
* Designed to work with [FastAPI](https://fastapi.tiangolo.com/)'s and [drf-spectacular](https://github.com/tfranzel/drf-spectacular)'s OpenAPI schema generator.
* The generated client only depends on [httpx](https://www.python-httpx.org/) and [Pydantic 2.4](https://docs.pydantic.dev/latest/).
* HTTP Basic and HTTP Bearer authentication support.
* Support your own configuration - we provide an entry point that will never be overwritten.
* Designed for easy testing with [respx](https://lundberg.github.io/respx/).
* API updated? Just run the same command again and check the git diff.
* Automatically formats the generated client with [black](https://black.readthedocs.io/en/stable/index.html).
