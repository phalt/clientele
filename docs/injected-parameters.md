# Injected parameters & typing

## The problem they solve

When you decorate a function with `@client.get(...)`, Clientele needs to hand back the parsed HTTP response to your function body. The natural way to do that is through a parameter, but that creates an awkward situation:

```python
@client.get("/users/{user_id}")
def get_user(result: User, user_id: int) -> User:
    return result
```

From *inside* the function, `result` is essential because it holds the `User` parsed from the response. But from the *caller's* perspective, `result` makes no sense: callers supply `user_id`, not a `User` they already have. If Clientele exposed `result` in the public signature, every call site would look broken:

```python
# Without injection stripping the callers would need to provide result themselves:
get_user(result=???, user_id=42)
```

Injected parameters are how Clientele resolves this: `result` (and the optional `response`) live in the function definition for *your* use, but Clientele **strips them from the public signature** so callers never see them.

---

## What callers and IDEs see

Clientele uses Python's `typing.Concatenate` and `typing.ParamSpec` to express this contract to type checkers at the decorator level. The decorator signature says: *"I accept a function whose first N parameters are injected values, and I return a new callable with those parameters removed."*

The result is that your IDE and type checker see the **public API**, not the implementation detail:

```
# What you write:
def get_user(result: User, user_id: int) -> User

# What your IDE and type checker see after decoration:
get_user(user_id: int) -> User
```

So autocomplete shows `user_id`, not `result`. Passing `user_id=42` produces no type error. Passing `result=...` produces an error, because `result` isn't in the public signature at all.

```python
get_user(user_id=42)        # ✅ correct
get_user(result=my_user, user_id=42)  # ❌ type error: unknown argument
```

At runtime, Clientele also patches the function's `__signature__` so that `inspect.signature()`, IDEs using runtime introspection, and Clientele's own cache key generator all agree with what the type checker sees.

---

## Injected parameters

Clientele injects the following parameters:

| Parameter  | Type                       | Required | Description                                                         |
|------------|----------------------------|----------|---------------------------------------------------------------------|
| `result`   | Your annotated type        | Yes      | The HTTP response body, parsed and validated into the declared type |
| `response` | `http.Response`            | No       | The raw `http.Response`, useful for headers, status, debugging     |

```python
from pydantic import BaseModel
from clientele import api as clientele_api

client = clientele_api.APIClient(base_url="https://api.example.com")

class User(BaseModel):
    id: int
    name: str

# result only — the common case
@client.get("/users/{user_id}")
def get_user(result: User, user_id: int) -> User:
    return result

# result + response — when you need headers or status
@client.get("/users/{user_id}")
def get_user_with_meta(result: User, response: httpx.Response, user_id: int) -> tuple[User, int]:
    return result, response.status_code
```

---

## Ordering requirement

**`result` and `response` must appear first in the parameter list**, before any caller-supplied parameters (path params, query params, `data`).

This is required because the `Concatenate` trick works by stripping parameters from the *front* of the signature. If injected params appear anywhere else, the type math breaks and type checkers will see the wrong signature.

```python
# ✅ Correct: injected params first
# Type checker sees: get_user(user_id: int) -> User
@client.get("/users/{user_id}")
def get_user(result: User, user_id: int) -> User:
    return result

# ❌ Incorrect: result is not first
# Type checker sees: get_user(user_id: int, result: User) -> User
@client.get("/users/{user_id}")
def get_user(user_id: int, result: User) -> User:
    return result
```

The runtime injection works regardless of position (Clientele finds injected params by name), but **correct typing requires them first**.

---

## Mypy plugin

Mypy does not natively support the `Concatenate`-based approach for stripping positional parameters. Clientele ships a mypy plugin that teaches mypy the same rule explicitly:

- Removes `result` and `response` from decorated function signatures during type checking
- Allows `dict` types to be passed where Pydantic models are expected (TypedDict ergonomics)

### Setup

The plugin is installed automatically with Clientele. Add it to your mypy configuration:

=== "mypy.ini / setup.cfg"

    ```ini
    [mypy]
    plugins = clientele.mypy
    ```

=== "pyproject.toml"

    ```toml
    [tool.mypy]
    plugins = ["clientele.mypy"]
    ```

With the plugin active, mypy behaves the same as pyright and ty: `result` and `response` are invisible to callers.

!!! note
    If you use **pyright** or **ty**, no plugin is needed — the `Concatenate`-based decorator signature is supported natively. Just ensure injected params appear first (see above).

---
