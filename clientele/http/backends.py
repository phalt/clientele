from __future__ import annotations

import abc
import typing

from clientele.http import response as http_response


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
    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
        """Handle synchronous streaming HTTP response without buffering.

        This method streams the response body line-by-line without buffering
        the entire response into memory. Each line is yielded immediately
        after being parsed.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            inner_type: The type to hydrate each streamed item to
            response_parser: Optional custom parser for each line
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Yields:
            Parsed items of inner_type, one per line
        """
        yield  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        """Handle asynchronous streaming HTTP response without buffering.

        This method streams the response body line-by-line without buffering
        the entire response into memory. Each line is yielded immediately
        after being parsed.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            inner_type: The type to hydrate each streamed item to
            response_parser: Optional custom parser for each line
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Yields:
            Parsed items of inner_type, one per line
        """
        yield  # pragma: no cover
        raise NotImplementedError
