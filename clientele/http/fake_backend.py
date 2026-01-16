from __future__ import annotations

import typing

from clientele.http import backends, response


class FakeHTTPBackend(backends.HTTPBackend):
    """Fake HTTP backend for testing and demonstration.

    This backend doesn't make real HTTP requests. Instead, it stores
    all requests made and returns configurable fake responses.

    This is useful for:
    - Testing clientele integrations without hitting real APIs
    - Demonstrating how to build custom HTTP backends
    - Unit testing API clients

    Args:
        default_status: Default HTTP status code for responses (default: 200)
        default_content: Default response content as bytes or dict (default: {})
        default_headers: Default response headers (default: {})

    Example:
        >>> fake_backend = FakeHTTPBackend(
        ...     default_content={"message": "success"},
        ...     default_status=200
        ... )
        >>> config = Config(http_backend=fake_backend)
        >>> client = APIClient(config=config)
        >>> # Make requests - they'll be stored but not sent
        >>> # Check what was requested:
        >>> fake_backend.requests
    """

    def __init__(
        self,
        default_status: int = 200,
        default_content: bytes | dict[str, typing.Any] | None = None,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self.default_status = default_status
        self.default_content = default_content or {}
        self.default_headers = default_headers or {"content-type": "application/json"}

        # Storage for captured requests
        self.requests: list[dict[str, typing.Any]] = []

        # Allow configuring responses per request
        self._response_queue: list[tuple[int, typing.Any, dict[str, str]]] = []

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
        status: int = 200,
        content: bytes | dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Queue a specific response for the next request.

        Responses are consumed in FIFO order. If queue is empty,
        default response is used.

        Args:
            status: HTTP status code
            content: Response content (dict will be JSON-encoded)
            headers: Response headers
        """
        self._response_queue.append(
            (
                status,
                content if content is not None else self.default_content,
                headers if headers is not None else self.default_headers,
            )
        )

    def _get_next_response(self) -> tuple[int, typing.Any, dict[str, str]]:
        """Get the next response from queue or use defaults."""
        if self._response_queue:
            return self._response_queue.pop(0)
        return (self.default_status, self.default_content, self.default_headers)

    def _create_response(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        """Create a fake generic Response object."""
        # Capture the request
        self.requests.append(
            {
                "method": method,
                "url": url,
                "kwargs": kwargs,
            }
        )

        # Get response configuration
        status, content, headers = self._get_next_response()

        # Convert dict content to JSON bytes
        if isinstance(content, dict):
            import json

            content_bytes = json.dumps(content).encode("utf-8")
            if "content-type" not in headers:
                headers["content-type"] = "application/json"
        elif isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content or b""

        # Create a generic clientele Response
        return response.Response(
            status_code=status,
            content=content_bytes,
            headers=headers,
            request_method=method,
            request_url=url,
        )

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
        """
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
        """
        return self._create_response(method, url, **kwargs)

    def close(self) -> None:
        """No-op: FakeHTTPBackend has no resources to close."""
        pass

    async def aclose(self) -> None:
        """No-op: FakeHTTPBackend has no resources to close."""
        pass

    def reset(self) -> None:
        """Clear all captured requests and queued responses."""
        self.requests.clear()
        self._response_queue.clear()

        self._response_queue.clear()
