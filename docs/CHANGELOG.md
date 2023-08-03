# Change log

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
