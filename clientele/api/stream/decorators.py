from __future__ import annotations

import inspect
import typing
from functools import wraps

from clientele import api
from clientele.api import requests

_F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])


class StreamDecorators:
    """
    Provides SSE (Server-Sent Events) streaming decorators.

    Accessed via client.stream.get(), client.stream.post(), etc.
    """

    def __init__(self, client: api.APIClient):
        self._client = client

    def get(self, path: str) -> typing.Callable[[_F], _F]:
        """Decorator for SSE GET requests."""
        return self._create_sse_decorator("GET", path)

    def post(self, path: str) -> typing.Callable[[_F], _F]:
        """Decorator for SSE POST requests."""
        return self._create_sse_decorator("POST", path)

    def patch(self, path: str) -> typing.Callable[[_F], _F]:
        """Decorator for SSE PATCH requests."""
        return self._create_sse_decorator("PATCH", path)

    def put(self, path: str) -> typing.Callable[[_F], _F]:
        """Decorator for SSE PUT requests."""
        return self._create_sse_decorator("PUT", path)

    def delete(self, path: str) -> typing.Callable[[_F], _F]:
        """Decorator for SSE DELETE requests."""
        return self._create_sse_decorator("DELETE", path)

    def _create_sse_decorator(
        self,
        method: str,
        path: str,
    ) -> typing.Callable[[_F], _F]:
        """
        Create a decorator for SSE streaming endpoints.

        Similar to APIClient._create_decorator but with streaming=True.
        """

        def decorator(func: _F) -> _F:
            context = requests.build_request_context(
                method,
                path,
                func,
                response_map=None,
                response_parser=None,
                streaming=True,
            )

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                    # Use streaming execution path
                    return await self._client._execute_async_stream(context, args, kwargs)

                async_wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
                return typing.cast(_F, async_wrapper)

            @wraps(func)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                # Use streaming execution path
                return self._client._execute_sync_stream(context, args, kwargs)

            wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
            return typing.cast(_F, wrapper)

        return decorator
