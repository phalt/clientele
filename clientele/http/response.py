"""Generic HTTP response abstraction.

This module provides a backend-agnostic response interface that any
HTTP backend can implement, allowing clientele to work with different
HTTP libraries without being coupled to httpx.
"""

from __future__ import annotations

import typing


class Response:
    """Generic HTTP response interface.

    This class provides a common interface for HTTP responses across
    different backend implementations.

    Backend implementations should convert their native response objects
    to this interface.
    """

    def __init__(
        self,
        *,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        text: str | None = None,
        request_method: str = "GET",
        request_url: str = "",
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self._text = text
        self.request_method = request_method
        self.request_url = request_url

    @property
    def text(self) -> str:
        """Get response content as text."""
        if self._text is None:
            self._text = self.content.decode("utf-8")
        return self._text

    def json(self) -> typing.Any:
        """Parse response content as JSON.

        Returns:
            Parsed JSON object (dict, list, etc.)

        Raises:
            ValueError: If content is not valid JSON
        """
        import json

        return json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise an exception if status code indicates an error.

        Raises:
            HTTPStatusError: If status code is 4xx or 5xx
        """
        if 400 <= self.status_code < 600:
            # Import here to avoid circular dependency
            from clientele.api import exceptions as api_exceptions

            raise api_exceptions.HTTPStatusError(
                response=self,
                reason=f"HTTP {self.status_code}",
            )

    def __repr__(self) -> str:
        return f"<Clientele HTTP Response [{self.status_code}]>"
