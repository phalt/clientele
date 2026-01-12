from __future__ import annotations

import inspect
import json
import re
import typing

# Parameters to ignore when generating cache keys (injected by clientele at runtime)
IGNORE_KEYS = {"result", "response", "data", "headers"}


def generate_cache_key(
    func: typing.Callable,
    args: tuple,
    kwargs: dict,
    path_template: typing.Optional[str] = None,
) -> str:
    """Generate a deterministic cache key from function arguments.

    Cache keys are generated as: "path:param1=value1:param2=value2"

    Algorithm:
    1. Extract function signature and bind arguments
    2. Filter out 'result' parameter (injected by clientele)
    3. Filter out 'data' parameter (request body, not part of cache identity)
    4. If path_template provided:
       - Extract path parameters (those in {braces})
       - Include path params first, then query params
    5. Sort parameters alphabetically for deterministic ordering
    6. Serialize values using serialize_value()
    7. Return formatted key string

    Args:
        func: The decorated function
        args: Positional arguments passed to the function
        kwargs: Keyword arguments passed to the function
        path_template: The API path template (e.g., "/pokemon/{id}")

    Returns:
        A deterministic cache key string

    Examples:
        >>> # For @client.get("/pokemon/{id}") called with id=25
        >>> generate_cache_key(func, (25,), {}, "/pokemon/{id}")
        "/pokemon/{id}:id=25"

        >>> # For @client.get("/users") called with limit=10, offset=0
        >>> generate_cache_key(func, (), {"limit": 10, "offset": 0}, "/users")
        "/users:limit=10:offset=0"

        >>> # Parameters are sorted alphabetically
        >>> generate_cache_key(func, (), {"z": 1, "a": 2}, "/items")
        "/items:a=2:z=1"
    """
    # Get function signature
    sig = inspect.signature(func)

    # Try to bind arguments - use partial binding to allow missing parameters
    # This is necessary because clientele injects 'result' and 'response' parameters at runtime
    try:
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # Filter out internal parameters
        params = {k: v for k, v in bound.arguments.items() if k not in IGNORE_KEYS}
    except TypeError:
        # If binding fails, fall back to using kwargs directly
        params = {k: v for k, v in kwargs.items() if k not in IGNORE_KEYS}

    # Build cache key parts
    base = path_template if path_template else getattr(func, "__name__", "<unknown>")

    if params:
        # Sort for deterministic ordering
        param_parts = [f"{k}={serialize_value(v)}" for k, v in sorted(params.items())]
        return f"{base}:{':'.join(param_parts)}"
    else:
        return base


def extract_path_params(path_template: str) -> list[str]:
    """Extract parameter names from a path template.

    Uses regex to find all {param_name} patterns.

    Args:
        path_template: Path template like "/pokemon/{id}"

    Returns:
        List of parameter names

    Examples:
        >>> extract_path_params("/pokemon/{id}")
        ["id"]
        >>> extract_path_params("/users/{user_id}/posts/{post_id}")
        ["user_id", "post_id"]
        >>> extract_path_params("/items")
        []
    """
    return re.findall(r"\{([^}]+)\}", path_template)


def serialize_value(value: typing.Any) -> str:
    """Serialize a value for cache key generation.

    Creates deterministic string representations suitable for cache keys.

    Args:
        value: The value to serialize

    Returns:
        String representation

    Examples:
        >>> serialize_value(42)
        "42"
        >>> serialize_value("hello")
        "hello"
        >>> serialize_value(None)
        "null"
        >>> serialize_value({"b": 2, "a": 1})
        '{"a":1,"b":2}'  # Sorted keys for determinism
    """
    if value is None:
        return "null"
    elif isinstance(value, (bool, int, float)):
        return str(value)
    elif isinstance(value, str):
        return value
    elif hasattr(value, "model_dump"):  # Pydantic model
        return json.dumps(value.model_dump(), sort_keys=True, separators=(",", ":"))
    elif isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    else:
        return repr(value)
