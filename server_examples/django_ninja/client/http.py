from __future__ import annotations

import decimal
import json
import types
import typing
from urllib import parse

import httpx

from server_examples.django_ninja.client import config as c  # noqa
from server_examples.django_ninja.client import schemas  # noqa


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
    api_url = f"{c.config.api_base_url}{url}"
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
    # Get the response types, merging function's globals with schemas module for forward reference resolution
    # This handles both cases: schemas.ResponseType and type aliases like list[UserResponse]
    globalns = {**func.__globals__, **schemas.__dict__}
    response_types = typing.get_type_hints(func, globalns=globalns)["return"]

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

    # Handle None responses (e.g., 204 No Content)
    if expected_response_class_name == "None":
        return None

    # Get the correct response type and build it
    # First try to match by __name__ (works for classes)
    response_type = None
    for t in response_types:
        if hasattr(t, "__name__") and t.__name__ == expected_response_class_name:
            response_type = t
            break

    # If not found, try to get it from the schemas module (works for type aliases)
    if response_type is None and hasattr(schemas, expected_response_class_name):
        response_type = getattr(schemas, expected_response_class_name)

    if response_type is None:
        raise APIException(response=response, reason=f"Could not find response type {expected_response_class_name}")

    data = response.json()

    # Handle array/list responses
    if typing.get_origin(response_type) is list:
        # Get the item type from the list
        item_type = typing.get_args(response_type)[0]
        # Validate each item in the list
        return [item_type.model_validate(item) for item in data]
    else:
        # Regular model validation for single objects
        return response_type.model_validate(data)


# Func map
func_response_code_maps = {
    "list_users": {"200": "Response"},
    "create_user": {"200": "UserOut"},
    "get_user": {"200": "UserOut"},
}

client_headers = c.config.additional_headers.copy()
_client_kwargs: dict[str, typing.Any] = {
    "headers": client_headers,
    "timeout": c.config.timeout,
    "follow_redirects": c.config.follow_redirects,
    "verify": c.config.verify_ssl,
    "http2": c.config.http2,
    "max_redirects": c.config.max_redirects,
}
if _limits := c.config.limits:
    _client_kwargs["limits"] = _limits
if _transport := c.config.transport:
    _client_kwargs["transport"] = _transport
client = httpx.Client(**_client_kwargs)


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
