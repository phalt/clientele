# Change log

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
- To regenerate a client (and to prevent accidental overrides) you must now pass `--regen t` or `-r t` to the `generate` command. This is automatically added to the line in `MANIFEST.md` to  help.
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
- async client support  fully working
- HTTP Bearer support
- HTTP Basic support

## 0.1.0

- Initial version
- Mostly works with a simple FastAPI generated spec (3.0.2)
- Works with Twilio's spec (see example_openapi_specs/ directory) (3.0.1)
- Almost works with stripes
