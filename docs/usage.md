
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

`-o` or `--output` is the target directory for the generated client.

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

# Create a client instance with default configuration
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

### Dynamic Configuration

Class-based clients support dynamic configuration, allowing you to create multiple clients with different settings:

```python
from my_client.client import Client
from my_client import config

# Create a client with custom configuration
custom_config = config.Config(
    api_base_url="https://api.example.com",
    bearer_token="my-auth-token",
    additional_headers={"X-Custom-Header": "value"}
)
client = Client(config=custom_config)

# Create multiple clients with different configurations
prod_config = config.Config(
    api_base_url="https://api.production.com",
    bearer_token="prod-token"
)
dev_config = config.Config(
    api_base_url="https://api.development.com",
    bearer_token="dev-token"
)

prod_client = Client(config=prod_config)
dev_client = Client(config=dev_config)

# Each client uses its own configuration
prod_response = prod_client.get_data()
dev_response = dev_client.get_data()
```

The `Config` class supports the following parameters:

- `api_base_url`: Base URL for the API (default: `"http://localhost"`)
- `additional_headers`: Additional headers to include in all requests (default: `{}`)
- `user_key`: Username for HTTP Basic authentication (default: `"user"`)
- `pass_key`: Password for HTTP Basic authentication (default: `"password"`)
- `bearer_token`: Token for HTTP Bearer authentication (default: `"token"`)

This makes it easy to:
- Switch between different API environments (dev, staging, production)
- Use different authentication tokens for different users or sessions
- Add custom headers per client instance
- Test your code with mock configurations

### Async Class-Based Client

You can generate an async class-based client as well:

```sh
clientele generate-class -f path/to/file.json -o my_client/ --asyncio t
```

Then use it with async/await:

```python
from my_async_client.client import Client
from my_async_client import config

# With default configuration
client = Client()
response = await client.simple_request_simple_request_get()

# With custom configuration
custom_config = config.Config(api_base_url="https://api.example.com")
client = Client(config=custom_config)
response = await client.simple_request_simple_request_get()
```

### When to Use Class-Based Clients

Use class-based clients when:

- You prefer object-oriented programming style
- You want to easily mock the client for testing
- You need to maintain state or configuration in the client instance
- You want to subclass and extend the client behavior
- **You need dynamic configuration or multiple clients with different settings**

Use function-based clients (`generate`) when:

- You prefer functional programming style
- You want the simplest possible client with no boilerplate
- You don't need to maintain state between requests
- You only need a single static configuration

## `validate`

Validate lets you check if an OpenAPI schema will work with clientele.

!!! note

    Some OpenAPI schema generators do not conform to the [specification](https://spec.openapis.org/oas/v3.1.0).

    Clientele uses [openapi-core](https://openapi-core.readthedocs.io/en/latest/) to validate the schema.

### From a URL

Use the `-u` or `--url` argument.

`-o` or `--output` is the target directory for the generated client.

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

It does not require an OpenAPI schema, just a path.

This command serves two purposes:

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

## `explore`

The `explore` command launches an **interactive REPL** (Read-Eval-Print Loop) that lets you explore and test API operations without writing any code. It's perfect for API discovery, testing, and debugging.

### Usage Modes

#### Explore an Existing Client

If you've already generated a client, you can explore it directly:

```sh
clientele explore -o pokeapi_client/
```

This loads the generated client and discovers all available operations.

#### Explore from a Schema File

Generate a temporary client and explore it in one command:

```sh
clientele explore -f pokeapi_openapi.yml
```

Clientele will:
1. Generate a temporary client from the schema
2. Load it into the REPL
3. Clean up the temporary files when you exit

#### Explore from a Schema URL

You can also explore directly from a URL:

```sh
clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
```

This is great for quickly testing remote APIs without saving the client locally.

### Interactive Features

Once inside the REPL, you have access to several powerful features:

#### Tab Autocomplete

Press **TAB** to autocomplete:

- **Operation names** - See all available API operations
- **Parameter names** - Get suggestions for function parameters
- **Type hints** - View parameter types and whether they're required

```
>>> pokemon_  <TAB>
pokemon_list                 pokemon_read
pokemon_encounter_list       pokemon_form_list

>>> pokemon_list(  <TAB>
limit=    (int, optional)
offset=   (int, optional)
q=        (str, optional)
```

#### Execute Operations

Call API operations using Python-like syntax:

```python
# Simple operation with no parameters
>>> ability_list()

# Operation with parameters
>>> pokemon_list(limit=5, offset=0)

# Operation with a specific ID
>>> pokemon_read(id="pikachu")
```

The REPL will:
- Validate your arguments against the operation signature
- Execute the API call
- Display timing information
- Format the response with syntax highlighting

#### Special Commands

Commands starting with `.` provide additional functionality:

**`/list`** or **`/operations`** - List all available operations in a table:

```
>>> /list
Available Operations
┌──────────────────────────────┬────────┬─────────────────────────────┐
│ Operation                    │ Method │ Description                 │
├──────────────────────────────┼────────┼─────────────────────────────┤
│ ability_list                 │ GET    │ List abilities              │
│ ability_read                 │ GET    │ Get ability by ID or name   │
│ pokemon_list                 │ GET    │ List pokemon                │
│ pokemon_read                 │ GET    │ Get pokemon by ID or name   │
│ berry_list                   │ GET    │ List berries                │
│ move_list                    │ GET    │ List moves                  │
└──────────────────────────────┴────────┴─────────────────────────────┘

Total: 6 operations
```

**`/help`** - Show help message with usage information:

```
>>> /help

Clientele Interactive API Explorer

Usage:
  • Type operation names and press TAB to autocomplete
  • Execute operations with Python-like syntax: operation_name(param=value)
  • Use UP/DOWN arrows to navigate command history

Special Commands:
  /list, /operations  - List all available operations
  /help                  - Show this help message
  /exit, /quit         - Exit the REPL

Examples:
  get_users()                           - Execute operation without parameters
  get_user(user_id="123")               - Execute with parameters
  create_user(data={"name": "John"})   - Pass complex data
```

**`/exit`** or **`/quit`** - Exit the REPL (you can also use Ctrl+D):

```
>>> /exit
Goodbye! 👋
```

#### Command History

Navigate your command history with **UP** and **DOWN** arrow keys. Your history is saved to `~/.clientele_history` and persists between sessions.

### Example Session

Here's a complete example exploring the PokeAPI:

```
$ clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml

═══════════════════════════════════════════════════════════
  Clientele Interactive API Explorer v0.10.0
═══════════════════════════════════════════════════════════

Type /help or ? for commands, /exit or Ctrl+D to quit
Type /list to see available operations

Press TAB for autocomplete

>>> /list
Available Operations
┌──────────────────────────────┬────────┬─────────────────────────────┐
│ Operation                    │ Method │ Description                 │
├──────────────────────────────┼────────┼─────────────────────────────┤
│ ability_list                 │ GET    │ List abilities              │
│ ability_read                 │ GET    │ Get ability by ID or name   │
│ pokemon_list                 │ GET    │ List pokemon                │
│ pokemon_read                 │ GET    │ Get pokemon by ID or name   │
│ berry_list                   │ GET    │ List berries                │
│ move_list                    │ GET    │ List moves                  │
└──────────────────────────────┴────────┴─────────────────────────────┘

Total: 6 operations

>>> pokemon_list(limit=3)
✓ Success in 0.52s
{
  "count": 1302,
  "next": "https://pokeapi.co/api/v2/pokemon?offset=3&limit=3",
  "previous": null,
  "results": [
    {
      "name": "bulbasaur",
      "url": "https://pokeapi.co/api/v2/pokemon/1/"
    },
    {
      "name": "ivysaur",
      "url": "https://pokeapi.co/api/v2/pokemon/2/"
    },
    {
      "name": "venusaur",
      "url": "https://pokeapi.co/api/v2/pokemon/3/"
    }
  ]
}

>>> pokemon_read(id="pikachu")
✓ Success in 0.38s
{
  "id": 25,
  "name": "pikachu",
  "height": 4,
  "weight": 60,
  "types": [
    {
      "slot": 1,
      "type": {
        "name": "electric",
        "url": "https://pokeapi.co/api/v2/type/13/"
      }
    }
  ],
  "abilities": [
    {
      "ability": {
        "name": "static",
        "url": "https://pokeapi.co/api/v2/ability/9/"
      },
      "is_hidden": false,
      "slot": 1
    },
    {
      "ability": {
        "name": "lightning-rod",
        "url": "https://pokeapi.co/api/v2/ability/31/"
      },
      "is_hidden": true,
      "slot": 3
    }
  ]
}

>>> ability_read(id="lightning-rod")
✓ Success in 0.29s
{
  "id": 31,
  "name": "lightning-rod",
  "is_main_series": true,
  "generation": {
    "name": "generation-iii",
    "url": "https://pokeapi.co/api/v2/generation/3/"
  },
  "effect_entries": [
    {
      "effect": "All single-target Electric-type moves are redirected to this Pokémon...",
      "language": {
        "name": "en",
        "url": "https://pokeapi.co/api/v2/language/9/"
      }
    }
  ]
}

>>> /exit
Goodbye! 👋
```

### Response Formatting

The explore command automatically formats responses for readability:

**JSON Responses** - Syntax-highlighted with proper indentation:

```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Timing Information** - Every request shows execution time:

```
✓ Success in 0.45s
```

**Error Handling** - Errors are displayed in a clear, formatted panel:

```
✗ Error in 0.12s
╭─────────────────────── Error ───────────────────────╮
│ ValueError: Missing required parameter: user_id     │
╰─────────────────────────────────────────────────────╯
```

### Use Cases

#### API Discovery

Quickly explore what operations are available in an API:

```sh
clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
>>> /list
```

#### Testing Before Coding

Try out API calls to understand request/response formats before writing production code:

```sh
clientele explore -o pokeapi_client/
>>> pokemon_list(limit=5)
>>> pokemon_read(id="charizard")
>>> ability_read(id="blaze")
```

#### Debugging

Validate that specific API operations work as expected:

```sh
clientele explore -o pokeapi_client/
>>> pokemon_read(id="pikachu")
>>> berry_read(id=1)
```

#### Documentation & Demos

Use the explore command during demos or documentation to show live API interactions.

### Tips & Tricks

**Use `?` as a shortcut for help:**

```
>>> ?
(Shows help message)
```

**Press Ctrl+C to cancel current input** without exiting the REPL.

**Press Ctrl+D to exit** the REPL quickly.

**Use arrow keys** to navigate command history - perfect for repeating similar commands with small variations.

**Tab completion works everywhere** - try it at any point to see available options.

### Compatibility

The explore command works with:

- ✅ Standard function-based clients (`generate`)
- ✅ Class-based clients (`generate-class`)
- ✅ Both sync and async clients
- ✅ Clients with authentication configured
- ✅ All OpenAPI 3.0+ schemas

### Limitations

- The explore command is **interactive only** - not suitable for CI/CD or automated testing
- Operations are executed against the **actual API** - be careful with destructive operations
- For automated testing, use the generated client directly in your test suite

## `version`

Print the current version of Clientele:

```sh
> clientele version
Clientele 0.9.0
```

## Regenerating

At times you may wish to regenerate the client. This could be because the API has updated or you just want to use a newer version of clientele.

To force a regeneration you must pass the `--regen` or `-r` argument, for example:

```sh
clientele generate -f example_openapi_specs/best.json -o my_client/  --regen t
```

!!! note

    You can copy and paste the command from the `MANIFEST.md` file in your previously-generated client for a quick and easy regeneration.

### Understanding Regeneration

When you regenerate a client with `--regen t`, Clientele follows these rules:

**Files that WILL be overwritten:**

- `client.py` - Your API client functions/class
- `schemas.py` - Pydantic models for request/response data
- `http.py` - HTTP handling logic
- `__init__.py` - Package initialization
- `MANIFEST.md` - Metadata about the generated client

**Files that will NOT be overwritten:**

- `config.py` - Your custom configuration (API URL, auth tokens, headers)

This design ensures your customizations in `config.py` are preserved while keeping the client code in sync with the latest API schema.

### The MANIFEST.md File

Every generated client includes a `MANIFEST.md` file that records:

- The exact command used to generate the client
- The OpenAPI version of the source schema
- The Clientele version used
- Generation timestamp

Example `MANIFEST.md`:

```markdown
# Manifest

Generated with [https://github.com/phalt/clientele](https://github.com/phalt/clientele)
Install with pipx:

```sh
pipx install clientele
```

API VERSION: 0.1.0
OPENAPI VERSION: 3.0.2
CLIENTELE VERSION: 0.10.0

Regenerate using this command:

```sh
clientele generate -f example_openapi_specs/best.json -o tests/async_test_client/ --asyncio t --regen t
```

You can copy the command directly from this file to regenerate your client.

### Regeneration Workflow

Here's the recommended workflow for keeping your client in sync:

1. **API Updated**: Your API has new endpoints or changed schemas
2. **Regenerate**: Run `clientele generate` with `--regen t`
   ```sh
   clientele generate -u http://localhost:8000/openapi.json -o my_client/ --regen t
   ```
3. **Review Changes**: Use git to see what changed
   ```sh
   git diff my_client/
   ```
4. **Inspect**: Look at:
   - New functions in `client.py`
   - Modified schemas in `schemas.py`
   - Changes to function signatures
5. **Test**: Run your test suite to catch breaking changes
   ```sh
   pytest tests/
   ```
6. **Commit**: Add the changes to git
   ```sh
   git add my_client/
   git commit -m "Regenerate client for API v2.1"
   ```

### Handling Breaking Changes

When the API introduces breaking changes, regeneration will reflect them:

- **Removed endpoints** → Functions deleted from `client.py`
- **Renamed fields** → Schema properties change
- **New required fields** → Function signatures updated
- **Changed response types** → Schema unions modified

Your tests should catch these issues. If you need to support multiple API versions, consider:

- Generating separate clients for each version
- Using version-specific directories (e.g., `my_client_v1/`, `my_client_v2/`)

### Regenerating vs. Fresh Generation

**Regenerating** (`--regen t`):

- Overwrites most files except `config.py`
- Preserves your configuration
- Intended for updating an existing client

**Fresh Generation** (without `--regen`):

- Will fail if the output directory already exists
- Use for creating a new client from scratch

### Integration with CI/CD

You can automate regeneration in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Regenerate API client
  run: |
    clientele generate \
      -u http://api:8000/openapi.json \
      -o clients/my_api/ \
      --regen t
    
    # Check if client changed
    if ! git diff --quiet clients/my_api/; then
      echo "API client changed - review required"
      git diff clients/my_api/
      exit 1
    fi
```

This keeps your client in sync with the API schema.
