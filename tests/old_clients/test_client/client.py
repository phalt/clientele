from __future__ import annotations

import typing  # noqa

from tests.old_clients.test_client import http, schemas  # noqa


def complex_model_request_complex_model_request_get() -> schemas.ComplexModelResponse:
    """Complex Model Request

    A request that returns a complex model demonstrating various response types
    """

    response = http.get(url="/complex-model-request")
    return http.handle_response(complex_model_request_complex_model_request_get, response)


def header_request_header_request_get(
    headers: typing.Optional[schemas.HeaderRequestHeaderRequestGetHeaders] = None,
) -> schemas.HTTPValidationError | schemas.HeadersResponse:
    """Header Request"""
    headers_dict: dict | None = headers.model_dump(by_alias=True, exclude_unset=True) if headers else None
    response = http.get(url="/header-request", headers=headers_dict)
    return http.handle_response(header_request_header_request_get, response)


def optional_parameters_request_optional_parameters_get() -> schemas.OptionalParametersResponse:
    """Optional Parameters Request

    A response with a a model that has optional input values
    """

    response = http.get(url="/optional-parameters")
    return http.handle_response(optional_parameters_request_optional_parameters_get, response)


def request_data_request_data_post(
    data: schemas.RequestDataRequest,
) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
    """Request Data

    An endpoint that takes input data from an HTTP POST request and returns it
    """

    response = http.post(url="/request-data", data=data.model_dump())
    return http.handle_response(request_data_request_data_post, response)


def request_data_request_data_put(
    data: schemas.RequestDataRequest,
) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
    """Request Data

    An endpoint that takes input data from an HTTP PUT request and returns it
    """

    response = http.put(url="/request-data", data=data.model_dump())
    return http.handle_response(request_data_request_data_put, response)


def request_data_path_request_data(
    path_parameter: str, data: schemas.RequestDataRequest
) -> schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse:
    """Request Data Path

    An endpoint that takes input data from an HTTP POST request and also a path parameter
    """

    response = http.post(url=f"/request-data/{path_parameter}", data=data.model_dump())
    return http.handle_response(request_data_path_request_data, response)


def request_delete_request_delete_delete() -> schemas.DeleteResponse:
    """Request Delete"""

    response = http.delete(url="/request-delete")
    return http.handle_response(request_delete_request_delete_delete, response)


def security_required_request_security_required_get() -> schemas.SecurityRequiredResponse:
    """Security Required Request"""

    response = http.get(url="/security-required")
    return http.handle_response(security_required_request_security_required_get, response)


def query_request_simple_query_get(
    your_input: str,
) -> schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse:
    """Query Request

    A request with a query parameters
    """

    response = http.get(url=f"/simple-query?yourInput={your_input}")
    return http.handle_response(query_request_simple_query_get, response)


def query_request_optional_query_get(
    your_input: typing.Optional[str] = None,
) -> schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse:
    """Optional Query Request

    A request with a query parameters that are optional
    """

    response = http.get(url=f"/optional-query?yourInput={your_input}")
    return http.handle_response(query_request_optional_query_get, response)


def simple_request_simple_request_get() -> schemas.SimpleResponse:
    """Simple Request

    A simple API request with no parameters.
    """

    response = http.get(url="/simple-request")
    return http.handle_response(simple_request_simple_request_get, response)


def parameter_request_simple_request(your_input: str) -> schemas.HTTPValidationError | schemas.ParameterResponse:
    """Parameter Request

    A request with a URL parameter
    """

    response = http.get(url=f"/simple-request/{your_input}")
    return http.handle_response(parameter_request_simple_request, response)


def deprecated_endpoint_deprecated_endpoint_get() -> schemas.SimpleResponse:
    """Deprecated Endpoint

    An endpoint specifically for testing deprecated functionality

    .. deprecated::
        This operation is deprecated and may be removed in a future version.
    """

    response = http.get(url="/deprecated-endpoint")
    return http.handle_response(deprecated_endpoint_deprecated_endpoint_get, response)


def nullable_fields_nullable_fields_post(
    data: schemas.NullableFieldsRequest,
) -> schemas.HTTPValidationError | schemas.NullableFieldsResponse:
    """Nullable Fields Request

    A request with nullable fields using OpenAPI 3.1.0 format
    """

    response = http.post(url="/nullable-fields", data=data.model_dump())
    return http.handle_response(nullable_fields_nullable_fields_post, response)
