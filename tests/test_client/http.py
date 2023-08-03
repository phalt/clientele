import typing
from os import environ  # noqa
from urllib.parse import urlparse

import httpx  # noqa
from pydantic import BaseModel, ValidationError  # noqa

from . import constants as c  # noqa


def parse_url(url: str) -> str:
    """
    Returns the base API URL for this service
    """
    api_url = f"{c.api_base_url()}{url}"
    url_parts = urlparse(url=api_url)
    return url_parts.geturl()


def handle_response(func, response):
    """
    returns a response that matches the data neatly for a function
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
    # As a fall back, return the response_data
    return response_data


auth_key = c.get_bearer_token()
headers = dict(Authorization="Bearer " + auth_key)
client = httpx.Client(headers=headers)


def get(url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
    return client.get(parse_url(url), headers=headers)


def post(url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
    return client.post(parse_url(url), json=data, headers=headers)


def delete(url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
    return client.delete(parse_url(url), headers=headers)
