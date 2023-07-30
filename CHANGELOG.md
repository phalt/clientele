# Change log

## 0.4.0 NOT YET RELEASED

- Use [pydantic settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/) for settings management in the `constants.py` file. This is a **breaking change** and you will need to delete your `constants.py` file.

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
- Documentation! [https://beckett-software.github.io/clientele/](https://beckett-software.github.io/clientele/)

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
