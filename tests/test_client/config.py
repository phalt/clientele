"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.

DO NOT CHANGE THE FUNCTION NAMES
"""

import httpx


def additional_headers() -> dict:
    """
    Modify this function to provide additional headers to all
    HTTP requests made by this client.
    """
    return {}


def api_base_url() -> str:
    """
    Modify this function to provide the current api_base_url.
    """
    return "http://localhost"


def get_user_key() -> str:
    """
    HTTP Basic authentication.
    Username parameter
    """
    return "user"


def get_pass_key() -> str:
    """
    HTTP Basic authentication.
    Password parameter
    """
    return "password"


def get_bearer_token() -> str:
    """
    HTTP Bearer authentication.
    Used by many authentication methods - token, jwt, etc.
    Does not require the "Bearer" content, just the key as a string.
    """
    return "token"


def get_timeout() -> float:
    """
    HTTP request timeout in seconds.
    Default is 5.0 seconds for all requests.
    Set to None for no timeout.
    """
    return 5.0


def get_follow_redirects() -> bool:
    """
    Whether to automatically follow HTTP redirects.
    Default is False.
    """
    return False


def get_verify_ssl() -> bool:
    """
    Whether to verify SSL certificates.
    Default is True. Set to False to disable SSL verification (not recommended for production).
    """
    return True


def get_http2() -> bool:
    """
    Whether to enable HTTP/2 support.
    Default is False.
    """
    return False


def get_max_redirects() -> int:
    """
    Maximum number of redirects to follow.
    Default is 20. Only applies when follow_redirects is True.
    """
    return 20


def get_limits() -> httpx.Limits | None:
    """
    Configure connection pool limits for the HTTP client.
    Return an httpx.Limits object to customize connection pooling behavior,
    or None to use httpx defaults.

    Example:
        return httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
            keepalive_expiry=5.0
        )

    Default is None (uses httpx defaults).
    """
    return None
