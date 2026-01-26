# Change log

## 1.11.0

### GraphQLClient support

- A method for building GraphQL integrations has been introduced.
- It follows the "Clientele" pattern of the standard `APIClient`.

**Query example**:

```python
@client.query('''
    query($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            name
            stargazerCount
        }
    }
''')
def get_repo(owner: str, name: str, result: RepositoryData) -> Repository:
    return result.repository
```

**Mutation example**:

```python
@client.mutation('''
    mutation($title: String!) {
        createIssue(input: {title: $title}) {
            issue { id title }
        }
    }
''')
def create_issue(title: str, result: IssueData) -> Issue:
    return result.createIssue.issue
```

## 1.10.0

- Dropped `scaffold-api` command
- Dropped `generate-basic` command
- Drop `httpx_client` from `APIClient`
- Drop `httpx_async_client` from `APIClient`

## 1.9.2

This release includes testing tools to make API integration testing easier.

### ResponseFactory

- Added `ResponseFactory` to `clientele.testing` for quick response fixtures.
- Create common HTTP responses easily: `ok()`, `created()`, `not_found()`, `bad_request()`, `internal_server_error()`, and more.

### NetworkErrorFactory

- Added `NetworkErrorFactory` factory to `clientele.testing` for simulating network-level failures.
- Simulate common network errors like `timeout()`, `connection_refused()`, `connection_reset()`, and `dns_failure()`.
- `FakeHTTPBackend` now supports `queue_error()` to queue errors for specific paths.

## 1.9.1

- Fix streaming responses to truly yield instead of consuming the full response.
- Introduces new http_backend methods for handling streaming however the backend chooses.

## 1.9.0

### Retry support

- Built-in `retries.retry` decorator for handling retry logic.
- This is built on top of `stamina` - a popular and reliable retry package.
- The retry logic is customised to suit Clientele's exception handling.

```python
from clientele import api, retries

client = api.APIClient(api.BaseConfig(base_url="https://httpbin.org/"))

@retries.retry(attempts=3)
@client.get("/status/{status_code}")
def get_status(status_code: int, result: dict) -> dict:
    return result
```

### Improved testing

- We have drastically improved the testing support for Clientele.
- The `FakeHTTPBackend` is now designed for testing.
- The `queue_response` method now takes a `http.Response` object as well as the path.
- The new `configure_client_for_testing` function accepts an existing client and then returns it with a new testing backend.

```python
from clientele.testing import configure_client_for_testing
from clientele import http
from my_api_client import client, my_function

def my_test():
    # Swap normal backend for a Fake HTTP backend
    fake_backend: http.FakeHTTPBackend = configure_client_for_testing(my_api_client.client)

    # Configure HTTP responses
    fake_backend.queue_response(
        path="/users",
        response_obj=Response(
            status_code=201,
            content=b'{"id": 10, "name": "Bob"}',
            headers={"content-type": "application/json"},
        ),
    )

    # Call function as normal, but it now calls the fake backend
    response = my_function()

```

### Dropped `explore` command

- While it is a cool feature, it distracts from the purpose of Clientele, so it is being removed.

## 1.8.1

- Add `configure` method to `APIClient` - enabling reconfiguration of clients. Thank you [Christian Assing](https://github.com/chassing) for the contribution.

## 1.8.0

### Request Logging

- Added optional request/response logging to `APIClient` via the `logger` parameter in `BaseConfig`. Logs include method, URL, status code, and elapsed time in seconds.
- Uses a `Logger` Protocol with `@runtime_checkable` for flexibility.
- Thank you [Matías Giménez](https://github.com/justmatias) for the contribution.

### CLI commands update

- A new command `start-api` has been introduced.
- The new command will replace `scaffold-api` and `generate-basic` in 2.0.0
- Currently it behaves as an alias for both.
- If not url or file is provided, will call `generate-basic`, otherwise it calls `scaffold-api`.

Start a basic client with one command:

```sh
uvx clientele start-api -o /path/to/my_client
```

- Dropped the `generate` and `generate-class` commands from the CLI.

## 1.7.1

- Support for OpenAPI discriminated unions (`oneOf` + `discriminator`). Schemas with discriminators now generate proper Pydantic discriminated unions using `typing.Annotated[..., pydantic.Field(discriminator="...")]`.

## 1.7.0

### HTTP Backends

- Clientele now supports configurable HTTP backends.
- If you want to use `aiohttp`, `reqwests` or `niquests` you can write an `HTTPBackend` so Clientele can support it.
- Clientele ships with a default `HttpxHTTPBackend` that will be used if no other is configured.
- Introduces a new `clientele.http.Response` wrapper for generic handling of responses.
- The `response_parser` callbacks now take the generic `clientele.http.Response` instead of `httpx.Response`.
- Introduces a new `FakeHTTPBackend` that can be used for testing.

### Direct requests

- An optional approach for making requests with Clientele is now available.
- This approach does not enforce the decorator pattern.
- But still offers smart data hydration and response mapping.
- Support for both async and sync.

## 1.6.1

- `cache_backend` can now be set in the `BaseConfig`, and will be used if it is not None. This saves you having to annotate the cache backend repeatedly in decorators.

## 1.6.0

### Streaming responses

- Clientele now supports streaming responses via Server Sent Events.
- Streaming is controlled via the `streaming_response=True` parameter on all HTTP method decorators (`get`, `post`, `put`, `patch`, `delete`).
- Clientele will attempt to hydrate the response into the correct type supplied by the `result` parameter.
- `response_parser` callbacks are supported and will be applied to each streamed item.
- `response_map` is not currently supported for streaming endpoints.

```python
from typing import AsyncIterator
from pydantic import BaseModel
from clientele import api

client = api.APIClient(base_url="http://localhost:8000")

class Event(BaseModel):
    text: str

@client.get("/events", streaming_response=True)
async def stream_events(*, result: AsyncIterator[Event]) -> AsyncIterator[Event]:
    return result
```

Usage:

```python
async for event in await stream_events():
    print(event.text)
```

### Mypy support

- A mypy plugin has been added that correctly handles Clientele. You will no longer see issues for the `result` and `response` arguments. Big shout out to [Christian Assing](https://github.com/chassing) for this contribution.

### Other changes

- The `scaffold-api` command now outputs a standard `pyproject.toml` into the client directory. It will not be overwritten on subsequent regenerations.
- Big code refactor - reorganising the `request` preparation and type handling into separate files.

## 1.5.0

- Introduce `cache.memoize` decorator for sensible, http-specific caching of HTTP get requests.
- Add documentation covering common approaches to handling retry logic.

## 1.4.3

- A tiny fix with error handling and using `response_parser` with plain types.

## 1.4.2

- Fix `scaffold-api` generating post/put/patch/delete methods with a `,,` when dealing with optional args. Contributor: [@peterHoburg](https://github.com/peterHoburg).

## 1.4.1

- Correct `--regen` and `--asyncio` to be boolean flags in `scaffold-api` command. Contributor: [@peterHoburg](https://github.com/peterHoburg).
- Properly support `null` field for `anyOf` schemas in OpenAPI schema generation. They now produce `None` correctly.

## 1.4.0

- You can now pass `TypedDict` instances for the `data` parameter on `post`, `put`, `patch` and `delete` methods.
- Decorated functions now accept a `response_parser` callback that will handle the response parsing. Use this to customise the `result` value that is sent back to the function.

## 1.3.0

### Introducing **Clientele API** - a different way to think about Python API Clients

- Clientele API is a decorator-driven http client that can create elegant API integrations.
- Clientele API is considered a beta project for this release. It is an evolving idea that has been tested thoroughly and it works well in ideal conditions. Small changes to the API and usage may occur over time as we encounter unexpected scenarios.

### Generate scaffolding for OpenAPI projects with **clientele API**

- The `scaffold-api` command will produce scaffolding from an OpenAPI schema and uses the new clientele api.

### Explore APIs with **Clientele API** clients

- The `explore` command has been updated to support clients that use the clientele api pattern.

### Improved documentation

- New documentation added to cover **Clientele API**.
- Documentation sections have been reorganised to reflect the key features of Clientele.

### 2.0.0 deprecation notice

- When **clientele API** reaches maturity, support for the current "barebones" style of OpenAPI scaffolders will be deprecated.
- This will be marked as the `2.0.0` release.

## 1.2.0

- Print operation information in explorer by typing the name of the operation without parenthesis. Prints information such as the docstring, return type, and input arguments.

## 1.1.0

- Schema inspection in explore REPL has been improved. Typing a schema name without parentheses now displays the schema's docstring and fields instead of the verbose inherited Pydantic BaseModel documentation.
- Config objects now handle correctly in explore REPL. Supports old style config functions and the new style classes

## 1.0.1

- Correct package installation dependencies.

## 1.0.0

### 2025-12-27

Version 1.0.0 represents 12 months of work, planning, testing and using clientele with real APIs. It has major new features and some breaking changes. I recommend completely deleting your previous clients and rebuilding to ensure a smooth rollout.

For most of this year I've been constrained by a lack of time to build the features I have planned. With the assistance of supervised agents I have been able to build out most of what I needed, and then spent time correcting and improving the agent's code to be functionally correct.

The productivity boost has been immense and has helped me to realise the goals and ambitions I have for this project.

### Major new features

- 🆕 **Explorer CLI**: Use `clientele explore` to use a REPL and discover APIs interactively, even without writing any code.
- ⚙️ **Rebuilt configuration**: `config.py` has been re-engineered to use [pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
- 📜 **Rebuilt parser** - parsing OpenAPI schema into python objects is now handled entirely by [Cicerone](https://github.com/phalt/cicerone), our own OpenAPI parser that was built to meet our unique needs.
- Clientele now specifically offers 100% support for all major Python API frameworks: FastAPI, Django REST Framework, and Django-Ninja.
- Clientele is now tested and proven to generate clients for 2000+ openapi schemas as part of our CI. It runs weekly and we use it to ensure broad capability with all OpenAPI services.

### Clientele code generation improvements

- Fixed function parameter ordering (required parameters before optional ones).
- Nullable fields properly handled (OpenAPI 3.0 `nullable: true` and OpenAPI 3.1 array type notation)
- **Fixed**: Array responses without a `title` field now correctly generate type aliases instead of wrapper classes with a `test` property.
- **Fixed**: Responses with no content (e.g., 204 No Content) are now properly included in the status code map with `None` as the response type.
- Correctly handle reserved python keywords for schema model properties (i.e. `type`, `next` etc).
- **New**: Extended httpx configuration options in generated clients - timeout, follow_redirects, verify_ssl, http2, and max_redirects are now configurable.
- Removed the `validate` command from the CLI.
- Replaced `openapi-core` dependency with `cicerone==0.3.0` for OpenAPI schema parsing and introspection. This change provides faster, more minimal, and fully typed OpenAPI schema handling.
- **New**: Support for OpenAPI `deprecated` field - operations marked as deprecated will include deprecation warnings in generated docstrings.
- **New**: Support for OpenAPI `description` field - operation descriptions are now included in generated function docstrings for better documentation.
- Clientele is 100% typed, including the generated code, and verified using [ty](https://github.com/astral-sh/ty) instead of mypy.
- Updated all dependencies to their latest stable versions.

## 0.10.0

- **New**: Class-based client generator! Use `clientele generate-class` to generate a client with a `Client` class and methods instead of standalone functions.
- Class-based clients support both sync and async modes with `--asyncio t` flag.
- Class-based clients are perfect for object-oriented codebases and when you need to mock the client for testing.
- **New**: Dynamic configuration for class-based clients! Class-based clients now accept a `Config` object in their constructor, allowing you to create multiple clients with different configurations on the fly.
- The `config.py` file in class-based clients now generates a `Config` class instead of standalone functions, enabling runtime configuration changes.
- You can now instantiate clients with custom configuration: `client = Client(config=Config(api_base_url="https://api.example.com", bearer_token="my-token"))`.
- This addresses issues #42 and #49, enabling dynamic auth tokens and multiple clients with different configurations.
- Updated documentation with comprehensive examples of class-based client usage.
- Added `generate-class` command to CLI with full feature parity to the standard `generate` command.
- Add ABC (Abstract Base Class) pattern to generators with a `Generator` base class that all generators inherit from.
- Refactored all imports to import modules.
- **Changed**: Generated code is now auto-formatted with Ruff instead of Black.
- **Breaking change for class-based clients**: The `config.py` file structure has changed from functions to a class. Existing generated clients will need to be regenerated with `--regen t`.
- **Fixed**: OpenAPI `number` type now correctly maps to Python `float` instead of `int`. The `integer` type continues to map to `int`, and `number` with `format: "decimal"` continues to map to `decimal.Decimal`. This addresses issue #40.
- **New**: Python 3.13 and Python 3.14 support! Clientele and all generated clients now officially support Python 3.10, 3.11, 3.12, 3.13, and 3.14.
- Python 3.9 support has been dropped. If you need Python 3.9 support, please use version 0.9.0 or earlier.

## 0.9.0

- Support `patch` methods
- Fix `config.py` file being overwritten when generating new clients

## 0.8.3

- Fix bug with headers assignment

## 0.8.2

- Improved json support

## 0.8.1

- Function parameters no longer format to snake_case to maintain consistency with the OpenAPI schema.

## 0.8.0

- Improved support for Async clients which prevents a weird bug when running more than one event loop. Based on the suggestions from [this httpx issue](https://github.com/encode/httpcore/discussions/659).
- We now use [`ruff format`](https://astral.sh/blog/the-ruff-formatter) for coding formatting (not the client output).
- `Decimal` support now extends to Decimal input values.
- Input and Output schemas will now have properties that directly match those provided by the OpenAPI schema. This fixes a bug where previously, the snake-case formatting did not match up with what the API expected to send or receive.

## 0.7.1

- Support for `Decimal` types.

## 0.7.0

- Updated all files to use the templates engine.
- Generator files have been reorganised in clientele to support future templates.
- `constants.py` has been renamed to `config.py` to better reflect how it is used. It is not generated from a template like the other files.
- If you are using Python 3.10 or later, the `typing.Unions` types will generate as the short hand `|` instead.
- To regenerate a client (and to prevent accidental overrides) you must now pass `--regen t` or `-r t` to the `generate` command. This is automatically added to the line in `MANIFEST.md` to help.
- Clientele will now automatically run [black](https://black.readthedocs.io/en/stable/) code formatter once a client is generated or regenerated.
- Clientele will now generate absolute paths to refer to adjacent files in the generated client, instead of relative paths. This assumes you are running the `clientele` command in the root directory of your project.
- A lot of documentation and docs strings updates so that code in the generated client is easier to understand.
- Improved the utility for snake-casing enum keys. Tests added for the functions.
- Python 3.12 support.
- Add a "basic" client using the command `generate-basic`. This can be used to keep a consistent file structure for an API that does not use OpenAPI.

## 0.6.3

- Packaged application installs in the correct location. Resolving [#6](https://github.com/phalt/clientele/issues/6)
- Updated pyproject.toml to include a better selection of links.

## 0.6.2

- Ignore optional URL query parameters if they are `None`.

## 0.6.1

- Added `from __future__ import annotations` in files to help with typing evaluation.
- Update to use pydantic 2.4.
- A bunch of documentation and readme updates.
- Small wording and grammar fixes.

## 0.6.0

- Significantly improved handling for response schemas. Responses from API endpoints now look at the HTTP status code to pick the correct response schema to generate from the HTTP json data. When regenerating, you will notice a bit more logic generated in the `http.py` file to handle this.
- Significantly improved coverage of exceptions raised when trying to generate response schemas.
- Response types for a class are now sorted.
- Fixed a bug where `put` methods did not generate input data correctly.

## 0.5.2

- Fix pathing for `constants.py` - thanks to @matthewknight for the contribution!
- Added `CONTRIBUTORS.md`

## 0.5.1

- Support for HTTP PUT methods
- Headers objects use `exclude_unset` to avoid passing `None` values as headers, which httpx does not support.

Additionally, an async test client is now included in the test suite. It has identical tests to the standard one but uses the async client instead.

## 0.5.0

### Please delete the constants.py file when updating to this version to have new features take affect

- Paths are resolved correctly when generating clients in nested directories.
- `additional_headers()` is now applied to every client, allowing you to set up headers for all requests made by your client.
- When the client cannot match an HTTP response to a return type for the function it will now raise an `http.APIException`. This object will have the `response` attached to it for inspection by the developer.
- `MANIFEST` is now renamed to `MANIFEST.md` and will include install information for Clientele, as well as information on the command used to generate the client.

## 0.4.4

Examples and documentation now includes a very complex example schema built using [FastAPI](https://fastapi.tiangolo.com/) that offers the following variations:

- Simple request / response (no input just an output)
- A request with a URL/Path parameter.
- Models with `int`, `str`, `list`, `dict`, references to other models, enums, and `list`s of other models and enums.
- A request with query parameters.
- A response model that has optional parameters.
- An HTTP POST request that takes an input model.
- An HTTP POST request that takes path parameters and also an input model.
- An HTTP GET request that requires an HTTP header, and returns it.
- An HTTP GET endpoint that returns the HTTP bearer authorization token (also makes clientele generate the http authentication for this schema).

A huge test suite has been added to the CI pipeline for this project using a copy of the generated client from the schema above.

## 0.4.3

- `Enums` now inherit from `str` as well so that they serialize to JSON properly. See [this little nugget](https://hultner.se/quickbits/2018-03-12-python-json-serializable-enum.html).

## 0.4.2

- Correctly use `model_rebuild` for complex schemas where there are nested schemas, his may be necessary when one of the annotations is a ForwardRef which could not be resolved during the initial attempt to build the schema.
- Do not raise for status, instead attempt to return the response if it cannot match a response type.

## 0.4.1

- Correctly generate lists of nested schema classes
- Correctly build response schemas that are emphemeral (such as when they just return an array of other schemas, or when they have no $ref).

## 0.4.0

- Change install suggestion to use [pipx](https://github.com/pypa/pipx) as it works best as a global CLI tool.
- Improved support for OpenAPI 3.0.3 schemas (a test version is available in the example_openapi_specs directory).
- `validate` command for validating an OpenAPI schema will work with clientele.
- `version` command for showing the current version of clientele.
- Supports HTTP DELETE methods.
- Big refactor of how methods are generated to reduce duplicate code.
- Support optional header parameters in all request functions (where they are required).
- Very simple Oauth2 support - if it is discovered will set up HTTP Bearer auth for you.
- Uses `dict` and `list` instead of `typing.Dict` and `typing.List` respectively.
- Improved schema generation when schemas have $ref to other models.

## 0.3.2

- Minor changes to function name generation to make it more consistent.
- Optional parameters in schemas are working properly.

## 0.3.1

- Fixes a bug when generating HTTP Authentication schema.
- Fixes a bug when generating input classes for post functions, when the input schema doesn't exist yet.
- Generates pythonic function names in clients now, always (like `lower_case_snake_case`).

## 0.3.0

- Now generates a `MANIFEST` file with information about the build versions
- Added a `constants.py` file to the output if one does not exist yet, which can be used to store values that you do not want to change between subsequent re-generations of the clientele client, such as the API base url.
- Authentication patterns now use `constants.py` for constants values.
- Removed `ipython` from package dependencies and moved to dev dependencies.
- Documentation! [https://phalt.github.io/clientele/](https://phalt.github.io/clientele/)

## 0.2.0

- Improved CLI output
- Code organisation is now sensible and not just one giant file
- Now supports an openapi spec generated from a dotnet project (`Microsoft.OpenApi.Models`)
- async client support fully working
- HTTP Bearer support
- HTTP Basic support

## 0.1.0

- Initial version
- Mostly works with a simple FastAPI generated spec (3.0.2)
- Works with Twilio's spec (see example_openapi_specs/ directory) (3.0.1)
- Almost works with stripes
