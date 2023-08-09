import typing
from urllib.parse import urlparse

import httpx  # noqa
from pydantic import ValidationError  # noqa

from . import constants as c  # noqa


class APIException(Exception):
    """Could not match API response to return type of this function"""

    response: httpx.Response

    def __init__(self, response: httpx.Response, *args: object) -> None:
        self.response = response
        super().__init__(*args)


def parse_url(url: str) -> str:
    """
    Returns the base API URL for this service
    """
    api_url = f"{c.api_base_url()}{url}"
    url_parts = urlparse(url=api_url)
    return url_parts.geturl()


def handle_response(func, response):
    """
    Returns a response that matches the data neatly for a function
    If it can't - raises an error with details of the response.
    """
    response_data = response.json()
    response_types = typing.get_type_hints(func).get("return")
    if typing.get_origin(response_types) == typing.Union:
        response_types = list(typing.get_args(response_types))
    else:
        response_types = [response_types]

    for single_type in response_types:
        try:
            return single_type.model_validate(response_data)
        except ValidationError:
            continue
    # As a fall back, raise an exception with the response in it
    raise APIException(response=response)
