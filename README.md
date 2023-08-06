<p align="center">
    <h1>⚜️ Clientele</h1>
    <em>Loveable API Clients from OpenAPI schemas</em>
    <img src="https://github.com/phalt/clientele/blob/main/docs/clientele.jpeg?raw=true">
</p>

<p align="center">
<a href="https://pypi.org/project/clientele" target="_blank">
    <img src="https://img.shields.io/pypi/v/clientele?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/clientele" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/clientele.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

Clientele lets you generate fully-typed, loveable Python API Clients from OpenAPI schemas:

```py
from my_api import client, schemas

# Pydantic-typed inputs
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

The generated code is tiny - the [example schema](https://github.com/phalt/clientele/blob/0.4.4/example_openapi_specs/best.json) we use for documentation and testing only requires [250 lines of code](https://github.com/phalt/clientele/tree/0.4.4/tests/test_client) and 5 files.

Choose either sync or async - we support both, and you can switch between them easily:

```py
from my_async_api import client

# Async client functions
response = await client.simple_request_simple_request_get()
```

All generated from a single command:

```sh
# add -asyncio -t to make it async
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o api_client/
```

(That works - try it now!)

## Other features

* Supports authentication automatically (curently only HTTP Bearer and HTTP Basic auth).
* Written entirely in Python - no need to install any other languages.
* The client footprint only requires `httpx` and `pydantic`.
* Support your own configuration - we provide an entry point that will never be overwritten.
* Designed for easy testing with [respx](https://lundberg.github.io/respx/).

We're built on:

* [Pydantic 2.0](https://docs.pydantic.dev/latest/)
* [httpx](https://www.python-httpx.org/)
* [openapi-core](https://openapi-core.readthedocs.io/en/latest/)
