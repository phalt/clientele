
# 📝 Use Clientele

!!! note

    You can type `clientele COMMAND --help` at anytime to see information about the available arguments.

## Client Types

Clientele offers five types of generators:

1. **`generate`** - a function-based client either as async or sync.
2. **`generate-class`** - a class-based client either as async or sync.
3. **`generate-basic`** - Basic file structure with no generated code.

## `generate`

Generate a function-based Python HTTP Client from an OpenAPI Schema.

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generated client.

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### From a file

Alternatively you can provide a local file using the `-f` or `--file` argument.

```sh
clientele generate -f path/to/file.json -o my_client/
```

### Async.io

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio t` to your command.

```sh
clientele generate -f path/to/file.json -o my_client/ --asyncio t
```

## `generate-class`

Generate a class-based Python HTTP Client from an OpenAPI Schema. This generator creates a `Client` class object with methods for each API endpoint instead of functions in a module.

### Usage

The `generate-class` command accepts the same arguments as `generate`:

```sh
clientele generate-class -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

## generate-basic

The `generate-basic` command can be used to generate a basic file structure for an HTTP client.

It does not require an OpenAPI schema. It does not generate any code.

This command is there for when have an HTTP API without an OpenAPI schema, but you want to keep a consistent file structure with other Clientele clients.

```sh
clientele generate-basic -o my_client/
```

## Functional vs Class

Use function-based clients (`generate`) when:

- You prefer a functional programming style.
- You want the simplest possible client.
- You don't need to maintain state between requests.
- You only need a single static configuration.

Use class-based (`generate-class`) clients when:

- You prefer an object-oriented programming style.
- You need to maintain state or configuration in the client instance.
- You want to subclass and extend the client behavior.
- You need dynamic configuration or multiple clients with different settings.

## `explore`

Run the explorer mode. See [explore](explore.md).

## `version`

Print the current version of Clientele:

    ```sh
    > clientele version
    Clientele 1.2.0
    ```
