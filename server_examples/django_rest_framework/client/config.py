"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.

DO NOT CHANGE THE FUNCTION NAMES
"""


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
