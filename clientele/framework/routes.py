from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

from .client import Client, _build_request_context

_F = TypeVar("_F", bound=Callable[..., Any])


class Routes:
    """Decorator provider for class-based APIs (Pattern A).

    Decorators capture route metadata at import time and delegate execution to a
    ``Client`` stored on the instance (default attribute name: ``_client``).
    """

    def __init__(self, *, client_attribute: str = "_client") -> None:
        self.client_attribute = client_attribute

    def get(self, path: str) -> Callable[[Callable[..., Any]], _F]:
        return self._create_decorator("GET", path)

    def post(self, path: str) -> Callable[[Callable[..., Any]], _F]:
        return self._create_decorator("POST", path)

    def put(self, path: str) -> Callable[[Callable[..., Any]], _F]:
        return self._create_decorator("PUT", path)

    def patch(self, path: str) -> Callable[[Callable[..., Any]], _F]:
        return self._create_decorator("PATCH", path)

    def delete(self, path: str) -> Callable[[Callable[..., Any]], _F]:
        return self._create_decorator("DELETE", path)

    def _create_decorator(self, method: str, path: str) -> Callable[[Callable[..., Any]], _F]:
        def decorator(func: Callable[..., Any]) -> _F:
            context = _build_request_context(method, path, func)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    client = self._resolve_client(args)
                    return await client._execute_async(context, args, kwargs)

                return async_wrapper  # type: ignore[return-value]

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                client = self._resolve_client(args)
                return client._execute_sync(context, args, kwargs)

            return wrapper  # type: ignore[return-value]

        return decorator

    def _resolve_client(self, args: tuple[Any, ...]) -> Client:
        if not args:
            raise TypeError("Routes-decorated methods must be called with an instance as the first argument")

        instance = args[0]
        client = getattr(instance, self.client_attribute, None)
        if client is None:
            raise AttributeError(
                f"Expected '{self.client_attribute}' on {instance!r} to execute the request. "
                "Assign a Client in __init__."
            )
        if not isinstance(client, Client):
            raise TypeError(
                f"Attribute '{self.client_attribute}' must be a Client instance; got {type(client)!r} instead"
            )

        return client
