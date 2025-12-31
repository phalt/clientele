from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from pydantic import BaseModel

from .client import Client, _build_request_context

_F = TypeVar("_F", bound=Callable[..., Any])


class Routes:
    """Decorator provider for class-based APIs (Pattern A).

    Decorators capture route metadata at import time and delegate execution to a
    ``Client`` stored on the instance (default attribute name: ``_client``).
    """

    def __init__(self, *, client_attribute: str = "_client") -> None:
        self.client_attribute = client_attribute

    def get(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("GET", path, response_map=response_map)

    def post(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("POST", path, response_map=response_map)

    def put(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("PUT", path, response_map=response_map)

    def patch(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("PATCH", path, response_map=response_map)

    def delete(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("DELETE", path, response_map=response_map)

    def _create_decorator(self, method: str, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            context = _build_request_context(method, path, func, response_map=response_map)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    client = self._resolve_client(args)
                    return await client._execute_async(context, args, kwargs)

                return cast(_F, async_wrapper)

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                client = self._resolve_client(args)
                return client._execute_sync(context, args, kwargs)

            return cast(_F, wrapper)

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
