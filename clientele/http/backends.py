from __future__ import annotations

import abc
import codecs
import dataclasses
import email.message
import typing

from clientele.http import response as http_response


@dataclasses.dataclass(frozen=True, slots=True)
class StreamResponse:
    """An open, unread streaming HTTP response returned by a synchronous backend.

    Backends report the status and headers as received and expose the body
    as raw byte chunks. They do not raise on error statuses or split the body
    into lines; clientele.api does both.

    Attributes:
        status_code: HTTP status code
        headers: Response headers
        request_method: HTTP method of the request
        request_url: Full URL of the request
        chunks: The response body as it arrives, unmodified
    """

    status_code: int
    headers: typing.Mapping[str, str]
    request_method: str
    request_url: str
    chunks: typing.Iterator[bytes]

    def to_response(self, content: bytes) -> http_response.Response:
        """Build a buffered Response from this stream's metadata and its body."""
        return _buffered_response(self, content)


@dataclasses.dataclass(frozen=True, slots=True)
class AsyncStreamResponse:
    """An open, unread streaming HTTP response returned by an asynchronous backend.

    The asynchronous counterpart of StreamResponse: chunks is an async iterator.
    """

    status_code: int
    headers: typing.Mapping[str, str]
    request_method: str
    request_url: str
    chunks: typing.AsyncIterator[bytes]

    def to_response(self, content: bytes) -> http_response.Response:
        """Build a buffered Response from this stream's metadata and its body."""
        return _buffered_response(self, content)


def _buffered_response(stream_response: StreamResponse | AsyncStreamResponse, content: bytes) -> http_response.Response:
    return http_response.Response(
        status_code=stream_response.status_code,
        headers=dict(stream_response.headers),
        content=content,
        text=content.decode(_charset(stream_response.headers), errors="replace"),
        request_method=stream_response.request_method,
        request_url=stream_response.request_url,
    )


def _charset(headers: typing.Mapping[str, str]) -> str:
    """Return the charset declared in Content-Type, or utf-8 if missing or unknown."""
    for name, value in headers.items():
        if name.lower() == "content-type":
            message = email.message.Message()
            message["content-type"] = value
            charset = message.get_content_charset()
            if charset:
                try:
                    codecs.lookup(charset)
                except LookupError:
                    break
                return charset
            break
    return "utf-8"


class HTTPBackend(abc.ABC):
    """Abstract base class for HTTP backends."""

    @abc.abstractmethod
    def build_client(self) -> typing.Any:
        """Build and return a synchronous HTTP client.

        Returns:
            A client object suitable for making synchronous requests.
        """

    @abc.abstractmethod
    def build_async_client(self) -> typing.Any:
        """Build and return an asynchronous HTTP client.

        Returns:
            A client object suitable for making asynchronous requests.
        """

    @staticmethod
    @abc.abstractmethod
    def convert_to_response(native_response: typing.Any) -> http_response.Response:
        """Convert a native HTTP response to a generic clientele Response.

        Each backend must implement this to convert their library's response
        object (e.g., httpx.Response, requests.Response) to the generic
        clientele.http.Response format.

        Args:
            native_response: The native response object from the HTTP library

        Returns:
            A generic clientele.http.Response object
        """

    @abc.abstractmethod
    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> http_response.Response:
        """Send a synchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Returns:
            A generic clientele.http.Response object
        """

    @abc.abstractmethod
    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> http_response.Response:
        """Send an asynchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Returns:
            A generic clientele.http.Response object
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Close the synchronous HTTP client and release resources."""

    @abc.abstractmethod
    async def aclose(self) -> None:
        """Asynchronously close the async HTTP client and release resources."""

    @abc.abstractmethod
    def open_sync_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.ContextManager[StreamResponse]:
        """Open a synchronous streaming request.

        Returns a context manager. Entering it sends the request and yields a
        StreamResponse once the status and headers have arrived; the body is
        read lazily through StreamResponse.chunks. Exiting it closes the
        response.

        Implementations must not raise on 4xx/5xx statuses, must not buffer or
        split the body, and must close the response on exit even if the body
        was not fully read. clientele.api checks the status and parses the body.

        A backend that cannot stream synchronously should raise
        NotImplementedError from this method.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)
        """

    @abc.abstractmethod
    def open_async_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.AsyncContextManager[AsyncStreamResponse]:
        """Open an asynchronous streaming request.

        The asynchronous counterpart of open_sync_stream: returns an async
        context manager that yields an AsyncStreamResponse.

        A backend that cannot stream asynchronously should raise
        NotImplementedError from this method.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)
        """
