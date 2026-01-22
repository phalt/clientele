from __future__ import annotations

import typing

import stamina

from clientele.api import exceptions as api_exceptions


def retry(
    *,
    attempts: int,
    on_status: typing.List[int] | None = None,
):
    """Decorator to retry API calls with configurable exception handling.

    This is a wrapper around stamina.retry that allows you to specify which
    exceptions to retry on. It should be applied ABOVE the @client.get() decorator:

        from clientele import retries

        @retries.retry(attempts=4, on_status=[500, 502, 503, 504])
        @client.get("/pokemon/{id}")
        def get_pokemon(id: int, result: dict) -> dict:
            return result

    Args:
        attempts: Number of retry attempts
        on_status: List of HTTP status codes to retry on (defaults to any 5XX code)

    Returns:
        Decorated function with retry behavior

    Examples:
        >>> # Simple example
        >>> @retries.retry(attempts=4)
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result

        >>> # Retry on specific status codes
        >>> @retries.retry(attempts=4, on_status=[500, 502, 503, 504])
        >>> @client.get("/pokemon/{id}")
        >>> def get_pokemon(id: int, result: dict) -> dict:
        >>>     return result
    """

    def _custom_on_handler(exc: Exception) -> bool:
        if isinstance(exc, api_exceptions.APIException):
            if on_status is not None:
                return exc.response.status_code in on_status
            # Default to retrying on any 5XX status code
            return exc.response.status_code >= 500
        return False

    return stamina.retry(
        on=_custom_on_handler,
        attempts=attempts,
    )
