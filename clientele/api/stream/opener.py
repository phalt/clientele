"""
Open a backend stream when the decorated function is called.

The request is sent and its status checked immediately, so HTTP errors are
raised by the call itself rather than on first iteration. The returned
generator owns the open response and closes it when it is exhausted, closed
or garbage collected after starting.
"""

from __future__ import annotations

import contextlib
import typing

from clientele.api.stream import lines
from clientele.http import backends
from clientele.http import response as http_response


def open_sync_lines(
    backend: backends.HTTPBackend, method: str, url: str, **kwargs: typing.Any
) -> typing.Generator[str, None, None]:
    """Send a streaming request now and return a generator over its lines.

    Raises:
        HTTPStatusError: If the response status is 4xx or 5xx. The error
            carries the fully read body.
    """
    with contextlib.ExitStack() as stack:
        stream_response = stack.enter_context(backend.open_sync_stream(method=method, url=url, **kwargs))
        if _is_error(stream_response.status_code):
            raise _status_error(stream_response, b"".join(stream_response.chunks))
        owned = stack.pop_all()
    return _close_after(owned, lines.iter_lines(stream_response.chunks))


async def open_async_lines(
    backend: backends.HTTPBackend, method: str, url: str, **kwargs: typing.Any
) -> typing.AsyncGenerator[str, None]:
    """Send a streaming request now and return an async generator over its lines.

    Raises:
        HTTPStatusError: If the response status is 4xx or 5xx. The error
            carries the fully read body.
    """
    async with contextlib.AsyncExitStack() as stack:
        stream_response = await stack.enter_async_context(backend.open_async_stream(method=method, url=url, **kwargs))
        if _is_error(stream_response.status_code):
            body = b"".join([chunk async for chunk in stream_response.chunks])
            raise _status_error(stream_response, body)
        owned = stack.pop_all()
    return _aclose_after(owned, lines.aiter_lines(stream_response.chunks))


def _is_error(status_code: int) -> bool:
    return 400 <= status_code < 600


def _status_error(
    stream_response: backends.StreamResponse | backends.AsyncStreamResponse, body: bytes
) -> http_response.HTTPStatusError:
    return http_response.HTTPStatusError(
        response=stream_response.to_response(body),
        reason=f"HTTP {stream_response.status_code}",
    )


def _close_after(stack: contextlib.ExitStack, items: typing.Iterator[str]) -> typing.Generator[str, None, None]:
    with stack:
        yield from items


async def _aclose_after(
    stack: contextlib.AsyncExitStack, items: typing.AsyncIterator[str]
) -> typing.AsyncGenerator[str, None]:
    async with stack:
        async for item in items:
            yield item
