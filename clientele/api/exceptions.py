"""Exceptions for the clientele api."""

from __future__ import annotations

import httpx


class APIException(Exception):
    """Could not match API response to return type of this function."""

    reason: str
    response: httpx.Response

    def __init__(self, response: httpx.Response, reason: str, *args: object) -> None:
        self.response = response
        self.reason = reason
        super().__init__(*args)
