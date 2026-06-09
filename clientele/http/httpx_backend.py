from __future__ import annotations

import typing

import httpx2

from clientele.api import exceptions as api_exceptions
from clientele.api.stream import hydrate_content
from clientele.http import backends, response


class HttpxHTTPBackend(backends.HTTPBackend):
    """Default HTTP backend using the httpx library.

    This is the default backend for clientele and provides full support
    for synchronous and asynchronous HTTP requests using httpx2.

    This backend converts httpx2.Response objects to generic clientele.http.Response
    objects to maintain abstraction from the underlying HTTP library.

    Args:
        client_options: Dictionary of options to pass to httpx2.Client and httpx2.AsyncClient.
            See https://www.python-httpx2.org/api/#client for available options.
    """

    _sync_client: httpx2.Client | None = None
    _async_client: httpx2.AsyncClient | None = None

    def __init__(self, client_options: dict[str, typing.Any] | None = None) -> None:
        self.client_options = client_options or {}

    @classmethod
    def from_config(cls, config: typing.Any) -> "HttpxHTTPBackend":
        return cls(
            client_options={
                "base_url": config.base_url,
                "headers": config.headers,
                "timeout": config.timeout,
                "follow_redirects": config.follow_redirects,
                "verify": config.verify,
                "http2": config.http2,
            }
        )

    def build_client(self) -> httpx2.Client:
        """Build and return a synchronous httpx2.Client."""
        if not self._sync_client:
            self._sync_client = httpx2.Client(**self.client_options)
        return self._sync_client

    def build_async_client(self) -> httpx2.AsyncClient:
        """Build and return an asynchronous httpx2.AsyncClient."""
        if not self._async_client:
            self._async_client = httpx2.AsyncClient(**self.client_options)
        return self._async_client

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        """Convert an httpx2.Response to a generic clientele Response.

        Args:
            native_response: An httpx2.Response object

        Returns:
            A generic clientele.http.Response object
        """
        # Accept any httpx2.Response or response-like object
        httpx_response = native_response

        # Handle case where request might not be set (e.g., in tests)
        request_method = httpx_response.request.method
        request_url = str(httpx_response.request.url)

        return response.Response(
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            content=httpx_response.content,
            text=httpx_response.text,
            request_method=request_method,
            request_url=request_url,
        )

    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Send a synchronous HTTP request using httpx2.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Returns:
            A generic clientele.http.Response object
        """
        client = self.build_client()
        httpx_response = client.request(method, url, **kwargs)
        return self.convert_to_response(httpx_response)

    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Send an asynchronous HTTP request using httpx2.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional request parameters (headers, params, json, etc.)

        Returns:
            A generic clientele.http.Response object
        """
        client = self.build_async_client()
        httpx_response = await client.request(method, url, **kwargs)
        return self.convert_to_response(httpx_response)

    def close(self) -> None:
        """Close the synchronous httpx client."""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        """Asynchronously close the async httpx client."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
        """Handle synchronous streaming response without buffering.

        Uses httpx2.Client.stream()
        """
        client = self.build_client()
        with client.stream(method, url, **kwargs) as httpx_response:
            try:
                # Check status code before starting to stream
                if 400 <= httpx_response.status_code < 600:
                    # For error responses, read the full response then raise
                    httpx_response.read()  # Read the stream before accessing content
                    generic_response = self.convert_to_response(httpx_response)
                    raise api_exceptions.HTTPStatusError(
                        response=generic_response,
                        reason=f"HTTP {httpx_response.status_code}",
                    )

                for line in httpx_response.iter_lines():
                    if not line:
                        continue

                    if response_parser is not None:
                        yield response_parser(line)
                    else:
                        yield hydrate_content(line, inner_type)
            finally:
                pass

    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        """Handle asynchronous streaming response without buffering.

        Uses httpx2.AsyncClient.stream()
        """

        client = self.build_async_client()
        async with client.stream(method, url, **kwargs) as httpx_response:
            try:
                # Check status code before starting to stream
                if 400 <= httpx_response.status_code < 600:
                    # For error responses, read the full response then raise
                    await httpx_response.aread()  # Read the stream before accessing content
                    generic_response = self.convert_to_response(httpx_response)
                    raise api_exceptions.HTTPStatusError(
                        response=generic_response,
                        reason=f"HTTP {httpx_response.status_code}",
                    )

                async for line in httpx_response.aiter_lines():
                    if not line:
                        continue

                    if response_parser is not None:
                        yield response_parser(line)
                    else:
                        yield hydrate_content(line, inner_type)
            finally:
                pass
