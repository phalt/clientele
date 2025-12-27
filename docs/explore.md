# Explorer Mode

The `explore` command launches an **interactive REPL** that lets you explore and test API operations without writing any code. It's perfect for API discovery, testing, and debugging.

![repl demo](https://raw.githubusercontent.com/phalt/clientele/refs/heads/main/docs/clientele.gif)

## Usage Modes

### Explore an Existing Client

If you've already generated a client, you can explore it directly:

```sh
clientele explore -c pokeapi_client/
```

### Explore from a Schema File

Generate a temporary client and explore it in one command:

```sh
clientele explore -f pokeapi_openapi.yml
```

Clientele will:

1. Generate a client in a temporary directory from the schema
2. Load it into the REPL
3. Clean up the temporary files when you exit

### Explore from a Schema URL

You can also explore directly from a URL:

```sh
clientele explore -u https://raw.githubusercontent.com/PokeAPI/pokeapi/master/openapi.yml
```

## Interactive Features

Once inside the REPL, you have access to several powerful features:

### Tab Autocomplete

Press **TAB** to autocomplete:

```sh
>>> api_v2_pokemon_  <TAB>
api_v2_pokemon_list                 pokemon_read
api_v2_pokemon_encounter_list       pokemon_form_list
```

### Execute Operations

Make API calls using the available operations

```python
# Simple operation with no parameters
>>> api_v2_ability_list()

# Operation with parameters
>>> api_v2_pokemon_list(limit=5, offset=0)

# Operation with a specific ID
>>> api_v2_pokemon_retrieve(id=25)
```

The REPL will:

- Validate your arguments against the operation signature
- Execute the API call
- Display timing information
- Format the response with syntax highlighting

### Inspect Schemas

You can inspect Pydantic schemas by simply typing their name (without parentheses):

```sh
>>> UserResponse
╭─────────────────────────────── UserResponse ───────────────────────────────╮
│ User response model containing user information.                           │
╰────────────────────────────────────────────────────────────────────────────╯

Fields:
┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ Field   ┃ Type   ┃ Required ┃
┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ id      │ int    │ ✓        │
│ name    │ str    │ ✓        │
│ email   │ str    │ ✓        │
│ active  │ bool   │ ✗        │
└─────────┴────────┴──────────┘

Total: 4 fields
```

This displays:
- The schema's docstring (if it has one)
- All fields with their types
- Whether each field is required or optional

You can also use the `/schemas` command to list all available schemas or view specific schema details:

```sh
# List all schemas
>>> /schemas

# View a specific schema
>>> /schemas UserResponse
```

### Special Commands

Commands starting with `/` provide additional functionality:

**`/list`** or **`/operations`** - List all available operations in a table:

```sh
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

```sh
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

```sh
>>> /exit
Goodbye! 👋
```

#### Command History

Navigate your command history with **UP** and **DOWN** arrow keys. Your history is saved to `~/.clientele_history` and persists between sessions.

### Config

You can inspect and modify the config during a CLI session:

```sh
# Show configuration values
>>> /config
Current Configuration              
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Setting      ┃ Value              ┃ Source    ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ base_url     │ https://pokeapi.co │ config.py │
│ bearer_token │ token              │ config.py │
│ user_key     │ user               │ config.py │
│ pass_key     │ password           │ config.py │
└──────────────┴────────────────────┴───────────┘

Debug Mode: OFF

# Update a config value
>>> /config set base_url mynewurl.com
✓ Set base_url = mynewurl.com
This override applies only to the current REPL session
```

Config changes only persist during the CLI session.

### Debug

You can enable debug mode to print useful information when using explore:

```sh
# Show debug state
>>> /debug
Debug Mode: OFF

Use '/debug on' or '/debug off' to toggle debug mode
# Update debug state
>>> /debug on
✓ Debug mode enabled
HTTP requests and responses will be logged
```

## Response Formatting

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

```sh
✓ Success in 0.45s
```

**Error Handling** - Errors are displayed in a clear, formatted panel:

```sh
✗ Error in 0.12s
╭─────────────────────── Error ───────────────────────╮
│ ValueError: Missing required parameter: user_id     │
╰─────────────────────────────────────────────────────╯
```

## Compatibility

The explore command works with:

- ✅ Standard function-based clients (`generate`)
- ✅ Class-based clients (`generate-class`)
- ✅ Both sync and async clients
- ✅ Clients with authentication configured
- ✅ All OpenAPI 3.0+ schemas

## Limitations

- The explore command is **interactive only** - not suitable for CI/CD or automated testing
- Operations are executed against the **actual API** - be careful with destructive operations
- For automated testing, use the generated client directly in your test suite
