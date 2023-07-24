import typing
from os import environ  # noqa

import httpx  # noqa
from pydantic import ValidationError


def handle_response(func, response):
    """
    returns a response that matches the data neatly for a function
    """
    response.raise_for_status()
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
