<p align="center">
    <h1>⚜️ Clientele</h1>
    <em>Typed API Clients from OpenAPI schemas</em>
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
