# 🥧 Mypy support

Clientele includes a mypy plugin that provides proper type checking for decorated API functions.

## What it does

The mypy plugin:

- Removes injected parameters (`result` and `response`) from function signatures during type checking
- Allows `dict` types to be passed to Pydantic model parameters
- Prevents false positives when calling your decorated API functions

## Installation

The plugin is automatically installed when you install Clientele.

## Configuration

Add the plugin to your mypy configuration file.

### Using `mypy.ini` or `setup.cfg`

```ini
[mypy]
plugins = clientele.mypy
```

### Using `pyproject.toml`

```toml
[tool.mypy]
plugins = ["clientele.mypy"]
```

## Example

Without the plugin, mypy would complain about the `result` parameter:

```python
from clientele import api
from pydantic import BaseModel

client = api.APIClient(base_url="https://api.example.com")

class User(BaseModel):
    name: str
    email: str

@client.get("/users/{user_id}")
def get_user(user_id: int, result: User) -> User:
    return result

# With the plugin: ✅ This works correctly
user = get_user(user_id=1)

# Without the plugin: ❌ mypy would require get_user(user_id=1, result=...)
```

The plugin ensures mypy understands that `result` and `response` are injected by Clientele and should not be provided by callers.

## Credits

Big thanks to [Christian Assing](https://github.com/chassing) for contributing this plugin!
