from __future__ import annotations

import typing  # noqa

from tests.test_class_client import http, schemas  # noqa


class Client:
    """
    API Client for making requests.
    Use this client to make requests to the API endpoints.
    """

    def __init__(self):
        pass

    def complex_model_request_complex_model_request_get(self) -> schemas.ComplexModelResponse:
        """Complex Model Request"""

        response = http.get(url="/complex-model-request")
        return http.handle_response(self.complex_model_request_complex_model_request_get, response)

    def header_request_header_request_get(
        self, headers: typing.Optional[schemas.HeaderRequestHeaderRequestGetHeaders]
    ) -> schemas.HTTPValidationError | schemas.HeadersResponse:
        """Header Request"""
        headers_dict = headers and headers.model_dump(by_alias=True, exclude_unset=True) or None
        response = http.get(url="/header-request", headers=headers_dict)
        return http.handle_response(self.header_request_header_request_get, response)

    def optional_parameters_request_optional_parameters_get(self) -> schemas.OptionalParametersResponse:
        """Optional Parameters Request"""

        response = http.get(url="/optional-parameters")
        return http.handle_response(self.optional_parameters_request_optional_parameters_get, response)

    def request_data_request_data_post(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data"""

        response = http.post(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_post, response)

    def request_data_request_data_put(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data"""

        response = http.put(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_put, response)

    def request_data_path_request_data(
        self, path_parameter: str, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse:
        """Request Data Path"""

        response = http.post(url=f"/request-data/{path_parameter}", data=data.model_dump())
        return http.handle_response(self.request_data_path_request_data, response)

    def request_delete_request_delete_delete(self) -> schemas.DeleteResponse:
        """Request Delete"""

        response = http.delete(url="/request-delete")
        return http.handle_response(self.request_delete_request_delete_delete, response)

    def security_required_request_security_required_get(self) -> schemas.SecurityRequiredResponse:
        """Security Required Request"""

        response = http.get(url="/security-required")
        return http.handle_response(self.security_required_request_security_required_get, response)

    def query_request_simple_query_get(
        self, yourInput: str
    ) -> schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse:
        """Query Request"""

        response = http.get(url=f"/simple-query?yourInput={yourInput}")
        return http.handle_response(self.query_request_simple_query_get, response)

    def query_request_optional_query_get(
        self, yourInput: typing.Optional[str]
    ) -> schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse:
        """Optional Query Request"""

        response = http.get(url=f"/optional-query?yourInput={yourInput}")
        return http.handle_response(self.query_request_optional_query_get, response)

    def simple_request_simple_request_get(self) -> schemas.SimpleResponse:
        """Simple Request"""

        response = http.get(url="/simple-request")
        return http.handle_response(self.simple_request_simple_request_get, response)

    def parameter_request_simple_request(
        self, your_input: str
    ) -> schemas.HTTPValidationError | schemas.ParameterResponse:
        """Parameter Request"""

        response = http.get(url=f"/simple-request/{your_input}")
        return http.handle_response(self.parameter_request_simple_request, response)
