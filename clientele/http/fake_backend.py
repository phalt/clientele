from __future__ import annotations

import contextlib
import dataclasses
import os
import sys
import typing
import warnings

from clientele.http import backends, response

_QUEUE_RESPONSE_STREAM_DEPRECATION = (
    "Streaming a response queued with FakeHTTPBackend.queue_response() is deprecated; use queue_stream() instead."
)

# Frames inside clientele and the standard library (contextlib, asyncio) sit between the
# user's call and the warning; skipping them points the warning at the user's code.
_INTERNAL_PREFIXES = (
    os.path.dirname(os.path.dirname(__file__)) + os.sep,
    os.path.dirname(contextlib.__file__) + os.sep,
)


def _warn_queue_response_stream() -> None:
    if sys.version_info >= (3, 12):
        warnings.warn(_QUEUE_RESPONSE_STREAM_DEPRECATION, DeprecationWarning, skip_file_prefixes=_INTERNAL_PREFIXES)
    else:
        warnings.warn(_QUEUE_RESPONSE_STREAM_DEPRECATION, DeprecationWarning, stacklevel=2)


@dataclasses.dataclass(frozen=True, slots=True)
class _QueuedStream:
    chunks: tuple[bytes, ...]
    status_code: int
    headers: dict[str, str]


class FakeHTTPBackend(backends.HTTPBackend):
    """Fake HTTP backend for testing and demonstration.

    This backend doesn't make real HTTP requests. Instead, it stores
    all requests made and returns configurable fake responses.

    This is useful for:
    - Testing clientele integrations without hitting real APIs
    - Demonstrating how to build custom HTTP backends
    - Unit testing API clients

    Args:
        default_response: Default Response object to return if no queued response matches.
                          If not provided, returns a 200 OK with empty content.

    Example:
        >>> fake_backend = FakeHTTPBackend(
        ...     default_response=Response(
        ...         status_code=200,
        ...         content=b'{"message": "success"}',
        ...         headers={"content-type": "application/json"},
        ...     )
        ... )
        >>> config = Config(http_backend=fake_backend)
        >>> client = APIClient(config=config)
        >>> # Make requests - they'll be stored but not sent
        >>> # Check what was requested:
        >>> fake_backend.requests
    """

    def __init__(
        self,
        default_response: response.Response | None = None,
    ) -> None:
        if default_response is None:
            default_response = response.Response(
                status_code=200,
                content=b"",
                headers={"content-type": "application/json"},
            )
        self.default_response = default_response

        # Storage for captured requests
        self.requests: list[dict[str, typing.Any]] = []

        # Map request paths to lists of Response objects (FIFO queue per path)
        self._response_map: dict[str, list[response.Response]] = {}

        # Map request paths to queued streaming responses (FIFO queue per path)
        self._stream_map: dict[str, list[_QueuedStream]] = {}

        # Map request paths to lists of Exceptions (FIFO queue per path)
        self._error_map: dict[str, list[Exception]] = {}

    def build_client(self) -> None:
        """Return None as no real client is needed."""
        return None

    def build_async_client(self) -> None:
        """Return None as no real client is needed."""
        return None

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        """Convert a response to generic Response.

        For FakeHTTPBackend, the response is already in the generic format,
        so this is a no-op that just returns the input.

        Args:
            native_response: A clientele.http.Response object

        Returns:
            The same Response object
        """
        # FakeHTTPBackend already creates generic Response objects,
        # so no conversion needed
        return native_response

    def queue_response(
        self,
        path: str,
        response_obj: response.Response,
    ) -> None:
        """Queue a specific response for a request path.

        Responses are consumed in FIFO order for each path.

        Args:
            path: The request path (e.g., "/users/{user_id}")
            response_obj: A Response object to queue
        """
        if path not in self._response_map:
            self._response_map[path] = []
        self._response_map[path].append(response_obj)

    def queue_stream(
        self,
        path: str,
        chunks: typing.Sequence[bytes | str],
        *,
        status_code: int = 200,
        headers: typing.Mapping[str, str] | None = None,
    ) -> None:
        """Queue a streaming response for a request path.

        Each chunk is delivered separately, exactly as given, so tests can
        control where chunk boundaries fall. str chunks are encoded as UTF-8.
        Streams are consumed in FIFO order for each path.

        Args:
            path: The request path (e.g., "/events")
            chunks: The response body, as the chunks a server would send
            status_code: HTTP status code of the response
            headers: Response headers
        """
        queued = _QueuedStream(
            chunks=tuple(chunk.encode("utf-8") if isinstance(chunk, str) else chunk for chunk in chunks),
            status_code=status_code,
            headers=dict(headers or {}),
        )
        self._stream_map.setdefault(path, []).append(queued)

    def queue_error(self, path: str, error: Exception) -> None:
        """Queue an error to raise for requests to a path.

        Errors are consumed FIFO, same as responses.
        Errors take priority over queued responses.

        Args:
            path: URL path pattern to match
            error: Exception instance to raise
        """
        if path not in self._error_map:
            self._error_map[path] = []
        self._error_map[path].append(error)

    def _get_next_error(self, url: str) -> Exception | None:
        """Get next queued error for URL, or None."""
        for path in self._error_map:
            if path in url:
                errors = self._error_map[path]
                if errors:
                    return errors.pop(0)
        return None

    def _get_next_response(self, url: str) -> response.Response | None:
        """Get the next response for the given URL path or None if no queued responses.

        Args:
            url: The request URL

        Returns:
            A Response object if one is queued for this URL, otherwise None
        """
        # Try to find a matching path in the response map
        for path in self._response_map:
            if path in url:
                responses = self._response_map[path]
                if responses:
                    return responses.pop(0)
        return None

    def _create_response(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Create a fake generic Response object."""
        # Capture the request
        request_details: dict[str, typing.Any] = {
            "method": method,
            "url": url,
            "kwargs": kwargs,
        }

        # Try to get a queued response for this URL
        queued_response = self._get_next_response(url)
        if queued_response is not None:
            request_details["response"] = queued_response
            self.requests.append(request_details)
            return queued_response

        # Return the default response
        resp = response.Response(
            status_code=self.default_response.status_code,
            content=self.default_response.content,
            headers=self.default_response.headers.copy(),
            request_method=method,
            request_url=url,
        )
        request_details["response"] = resp
        self.requests.append(request_details)
        return resp

    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Capture request and return a fake response synchronously.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (stored but not used)

        Returns:
            A generic clientele.http.Response object

        Raises:
            Exception: If an error is queued for this URL path
        """
        # Check for queued error FIRST (errors take priority)
        error = self._get_next_error(url)
        if error is not None:
            self.requests.append(
                {
                    "method": method,
                    "url": url,
                    "kwargs": kwargs,
                    "error": error,
                }
            )
            raise error

        return self._create_response(method, url, **kwargs)

    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Capture request and return a fake response asynchronously.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (stored but not used)

        Returns:
            A generic clientele.http.Response object

        Raises:
            Exception: If an error is queued for this URL path
        """
        # Check for queued error FIRST (errors take priority)
        error = self._get_next_error(url)
        if error is not None:
            self.requests.append(
                {
                    "method": method,
                    "url": url,
                    "kwargs": kwargs,
                    "error": error,
                }
            )
            raise error

        return self._create_response(method, url, **kwargs)

    def close(self) -> None:
        """No-op: FakeHTTPBackend has no resources to close."""
        pass

    async def aclose(self) -> None:
        """No-op: FakeHTTPBackend has no resources to close."""
        pass

    def reset(self) -> None:
        """Clear all captured requests, queued responses, and errors."""
        self.requests.clear()
        self._response_map.clear()
        self._stream_map.clear()
        self._error_map.clear()

    def _get_next_stream(self, url: str) -> _QueuedStream:
        """Get the next queued stream for the URL.

        Falls back to a queued Response (deprecated), then to an empty 200 stream.
        """
        for path in self._stream_map:
            if path in url:
                streams = self._stream_map[path]
                if streams:
                    return streams.pop(0)

        queued_response = self._get_next_response(url)
        if queued_response is not None:
            _warn_queue_response_stream()
            return _QueuedStream(
                chunks=(queued_response.content,),
                status_code=queued_response.status_code,
                headers=dict(queued_response.headers),
            )

        return _QueuedStream(chunks=(), status_code=200, headers={})

    def _record_stream_request(self, method: str, url: str, kwargs: dict[str, typing.Any]) -> _QueuedStream:
        self.requests.append({"method": method, "url": url, "kwargs": kwargs, "streaming": True})
        return self._get_next_stream(url)

    @contextlib.contextmanager
    def open_sync_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.Generator[backends.StreamResponse, None, None]:
        """Open a fake synchronous stream from the next queued stream for the URL."""
        queued = self._record_stream_request(method, url, kwargs)
        yield backends.StreamResponse(
            status_code=queued.status_code,
            headers=dict(queued.headers),
            request_method=method,
            request_url=url,
            chunks=iter(queued.chunks),
        )

    @contextlib.asynccontextmanager
    async def open_async_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[backends.AsyncStreamResponse, None]:
        """Open a fake asynchronous stream from the next queued stream for the URL."""
        queued = self._record_stream_request(method, url, kwargs)

        async def chunks() -> typing.AsyncGenerator[bytes, None]:
            for chunk in queued.chunks:
                yield chunk

        yield backends.AsyncStreamResponse(
            status_code=queued.status_code,
            headers=dict(queued.headers),
            request_method=method,
            request_url=url,
            chunks=chunks(),
        )
