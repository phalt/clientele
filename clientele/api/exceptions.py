"""Exceptions for the clientele api.

They are defined in clientele.http.response, because the HTTP backends raise them.
"""

from clientele.http.response import APIException, HTTPStatusError

__all__ = [
    "APIException",
    "HTTPStatusError",
]
