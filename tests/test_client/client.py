import typing  # noqa
from . import schemas  # noqa
from . import http  # noqa


def complex_model_request_complex_model_request_get() -> schemas.ComplexModelResponse:
    """Complex Model Request"""

    response = http.get(url="/complex-model-request")
    return http.handle_response(
        complex_model_request_complex_model_request_get, response
    )


def header_request_header_request_get(
    headers: typing.Optional[schemas.HeaderRequestHeaderRequestGetHeaders],
) -> typing.Union[schemas.HeadersResponse, schemas.HTTPValidationError]:
    """Header Request"""
    headers_dict = headers and headers.model_dump(by_alias=True) or None
    response = http.get(url="/header-request", headers=headers_dict)
    return http.handle_response(header_request_header_request_get, response)


def optional_parameters_request_optional_parameters_get() -> (
    schemas.OptionalParametersResponse
):
    """Optional Parameters Request"""

    response = http.get(url="/optional-parameters")
    return http.handle_response(
        optional_parameters_request_optional_parameters_get, response
    )


def request_data_request_data_post(
    data: schemas.RequestDataRequest,
) -> typing.Union[schemas.RequestDataResponse, schemas.HTTPValidationError]:
    """Request Data"""

    response = http.post(url="/request-data", data=data.model_dump())
    return http.handle_response(request_data_request_data_post, response)


def request_data_path_request_data(
    path_parameter: str, data: schemas.RequestDataRequest
) -> typing.Union[schemas.RequestDataAndParameterResponse, schemas.HTTPValidationError]:
    """Request Data Path"""

    response = http.post(url=f"/request-data/{path_parameter}", data=data.model_dump())
    return http.handle_response(request_data_path_request_data, response)


def request_delete_request_delete_delete() -> schemas.DeleteResponse:
    """Request Delete"""

    response = http.delete(url="/request-delete")
    return http.handle_response(request_delete_request_delete_delete, response)


def security_required_request_security_required_get() -> (
    schemas.SecurityRequiredResponse
):
    """Security Required Request"""

    response = http.get(url="/security-required")
    return http.handle_response(
        security_required_request_security_required_get, response
    )


def query_request_simple_query_get(
    your_input: str,
) -> typing.Union[schemas.SimpleQueryParametersResponse, schemas.HTTPValidationError]:
    """Query Request"""

    response = http.get(url=f"/simple-query?your_input={your_input}")
    return http.handle_response(query_request_simple_query_get, response)


def simple_request_simple_request_get() -> schemas.SimpleResponse:
    """Simple Request"""

    response = http.get(url="/simple-request")
    return http.handle_response(simple_request_simple_request_get, response)


def parameter_request_simple_request(
    your_input: str,
) -> typing.Union[schemas.ParameterResponse, schemas.HTTPValidationError]:
    """Parameter Request"""

    response = http.get(url=f"/simple-request/{your_input}")
    return http.handle_response(parameter_request_simple_request, response)
