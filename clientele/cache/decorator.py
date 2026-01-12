"""Memoization decorator for caching HTTP GET requests."""

import functools
import inspect
from typing import Any, Callable, Optional, TypeVar, cast

from clientele.cache.backends import MemoryBackend
from clientele.cache.key_generator import IGNORE_KEYS, generate_cache_key
from clientele.cache.types import CacheBackend

# Type variable for generic function decoration
F = TypeVar("F", bound=Callable[..., Any])

# Global default cache backend
_default_backend: CacheBackend = MemoryBackend()


def memoize(
    ttl: Optional[int | float] = None,
    backend: Optional[CacheBackend] = None,
    key: Optional[Callable[..., str]] = None,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator to cache HTTP GET request results.

    This decorator should be applied ABOVE the @client.get() decorator:

        @memoize(ttl=300)
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

    The decorator:
    - Extracts the HTTP method and path from the clientele decorator
    - Generates cache keys from the path template and function parameters
    - Checks the cache before executing the HTTP request
    - Stores results in the cache after successful requests
    - Respects TTL for automatic expiration

    IMPORTANT: Only use with GET requests (idempotent operations).
    POST/PUT/PATCH/DELETE should not be cached as they modify state.

    Args:
        ttl: Time-to-live in seconds (None = cache forever, not recommended)
        backend: Cache backend to use (defaults to global MemoryBackend)
        key: Custom cache key function receiving the same args as the decorated function
             (excluding 'result'). Should return a string cache key.
        enabled: Whether caching is enabled (allows conditional disable via config)

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
        # Use provided backend or fall back to default
        cache_backend = backend or _default_backend

        # Extract path template and HTTP method from clientele decorator closure
        path_template, http_method = _extract_request_context(func)

        def _generate_cache_key(args: tuple, kwargs: dict) -> str:
            """Generate cache key from arguments (shared by sync and async wrappers)."""
            if key is not None:
                # Use custom key function
                sig = inspect.signature(func)
                try:
                    bound = sig.bind_partial(*args, **kwargs)
                    bound.apply_defaults()
                    key_args = {k: v for k, v in bound.arguments.items() if k not in IGNORE_KEYS}
                except TypeError:
                    # Fallback to kwargs only
                    key_args = {k: v for k, v in kwargs.items() if k not in IGNORE_KEYS}
                return key(**key_args)
            else:
                # Use automatic key generation
                cache_key = generate_cache_key(func, args, kwargs, path_template)
                # Prepend HTTP method to cache key for uniqueness
                return f"{http_method}:{cache_key}" if http_method else cache_key

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
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
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
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
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator


def _extract_request_context(func: Callable) -> tuple[Optional[str], Optional[str]]:
    """Extract path template and HTTP method from clientele decorator closure.

    This function inspects the closure of a function decorated with @client.get(), etc.
    to extract the _RequestContext object containing the path template and HTTP method.

    Reference implementation: clientele/explore/introspector.py lines 266-304

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
