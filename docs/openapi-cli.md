
# 🏗️ Client creator

Clientele can build a project template for an API Client.

It can also generate functions and models from an OpenAPI schema.

## Basic project template

To create a new clientele API client project just use the `start-api` command:

```sh
uv run clientele start-api -o path/to/my_client
```

This will create a new directory with the following file stucture:

```sh
my_client/
    config.py.  # Client configuration
    client.py   # API client functions
    schemas.py  # API models
    MANIFEST.md # Information about the project
```

The only code within these files will be a simple configuration set up and some basic imports.

## OpenAPI project template

The `start-api` command can also be used to scaffold an entire API client integration using an OpenAPI schema.

If you provide a schema then the `start-api` command will generate the same project structure and it will also include:

- All available operations in the `operations` of the OpenAPI spec as fully typed, decorated functions.
- All available models in the `schemas` of the OpenAPI spec as Pyantic models.

```sh
clientele start-api -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generated client.

```sh
clientele start-api -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### From a file

Alternatively you can provide a local file using the `-f` or `--file` argument.

```sh
clientele start-api -f path/to/file.json -o my_client/
```

### Async.io

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio` to your command.

```sh
clientele start-api -f path/to/file.json -o my_client/ --asyncio
```

## Generated code

### Enums

OpenAPI `enum` schemas are generated as Python `enum` classes in `schemas.py`. The base class is chosen from the member values:

| Enum values | Generated base class | Member naming |
| ----------- | -------------------- | ------------- |
| All strings | `str, enum.Enum` | Upper-cased value, e.g. `RED = "red"` |
| All integers | `enum.IntEnum` | `VALUE_<n>`, e.g. `VALUE_1 = 1` |
| Numbers or mixed types | `enum.Enum` | Strings as above, others `VALUE_<n>` |

For example, this schema:

```json
{
  "StatusCode": { "type": "integer", "enum": [1, 2, 3] },
  "Colour": { "type": "string", "enum": ["red", "green"] }
}
```

Generates:

```python
class StatusCode(enum.IntEnum):
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3


class Colour(str, enum.Enum):
    RED = "red"
    GREEN = "green"
```

Negative numbers use `MINUS_` (`VALUE_MINUS_12 = -12`) and decimal points become underscores (`VALUE_0_5 = 0.5`). If two values sanitise to the same member name, later members get a numeric suffix (`YES = "YES"`, `YES_2 = "yes"`).

### Map types (additionalProperties)

Object schemas with a schema-valued `additionalProperties` describe maps — objects whose values all match one schema, such as error maps or translations. These are generated as typed dictionaries.

A map-valued property generates a typed `dict`:

```json
{
  "Report": {
    "type": "object",
    "properties": {
      "scores": {
        "type": "object",
        "additionalProperties": { "type": "integer" }
      }
    }
  }
}
```

```python
class Report(pydantic.BaseModel):
    scores: typing.Optional[dict[str, int]] = None
```

A component schema that is purely a map (no `properties` of its own) generates a `DictResponse` class — a real type that validates its values and can be used in `response_map`, with dict-style access:

```json
{
  "ErrorMap": {
    "type": "object",
    "additionalProperties": { "$ref": "#/components/schemas/Error" }
  }
}
```

```python
class ErrorMap(DictResponse[Error]):
    pass
```

```python
errors = schemas.ErrorMap.model_validate({"email": {"message": "invalid"}})
errors["email"].message  # "invalid"
len(errors), errors.keys(), errors.items()  # dict-style access
```

Objects with `additionalProperties: true`, `{}`, or no `additionalProperties` at all keep the untyped `dict[str, typing.Any]` behaviour, and objects that declare their own `properties` are generated as regular models.
