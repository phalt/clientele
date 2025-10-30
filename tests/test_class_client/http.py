from __future__ import annotations

import decimal
import json
import types
import typing
from urllib import parse

import httpx

from tests.test_class_client import config as c  # noqa


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


def parse_url(url: str, config: c.Config) -> str:
    """
    Returns the full URL from a string.

    Will filter out any optional query parameters if they are None.
    """
    api_url = f"{config.api_base_url}{url}"
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
    "complex_model_request_complex_model_request_get": {"200": "ComplexModelResponse"},
    "header_request_header_request_get": {"200": "HeadersResponse", "422": "HTTPValidationError"},
    "optional_parameters_request_optional_parameters_get": {"200": "OptionalParametersResponse"},
    "request_data_request_data_post": {"200": "RequestDataResponse", "422": "HTTPValidationError"},
    "request_data_request_data_put": {"200": "RequestDataResponse", "422": "HTTPValidationError"},
    "request_data_path_request_data": {"200": "RequestDataAndParameterResponse", "422": "HTTPValidationError"},
    "request_delete_request_delete_delete": {"200": "DeleteResponse"},
    "security_required_request_security_required_get": {"200": "SecurityRequiredResponse"},
    "query_request_simple_query_get": {"200": "SimpleQueryParametersResponse", "422": "HTTPValidationError"},
    "query_request_optional_query_get": {"200": "OptionalQueryParametersResponse", "422": "HTTPValidationError"},
    "simple_request_simple_request_get": {"200": "SimpleResponse"},
    "parameter_request_simple_request": {"200": "ParameterResponse", "422": "HTTPValidationError"},
}


class HTTPClient:
    """HTTP client wrapper that manages the httpx client with configuration."""

    def __init__(self, config: c.Config):
        self.config = config
        self._client: typing.Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the httpx client with current configuration."""
        if self._client is None:
            client_headers = self.config.additional_headers.copy()
            client_headers.update(Authorization=f"Bearer {self.config.bearer_token}")
            self._client = httpx.Client(headers=client_headers)
        return self._client

    def _get_headers(self, additional_headers: typing.Optional[dict] = None) -> dict:
        """Get headers for a request, merging config and request-specific headers."""
        headers = self.config.additional_headers.copy()
        headers.update(Authorization=f"Bearer {self.config.bearer_token}")
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def get(self, url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
        """Issue an HTTP GET request"""
        request_headers = self._get_headers(headers)
        client = self._get_client()
        return client.get(parse_url(url, self.config), headers=request_headers)

    def post(self, url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
        """Issue an HTTP POST request"""
        request_headers = self._get_headers(headers)
        json_data = json.loads(json.dumps(data, default=json_serializer))
        client = self._get_client()
        return client.post(parse_url(url, self.config), json=json_data, headers=request_headers)

    def put(self, url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
        """Issue an HTTP PUT request"""
        request_headers = self._get_headers(headers)
        json_data = json.loads(json.dumps(data, default=json_serializer))
        client = self._get_client()
        return client.put(parse_url(url, self.config), json=json_data, headers=request_headers)

    def patch(self, url: str, data: dict, headers: typing.Optional[dict] = None) -> httpx.Response:
        """Issue an HTTP PATCH request"""
        request_headers = self._get_headers(headers)
        json_data = json.loads(json.dumps(data, default=json_serializer))
        client = self._get_client()
        return client.patch(parse_url(url, self.config), json=json_data, headers=request_headers)

    def delete(self, url: str, headers: typing.Optional[dict] = None) -> httpx.Response:
        """Issue an HTTP DELETE request"""
        request_headers = self._get_headers(headers)
        client = self._get_client()
        return client.delete(parse_url(url, self.config), headers=request_headers)
