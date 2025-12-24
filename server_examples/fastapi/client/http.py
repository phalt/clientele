from __future__ import annotations

import decimal
import json
import types
import typing
from urllib import parse

import httpx

from server_examples.fastapi.client import config as c  # noqa


def json_serializer(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)


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
    Returns the full URL from a string.

    Will filter out any optional query parameters if they are None.
    """
    api_url = f"{c.api_base_url()}{url}"
    url_parts = parse.urlparse(url=api_url)
    # Filter out "None" optional query parameters
    filtered_query_params = {k: v for k, v in parse.parse_qs(url_parts.query).items() if v[0] not in ["None", ""]}
    filtered_query_string = parse.urlencode(filtered_query_params, doseq=True)
    return parse.urlunparse(
        (
            url_parts.scheme,
            url_parts.netloc,
            url_parts.path,
            url_parts.params,
            filtered_query_string,
            url_parts.fragment,
        )
    )


def handle_response(func, response):
    """
    Returns a schema object that matches the JSON data from the response.

    If it can't find a matching schema it will raise an error with details of the response.
    """
    status_code = response.status_code
    # Get the response types
    response_types = typing.get_type_hints(func)["return"]

    if typing.get_origin(response_types) in [typing.Union, types.UnionType]:
        response_types = list(typing.get_args(response_types))
    else:
        response_types = [response_types]

    # Determine, from the map, the correct response for this status code
    expected_responses = func_response_code_maps[func.__name__]  # noqa
    if str(status_code) not in expected_responses.keys():
        raise APIException(response=response, reason="An unexpected status code was received")
    else:
        expected_response_class_name = expected_responses[str(status_code)]

    # Get the correct response type and build it
    response_type = [t for t in response_types if t.__name__ == expected_response_class_name][0]
    data = response.json()
    return response_type.model_validate(data)


# Func map
func_response_code_maps = {
    "list_users": {"200": "ResponseListUsers"},
    "create_user": {"200": "UserResponse", "422": "HTTPValidationError"},
    "get_user": {"200": "UserResponse", "422": "HTTPValidationError"},
}

client_headers = c.additional_headers()
client = httpx.Client(headers=client_headers)


def get(url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
    """Issue an HTTP GET request"""
    if headers:
        client_headers.update(headers)
    return client.get(parse_url(url), headers=client_headers)


def post(url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
    """Issue an HTTP POST request"""
    if headers:
        client_headers.update(headers)
    json_data = json.loads(json.dumps(data, default=json_serializer))
    return client.post(parse_url(url), json=json_data, headers=client_headers)


def put(url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
    """Issue an HTTP PUT request"""
    if headers:
        client_headers.update(headers)
    json_data = json.loads(json.dumps(data, default=json_serializer))
    return client.put(parse_url(url), json=json_data, headers=client_headers)


def patch(url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
    """Issue an HTTP PATCH request"""
    if headers:
        client_headers.update(headers)
    json_data = json.loads(json.dumps(data, default=json_serializer))
    return client.patch(parse_url(url), json=json_data, headers=client_headers)


def delete(url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
    """Issue an HTTP DELETE request"""
    if headers:
        client_headers.update(headers)
    return client.delete(parse_url(url), headers=client_headers)
