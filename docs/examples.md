# 🪄 Client example

Let's build an API Client using clientele and an example OpenAPI schema.

Our [GitHub](https://github.com/phalt/clientele/tree/main/example_openapi_specs) has a bunch of schemas that are proven to work with clientele, so let's use one of those!

## Generate the client

Simply:

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

The `-u` parameter expects a URL, you can provide a path to a file with `-f` instead if you download the file.

The `-o` parameter is the output directory of the generated client.

Run it now and you will see this output:

```sh
my_client/
    __init__.py
    client.py
    constants.py
    http.py
    MANIFEST
    schemas.py
```

## Client

Let's go over each file and talk about what it does

### GET functions

The `client.py` file provides all the API functions from the OpenAPI schema.

```py title="my_client/client.py" linenums="1"
import typing  # noqa
from . import schemas  # noqa
from . import http  # noqa


def simple_request_simple_request_get() -> schemas.SimpleResponse:
    """Simple Request"""

    response = http.get(url="/simple-request")
    return http.handle_response(simple_request_simple_request_get, response)

...
```

We can see one of the functions here, `simple_request_simple_request_get`, is for a straight-forward HTTP GET request without any input arguments, and it returns a schema object.

Here is how you might use it:

```py
from my_client import client

client.simple_request_simple_request_get()
>>> SimpleResponse(name='Paul')
```

#### URL and Query parameters

If your endpoint takes [path parameters](https://learn.openapis.org/specification/parameters.html#parameter-location) (aka URL parameters) then clientele will turn them into parameters in the function:

```py
from my_client import client

client.parameter_request_simple_request(your_input="gibberish")
>>> ParameterResponse(your_input='gibberish')
```

Query parameters will also be generated the same way. See [this example](https://github.com/phalt/clientele/blob/0.4.4/tests/test_client/client.py#L71) for a function that takes a required query parameter.

### POST functions

A more complex example is shown just below. This is for an HTTP POST method, and it requires an input property called `data` that is an instance of a schema, and returns a union of responses. If the endpoint has url parameters or query parameters, they will appear as input arguments to the function alongside the `data` argument.

```py
def request_data_request_data_post(
    data: schemas.RequestDataRequest,
) -> typing.Union[schemas.RequestDataResponse, schemas.HTTPValidationError]:
    """Request Data"""

    response = http.post(url="/request-data", data=data.model_dump())
    return http.handle_response(request_data_request_data_post, response)
```

Here is how you might use it:

```py
from my_client import client, schemas

data = schemas.RequestDataRequest(my_input="Hello, world")
response = client.request_data_request_data_post(data=data)
>>> RequestDataResponse(your_input='Hello, world')
```

Because we're using Pydantic to manage the input data, we get a strongly-typed response object.
This works beautifully with the new [structural pattern matching](https://peps.python.org/pep-0636/) feature in Python 3.10:

```py

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

## Schemas

The `schemas.py` file has all the possible schemas, request and response, and even Enums, for the API.

They are all subclassed from pydantic's `BaseModel`. Here are a few examples:

```py title="my_client/schemas.py" linenums="1"
import typing  # noqa
import pydantic  # noqa
from enum import Enum  # noqa


class ParameterResponse(pydantic.BaseModel):
    your_input: str

class RequestDataRequest(pydantic.BaseModel):
    my_input: str

class RequestDataResponse(pydantic.BaseModel):
    my_input: str

# Enums subclass str so they serialize to JSON nicely
class ExampleEnum(str, Enum):
    ONE = "ONE"
    TWO = "TWO"
```

## Configuration

One of the problems with auto-generated clients is that you often need to configure them, and
if you try and regenerate the client at some point then your configuration gets wiped clean and you have to do it all over again.

Clientele solves this problem by providing an entry point for configuration that will never be overwritten - `constants.py`.

When you first generate the project, you will see a file called `constants.py` and it will offer configuration functions a bit like this:

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

Just keep the function names the same and you're good to go.

### Authentication

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
