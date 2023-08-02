# 🪄 Client example

Let's build an API Client using clientele and an example OpenAPI schema.

Our [GitHub](https://github.com/phalt/clientele/tree/main/example_openapi_specs) has a bunch of schemas that are proven to work with clientele, so let's use one of those!

## Generate the client

Very simply:

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/simple.json -o my_client/
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

## Client directory

Let's go over each file and talk about what it does

### client.py

This file provides all the client functions.

```py title="my_client/client.py" linenums="1"
import typing  # noqa
from . import schemas  # noqa
from . import http  # noqa


def HealthCheckHealthCheckGet() -> schemas.HealthCheckResponse:
    response = http.get("/health-check")
    return http.handle_response(HealthCheckHealthCheckGet, response)


def TestInputTestInputPost(
    data: schemas.TestInputData,
) -> typing.Union[schemas.HTTPValidationError, schemas.TestInputResponse]:
    response = http.post("/test-input", data=data and data.model_dump())
    return http.handle_response(TestInputTestInputPost, response) 
```

We can see one of the functions here, `HealthCheckHealthCheckGet`, is for a straight-forward HTTP GET request without any input arguments, and it returns a schema object. If the endpoint has url parameters or query parameters, they will appear as input arguments to the function.

```py
def HealthCheckHealthCheckGet() -> schemas.HealthCheckResponse:
    response = http.get("/health-check")
    return http.handle_response(HealthCheckHealthCheckGet, response)
```

Here is how you might use it:

```py
from my_client import client

client.HealthCheckHealthCheckGet()
>>> HealthCheckResponse(status='ok')
```

A more complex example is shown just below - `TestInputTestInputPost`, this is for an HTTP POST method, and it requires an input property called `data` that is an instance of a schema, and returns a union of responses. If the endpoint has url parameters or query parameters, they will appear as input arguments to the function alongside the `data` argument.

```py
def TestInputTestInputPost(
    data: schemas.TestInputData,
) -> typing.Union[schemas.HTTPValidationError, schemas.TestInputResponse]:
    response = http.post("/test-input", data=data and data.model_dump())
    return http.handle_response(TestInputTestInputPost, response) 
```

Here is how you might use it:

```py
from my_client import client, schemas

data = schemas.TestInputData(my_title="Hello, world")
client.TestInputTestInputPost(data=data)
>>> TestInputResponse(title='Hello, world')
```

Because we're using Pydantic to manage the input data, we get a strongly-typed interface for us.

### schemas.py

This file has all the possible schemas, request and response, for the API.

They are all subclassed from pydantic's `BaseModel`. Here are a few examples:

```py title="my_client/schemas.py" linenums="1"
import typing  # noqa
from pydantic import BaseModel  # noqa
from enum import Enum  # noqa


class HTTPValidationError(BaseModel):
    detail: list[typing.Any]


class HealthCheckResponse(BaseModel):
    status: str


class TestInputData(BaseModel):
    my_title: str


class TestInputResponse(BaseModel):
    title: str


class ValidationError(BaseModel):
    loc: list[typing.Any]
    msg: str
    type: str

```

### http.py

This file manages the HTTP layer of the client.

You should never need to touch the code here, but feel free to have a browse.

This file will have either a sync, or an async instance of a client from `httpx`.

It also manages the coersion of response bodies into schema objects.

### constants.py

This manages all the configuration your client might need.

This file is only ever generated once, and will never be overwritten (unless you delete it yourself).

You can modify the contents of the functions in this file to provide things like the base url and authentication keys for your client.

### MANIFEST

The `MANIFEST` file provides some information on how the client was generated.
