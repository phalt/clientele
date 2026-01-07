from __future__ import annotations

import typing

from clientele import api as clientele_api
from tests.api_clients.test_client import config, schemas

client = clientele_api.APIClient(config=config.Config())


@client.get("/complex-model-request")
def complex_model_request_complex_model_request_get(
    result: schemas.ComplexModelResponse,
) -> schemas.ComplexModelResponse:
    """Complex Model Request

    A request that returns a complex model demonstrating various response types
    """
    return result


@client.get("/header-request", response_map={200: schemas.HeadersResponse, 422: schemas.HTTPValidationError})
def header_request_header_request_get(
    result: schemas.HTTPValidationError | schemas.HeadersResponse,
) -> schemas.HTTPValidationError | schemas.HeadersResponse:
    """Header Request"""
    return result


@client.get("/optional-parameters")
def optional_parameters_request_optional_parameters_get(
    result: schemas.OptionalParametersResponse,
) -> schemas.OptionalParametersResponse:
    """Optional Parameters Request

    A response with a a model that has optional input values
    """
    return result


@client.post("/request-data", response_map={200: schemas.RequestDataResponse, 422: schemas.HTTPValidationError})
def request_data_request_data_post(
    data: schemas.RequestDataRequest, result: schemas.HTTPValidationError | schemas.RequestDataResponse
) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
    """Request Data

    An endpoint that takes input data from an HTTP POST request and returns it
    """
    return result


@client.put("/request-data", response_map={200: schemas.RequestDataResponse, 422: schemas.HTTPValidationError})
def request_data_request_data_put(
    data: schemas.RequestDataRequest, result: schemas.HTTPValidationError | schemas.RequestDataResponse
) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
    """Request Data

    An endpoint that takes input data from an HTTP PUT request and returns it
    """
    return result


@client.post(
    "/request-data/{path_parameter}",
    response_map={200: schemas.RequestDataAndParameterResponse, 422: schemas.HTTPValidationError},
)
def request_data_path_request_data(
    path_parameter: str,
    data: schemas.RequestDataRequest,
    result: schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse,
) -> schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse:
    """Request Data Path

    An endpoint that takes input data from an HTTP POST request and also a path parameter
    """
    return result


@client.delete("/request-delete")
def request_delete_request_delete_delete(result: schemas.DeleteResponse) -> schemas.DeleteResponse:
    """Request Delete"""
    return result


@client.get("/security-required")
def security_required_request_security_required_get(
    result: schemas.SecurityRequiredResponse,
) -> schemas.SecurityRequiredResponse:
    """Security Required Request"""
    return result


@client.get(
    "/simple-query", response_map={200: schemas.SimpleQueryParametersResponse, 422: schemas.HTTPValidationError}
)
def query_request_simple_query_get(
    your_input: str, result: schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse
) -> schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse:
    """Query Request

    A request with a query parameters
    """
    return result


@client.get(
    "/optional-query", response_map={200: schemas.OptionalQueryParametersResponse, 422: schemas.HTTPValidationError}
)
def query_request_optional_query_get(
    result: schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse,
    your_input: typing.Optional[str] = None,
) -> schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse:
    """Optional Query Request

    A request with a query parameters that are optional
    """
    return result


@client.get("/simple-request")
def simple_request_simple_request_get(result: schemas.SimpleResponse) -> schemas.SimpleResponse:
    """Simple Request

    A simple API request with no parameters.
    """
    return result


@client.get(
    "/simple-request/{your_input}", response_map={200: schemas.ParameterResponse, 422: schemas.HTTPValidationError}
)
def parameter_request_simple_request(
    your_input: str, result: schemas.HTTPValidationError | schemas.ParameterResponse
) -> schemas.HTTPValidationError | schemas.ParameterResponse:
    """Parameter Request

    A request with a URL parameter
    """
    return result


@client.get("/deprecated-endpoint")
def deprecated_endpoint_deprecated_endpoint_get(result: schemas.SimpleResponse) -> schemas.SimpleResponse:
    """Deprecated Endpoint

    An endpoint specifically for testing deprecated functionality

    .. deprecated::
        This operation is deprecated and may be removed in a future version.
    """
    return result


@client.post("/nullable-fields", response_map={200: schemas.NullableFieldsResponse, 422: schemas.HTTPValidationError})
def nullable_fields_nullable_fields_post(
    data: schemas.NullableFieldsRequest, result: schemas.HTTPValidationError | schemas.NullableFieldsResponse
) -> schemas.HTTPValidationError | schemas.NullableFieldsResponse:
    """Nullable Fields Request

    A request with nullable fields using OpenAPI 3.1.0 format
    """
    return result
