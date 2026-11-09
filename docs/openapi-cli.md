
# 🏗️ Client creator

Clientele can build a project template for an API Client.

It can also generate functions and models from an OpenAPI schema.

## Basic project template

To create a new clientele API client project just use the `start-api` command:

```sh
uv run clientele start-api -o path/to/my_client
```

![clientele start-api creating a basic API client project](clientele_start_api_basic.svg)

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

![clientele start-api generating a typed API client from an OpenAPI schema](clientele_start_api.svg)

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

### Environment variable prefix

The generated `Config` in `config.py` reads its settings from environment variables and `.env`, prefixed with the output directory's name in upper case. For `-o billing_client/` that's `BILLING_CLIENT_BASE_URL`, `BILLING_CLIENT_TIMEOUT`, `BILLING_CLIENT_HEADERS` and so on, so two clients in one app don't share settings, and generic names like `TIMEOUT` don't collide with your app's own.

Use `--env-prefix` to pick a different prefix, or pass `""` to read the unprefixed names (`BASE_URL`, `TIMEOUT`, ...):

```sh
clientele start-api -f path/to/file.json -o billing_client/ --env-prefix BILLING_
```

The prefix is only used when `config.py` is created. `config.py` is never overwritten, so `--regen` keeps the prefix (or no prefix) your existing `config.py` has. To change it, edit `model_config = SettingsConfigDict(env_prefix=...)` in `config.py`.

### Model base class

Generated models subclass `pydantic.BaseModel`. To give them a shared base, for an app-wide `model_config` such as `extra="forbid"`, `frozen=True` or an `alias_generator`, pass a dotted path to your own `pydantic.BaseModel` subclass with `--base-class`:

```python
# my_app/models.py
import pydantic


class Base(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)
```

```sh
clientele start-api -f path/to/file.json -o my_client/ --base-class my_app.models.Base
```

`schemas.py` then imports it as `from my_app.models import Base as _ClienteleBase` and every generated model, including request, response and header models, subclasses it. Enums and list models (`ListResponse`) are unchanged. A model's own `model_config` (e.g. `populate_by_name=True, serialize_by_alias=True` on models with aliased fields) is merged over the base's.

The path is checked for its format but not imported when generating, so the class only has to be importable where the client runs. The option is recorded in `MANIFEST.md`, so the regen command there keeps it. Response models are validated with the base's config too, so `extra="forbid"` makes a response with a field the spec doesn't list fail validation.

### Regenerating

When your API changes, run the same command again with `-r` or `--regen` to update the client in place. Without it, clientele won't overwrite an existing client and will warn you instead. The exact command is also written into your client's `MANIFEST.md`.

```sh
clientele start-api -f path/to/file.json -o my_client/ --regen
```

Then review the git diff before you ship it. Here a new `/widgets/{widget_id}` endpoint was added to the schema:

![clientele regenerating a client and git diff showing the new function and model](clientele_regen.svg)
