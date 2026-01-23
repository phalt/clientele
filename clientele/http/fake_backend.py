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
        request_details = {
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
        self._response_map.clear()
