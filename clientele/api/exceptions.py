"""Exceptions for the clientele api."""

from __future__ import annotations

from clientele.http import response


class APIException(Exception):
    """Could not match API response to return type of this function."""

    reason: str
    response: response.Response

    def __init__(self, response: response.Response, reason: str, *args: object) -> None:
        self.response = response
        self.reason = reason
        super().__init__(*args)


class HTTPStatusError(APIException):
    """HTTP response returned an error status code (4xx or 5xx)."""

    def __init__(self, response: response.Response, reason: str, *args: object) -> None:
        super().__init__(response, reason, *args)
