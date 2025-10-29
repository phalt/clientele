
# 📝 Use Clientele

!!! note

    You can type `clientele COMMAND --help` at anytime to see explicit information about the available arguments.

## Client Types

Clientele offers three types of client generators:

1. **`generate`** - Standard function-based client (recommended for most use cases)
2. **`generate-class`** - Class-based client with methods
3. **`generate-basic`** - Basic file structure with no generated code

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

## `generate-class`

Generate a class-based Python HTTP Client from an OpenAPI Schema. This generator creates a `Client` class with methods for each API endpoint.

### Usage

The `generate-class` command accepts the same arguments as `generate`:

```sh
clientele generate-class -u https://raw.githubusercontent.com/phalt/clientele/main/example_openapi_specs/best.json -o my_client/
```

### Example Usage

With a class-based client, you instantiate the `Client` class and call methods:

```python
from my_client.client import Client
from my_client import schemas

# Create a client instance
client = Client()

# Call API methods
data = schemas.RequestDataRequest(my_input="test")
response = client.request_data_request_data_post(data=data)

# Handle responses
match response:
    case schemas.RequestDataResponse():
        print(f"Success: {response}")
    case schemas.ValidationError():
        print(f"Validation error: {response}")
```

### Async Class-Based Client

You can generate an async class-based client as well:

```sh
clientele generate-class -f path/to/file.json -o my_client/ --asyncio t
```

Then use it with async/await:

```python
from my_async_client.client import Client

client = Client()
response = await client.simple_request_simple_request_get()
```

### When to Use Class-Based Clients

Use class-based clients when:

- You prefer object-oriented programming style
- You want to easily mock the client for testing
- You need to maintain state or configuration in the client instance
- You want to subclass and extend the client behavior

Use function-based clients (`generate`) when:

- You prefer functional programming style
- You want the simplest possible client with no boilerplate
- You don't need to maintain state between requests

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
Clientele 0.9.0
```
