
# 📝 Usage

Clientele provides a single command, `generate`, for generating your API Clients.

## From a URL

Assuming the OpenAPI schema is available on the internet somewhere, you can query it to generate your client.

```sh
clientele generate -u https://raw.githubusercontent.com/beckett-software/clientele/main/example_openapi_specs/simple.json -o my_client/
```

!!! note

    The example above uses a test OpenAPI format, and will work if you copy/paste it!


## From a file

Alternatively, if you have a local file you can use it to generate your client.

```sh
clientele generate -f path/to/file.json -o my_client/
```

## Async Client

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio t` to your command.

```sh
clientele generate -f path/to/file.json -o my_client/ --asyncio t
```

!!! note

    You can use this command later to swap between a sync and async client so long as the OpenAPI schema remains the same, so don't worry about making a hard decision now.

## Authentication

If your OpenAPI spec provides security information for the following authentication methods:

* HTTP Bearer
* HTTP Basic

Then clientele will provide you information on the environment variables you need to set to
make this work during the generation. For example:

```sh
Please see my_client/constants.py to set authentication variables
```

The `constants.py` file will have entry points for you to configure, for example, HTTP Bearer authentication will need the `get_bearer_token` function to be updated, something like this:

```py

def get_bearer_token() -> str:
    """
    HTTP Bearer authentication.
    Used by many authentication methods - token, jwt, etc.
    Does not require the "Bearer" content, just the key as a string.
    """
    from os import environ
    return environ.get("MY_AUTHENTICATION_TOKEN")
```

## Configuration

One of the problems with auto-generated clients is that you often need to configure them, and
if you try and regenerate the client at some point (say because you've added new endpoints or fixed a bug)
then your configuration gets wiped clean and you have to do it all over again.

Clientele solves this problem by providing an entry point for configuration that will never be overwritten - `constants.py`.

When you first generate the project, you will see a file called `my_client/constants.py` (assuming your `-o` was `my_client/`), and it'll look a bit like this:

```python
"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.

DO NOT CHANGE THE FUNCTION NAMES
"""


def api_base_url() -> str:
    """
    Modify this function to provide the current api_base_url.
    """
    return "http://localhost"
```

Subsequent runs of the `generate` command will not change this file the first time is made, so you are free to modify the defaults to suit your needs, for example, if you need to source the base url of your API for different configurations, you can modify the `api_base_url` function like this:

```py

from my_project import my_config

def api_base_url() -> str:
    """
    Modify this function to provide the current api_base_url.
    """
    if my_config.debug:
        return "http://localhost:8000"
    elif my_config.production:
        return "http://my-production-url.com"
```
