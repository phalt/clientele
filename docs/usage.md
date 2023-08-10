
# 📝 Commands

## Validate

Validate lets you check if an OpenAPI schema will work with clientele. Some OpenAPI schema generators do not comply properly with the specification and it is a good way to check if your schema is correct.

```sh
clientele validate -u http://path.com/to/openapi.json
```

Alternatively you can provide a local file:

```sh
clientele validate -f /path/to/openapi.json
```

## Generate

### From a URL

Assuming the OpenAPI schema is available on the internet somewhere, you can query it to generate your client.

```sh
clientele generate -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

!!! note

    The example above uses a test OpenAPI format, and will work if you copy/paste it!

### From a file

Alternatively, if you have a local file you can use it to generate your client.

```sh
clientele generate -f path/to/file.json -o my_client/
```

### Async Client

If you prefer an [asyncio](https://docs.python.org/3/library/asyncio.html) client, just pass `--asyncio t` to your command.

```sh
clientele generate -f path/to/file.json -o my_client/ --asyncio t
```

!!! note

    You can use this command later to swap between a sync and async client so long as the OpenAPI schema remains the same, so don't worry about making a hard decision now.
