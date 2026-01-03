
# 📝 Usage and CLI

!!! note

    You can type `clientele COMMAND --help` at anytime to see information about the available arguments.

## OpenAPI scaffold styles

Clientele offers four styles of client generators.

### Clientele API generators

These generators will produce scaffolding that uses the [clientele API](api-overview.md):

1. **`generate-basic`** - Basic scaffolding with no generated code.
2. **`scaffold-api`** - A fully scaffolded client integration either async or sync.

### Barebones generators

Clientele can provide generated http clients that do not use [clientele API](api-overview.md) and instead provide a `http.py` package that manages most of the core http request/response logic.

!!! warning

    These options are considered deprecated from clientele version 2.0.0 and will not be supported in future versions.

1. **`generate`** - a barebones function-based client either as async or sync.
2. **`generate-class`** - a barebones class-based client either as async or sync.

## scaffold-api

The `scaffold-api` command can be used to scaffold an entire API client integration from an OpenAPI schema.

This command will generate:

- All available operations in the `operations` of the OpenAPI spec as fully typed, decorated functions.
- All available `schemas` in the `schemas` of the OpenAPI spec as Pyantic models.

```sh
clientele scaffold-api -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generated client.

```sh
clientele scaffold-api -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### From a file

Alternatively you can provide a local file using the `-f` or `--file` argument.

```sh
clientele scaffold-api -f path/to/file.json -o my_client/
```

### Async.io

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio t` to your command.

```sh
clientele scaffold-api -f path/to/file.json -o my_client/ --asyncio t
```

## generate-basic

The `generate-basic` command can be used to scaffold a basic file structure for an HTTP client.

It does not require an OpenAPI schema.

It will generate some basic imports and a sample configuration class.

This command is there for when have an HTTP API without an OpenAPI schema, but you want to keep a consistent file structure with other Clientele API clients.

```sh
clientele generate-basic -o my_client/
```

## `generate`

!!! warning

    This option is considered deprecated from clientele version 2.0.0 and will not be supported in future versions.

Generate a barebones function-based Python HTTP Client from an OpenAPI Schema.

It accepts the same arguments as `scaffold-api`.

## `generate-class`

!!! warning

    This option is considered deprecated from clientele version 2.0.0 and will not be supported in future versions.

Generate a barebones class-based Python HTTP Client from an OpenAPI Schema. 

This generator creates a `Client` class object with methods for each API endpoint instead of functions in a module.

### Usage

The `generate-class` command accepts the same arguments as `generate`:

```sh
clientele generate-class -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

It accepts the same arguments as `scaffold-api`.
