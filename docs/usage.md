
# 📝 Use Clientele

!!! note

    You can type `clientele COMMAND --help` at anytime to see explicit information about the available arguments.

## `generate`

Generate a Python HTTP Client from an OpenAPI Schema.

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generate client.

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

!!! note

    The example above uses one of our test schemas, and will work if you copy/paste it!

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

### Regenerating

At times you may wish to regenerate the client. This could be because the API has updated or you just want to use a newer version of clientele.

To force a regeneration you must pass the `--regen` or `-r` argument, for example:

```sh
clientele generate -f example_openapi_specs/best.json -o my_client/  --regen t
```

!!! note

    You can copy and paste the command from the `MANIFEST.md` file in your previously-generated client for a quick and easy regeneration.

## `validate`

Validate lets you check if an OpenAPI schema will work with clientele.

!!! note

    Some OpenAPI schema generators do not conform to the [specification](https://spec.openapis.org/oas/v3.1.0).

    Clientele uses [openapi-core](https://openapi-core.readthedocs.io/en/latest/) to validate the schema.

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generate client.

```sh
clientele validate -u http://path.com/to/openapi.json
```

### From a file path

Alternatively you can provide a local file using the `-f` or `--file` argument.

```sh
clientele validate -f /path/to/openapi.json
```

## generate-basic

The `generate-basic` command can be used to generate a basic file structure for an HTTP client.

It does not required an OpenAPI schema, just a path.

This command serves two reasons:

1. You may have an HTTP API without an OpenAPI schema and you want to keep a consistent file structure with other Clientele clients.
2. The generator for this basic client can be extended for your own client in the future, if you choose.

```sh
clientele generate-basic -o my_client/
```

## `version`

Print the current version of Clientele:

```sh
> clientele version
Clientele 0.8.2
```
