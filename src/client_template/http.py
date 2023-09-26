import typing
from urllib.parse import urlparse

import httpx  # noqa

from . import constants as c  # noqa


class APIException(Exception):
    """Could not match API response to return type of this function"""

    reason: str
    response: httpx.Response

    def __init__(self, response: httpx.Response, reason: str, *args: object) -> None:
        self.response = response
        self.reason = reason
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
    status_code = response.status_code
    # Get the response types
    response_types = typing.get_type_hints(func)["return"]
    if typing.get_origin(response_types) == typing.Union:
        response_types = list(typing.get_args(response_types))
    else:
        response_types = [response_types]

    # Determine, from the map, the correct response for this status code
    expected_responses = func_response_code_maps[func.__name__]  # noqa
    if str(status_code) not in expected_responses.keys():
        raise APIException(
            response=response, reason="An unexpected status code was received"
        )
    else:
        expected_response_class_name = expected_responses[str(status_code)]

    # Get the correct response type and build it
    response_type = [
        t for t in response_types if t.__name__ == expected_response_class_name
    ][0]
    data = response.json()
    return response_type.model_validate(data)
