from __future__ import annotations

import functools
import inspect
import typing

from clientele import api
from clientele.cache.backends import MemoryBackend
from clientele.cache.key_generator import IGNORE_KEYS, generate_cache_key
from clientele.cache.types import CacheBackend

# Type variable for generic function decoration
F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])

# Global default cache backend
_default_backend: CacheBackend = MemoryBackend()


def memoize(
    ttl: typing.Optional[int | float] = None,
    backend: typing.Optional[CacheBackend] = None,
    key: typing.Optional[typing.Callable[..., str]] = None,
    enabled: bool = True,
) -> typing.Callable[[F], F]:
    """Decorator to cache HTTP GET request results.

    This decorator should be applied ABOVE the @client.get() decorator:

        @memoize(ttl=300)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

    Args:
        ttl: Time-to-live in seconds (None = cache forever)
        backend: Cache backend to use (defaults to global MemoryBackend)
        key: Custom cache key function receiving the same args as the decorated function
             (excluding 'result' and 'response'). Should return a string cache key.
        enabled: Whether caching is enabled

    Returns:
        Decorated function with caching behavior

    Examples:
        >>> # Basic usage with TTL
        >>> @memoize(ttl=300)
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result

        >>> # Custom cache key
        >>> @memoize(ttl=600, key=lambda id: f"pokemon:{id}")
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result

        >>> # Conditional caching based on config
        >>> ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true") == "true"
        >>> @memoize(ttl=300, enabled=ENABLE_CACHE)
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result
    """

    def decorator(func: F) -> F:
        if not backend:
            cache_backend = _extract_cache_backend(func)
        else:
            cache_backend = backend

        path_template, http_method = _extract_request_context(func)

        def _generate_cache_key(args: tuple, kwargs: dict) -> str:
            """Generate cache key from arguments (shared by sync and async wrappers)."""
            if key is not None:
                sig = inspect.signature(func)
                try:
                    bound = sig.bind_partial(*args, **kwargs)
                    bound.apply_defaults()
                    key_args = {k: v for k, v in bound.arguments.items() if k not in IGNORE_KEYS}
                except TypeError:
                    key_args = {k: v for k, v in kwargs.items() if k not in IGNORE_KEYS}
                return key(**key_args)
            else:
                cache_key = generate_cache_key(func, args, kwargs, path_template)
                return f"{http_method}:{cache_key}" if http_method else cache_key

        @functools.wraps(func)
        def sync_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not enabled:
                return func(*args, **kwargs)

            cache_key = _generate_cache_key(args, kwargs)

            # Try to get from cache
            cached_value = cache_backend.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss - call original function
            result = func(*args, **kwargs)

            # Store in cache (only if result is not None)
            if result is not None:
                cache_backend.set(cache_key, result, ttl)

            return result

        @functools.wraps(func)
        async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            if not enabled:
                return await func(*args, **kwargs)

            cache_key = _generate_cache_key(args, kwargs)

            # Try to get from cache
            cached_value = cache_backend.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss - call original function
            result = await func(*args, **kwargs)

            # Store in cache (only if result is not None)
            if result is not None:
                cache_backend.set(cache_key, result, ttl)

            return result

        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return typing.cast(F, async_wrapper)
        else:
            return typing.cast(F, sync_wrapper)

    return decorator


def _extract_request_context(func: typing.Callable) -> tuple[typing.Optional[str], typing.Optional[str]]:
    """Extract path template and HTTP method from clientele decorator closure.

    This function inspects the closure of a function decorated with @client.get(), etc.
    to extract the _RequestContext object containing the path template and HTTP method.

    Args:
        func: The decorated function

    Returns:
        Tuple of (path_template, http_method) or (None, None) if not found

    Examples:
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result
        >>> _extract_request_context(get_pokemon)
        ("/pokemon/{id}", "GET")

        >>> def regular_function():
        >>>     pass
        >>> _extract_request_context(regular_function)
        (None, None)
    """
    try:
        if not hasattr(func, "__closure__") or func.__closure__ is None:
            return (None, None)

        # Type checker: __closure__ is confirmed to be not None above
        for cell in func.__closure__:  # type: ignore[union-attr]
            cell_contents = cell.cell_contents
            if hasattr(cell_contents, "__dict__"):
                cell_dict = getattr(cell_contents, "__dict__", {})
                if "method" in cell_dict and "path_template" in cell_dict:
                    path_template = cell_dict.get("path_template")
                    method = cell_dict.get("method")
                    if isinstance(path_template, str) and isinstance(method, str):
                        return (path_template, method.upper())

        return (None, None)
    except (AttributeError, TypeError):
        return (None, None)


def _extract_cache_backend(func: typing.Callable) -> CacheBackend:
    try:
        if not hasattr(func, "__closure__") or func.__closure__ is None:
            return _default_backend
        for cell in func.__closure__:  # type: ignore[union-attr]
            cell_contents = cell.cell_contents
            if isinstance(cell_contents, api.APIClient):
                backend = cell_contents.config.cache_backend
                # Use config backend if it is set
                return backend if backend is not None else _default_backend
    except (AttributeError, TypeError):
        return _default_backend
    return _default_backend
