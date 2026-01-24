from __future__ import annotations

import json
import typing

from clientele.api import client as api_client
from clientele.http import Response, fake_backend
from clientele.http.status_codes import codes


def configure_client_for_testing(
    client: api_client.APIClient,
) -> fake_backend.FakeHTTPBackend:
    """Function that provides a FakeHTTPBackend for testing.

    This function takes an APIClient instance and
    configures it to use a FakeHTTPBackend.

    The function returns the FakeHTTPBackend instance so you can queue responses
    in your test.

    Args:
        client: An APIClient instance to configure with the fake backend.
    Returns:
        A FakeHTTPBackend instance configured with the client.

    """

    # Create the fake backend
    backend = fake_backend.FakeHTTPBackend()

    # Configure the client to use the fake backend
    config = client.config
    config.http_backend = backend
    client.configure(config=config)

    # Return the backend
    return backend


def _prep_content(data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None) -> bytes:
    if data is None:
        return b""
    if isinstance(data, str):
        return data.encode("utf-8")
    if isinstance(data, bytes):
        return data
    return json.dumps(data).encode("utf-8")


class ResponseFactory:
    @staticmethod
    def ok(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 200 OK Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.OK,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def created(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 201 Created Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.CREATED,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def accepted(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 202 Accepted Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.ACCEPTED,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def no_content(
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 204 No Content Response."""
        return Response(
            status_code=codes.NO_CONTENT,
            headers=headers or {},
            content=b"",
        )

    @staticmethod
    def bad_request(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 400 Bad Request Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.BAD_REQUEST,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def unauthorized(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 401 Unauthorized Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.UNAUTHORIZED,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def forbidden(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 403 Forbidden Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.FORBIDDEN,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def not_found(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 404 Not Found Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.NOT_FOUND,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )

    @staticmethod
    def internal_server_error(
        data: dict[str, typing.Any] | typing.List[typing.Any] | str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """Create a generic 500 Internal Server Error Response.

        Args:
            data: Optional JSON data to include in the response body.
        """
        return Response(
            status_code=codes.INTERNAL_SERVER_ERROR,
            headers=headers or {"Content-Type": "application/json"},
            content=_prep_content(data),
        )
