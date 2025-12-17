from __future__ import annotations

import typing  # noqa

from tests.test_class_client import config as _config
from tests.test_class_client import http, schemas  # noqa


class Client:
    """
    API Client for making requests.
    Use this client to make requests to the API endpoints.

    Args:
        config: Configuration object for the client. If not provided, uses default configuration.

    Example:
        # Use default configuration
        client = Client()

        # Use custom configuration
        from tests.test_class_client import config
        custom_config = config.Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token"
        )
        client = Client(config=custom_config)
    """

    def __init__(self, config: typing.Optional[_config.Config] = None):
        self.config = config or _config.Config()
        self._http_client = http.HTTPClient(self.config)

    def complex_model_request_complex_model_request_get(self) -> schemas.ComplexModelResponse:
        """Complex Model Request"""

        response = self._http_client.get(url="/complex-model-request")
        return http.handle_response(self.complex_model_request_complex_model_request_get, response)

    def header_request_header_request_get(
        self, headers: typing.Optional[schemas.HeaderRequestHeaderRequestGetHeaders]
    ) -> schemas.HTTPValidationError | schemas.HeadersResponse:
        """Header Request"""
        headers_dict = headers and headers.model_dump(by_alias=True, exclude_unset=True) or None
        response = self._http_client.get(url="/header-request", headers=headers_dict)
        return http.handle_response(self.header_request_header_request_get, response)

    def optional_parameters_request_optional_parameters_get(self) -> schemas.OptionalParametersResponse:
        """Optional Parameters Request"""

        response = self._http_client.get(url="/optional-parameters")
        return http.handle_response(self.optional_parameters_request_optional_parameters_get, response)

    def request_data_request_data_post(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data"""

        response = self._http_client.post(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_post, response)

    def request_data_request_data_put(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data"""

        response = self._http_client.put(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_put, response)

    def request_data_path_request_data(
        self, path_parameter: str, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse:
        """Request Data Path"""

        response = self._http_client.post(url=f"/request-data/{path_parameter}", data=data.model_dump())
        return http.handle_response(self.request_data_path_request_data, response)

    def request_delete_request_delete_delete(self) -> schemas.DeleteResponse:
        """Request Delete

        .. deprecated::
            This operation is deprecated and may be removed in a future version.
        """

        response = self._http_client.delete(url="/request-delete")
        return http.handle_response(self.request_delete_request_delete_delete, response)

    def security_required_request_security_required_get(self) -> schemas.SecurityRequiredResponse:
        """Security Required Request"""

        response = self._http_client.get(url="/security-required")
        return http.handle_response(self.security_required_request_security_required_get, response)

    def query_request_simple_query_get(
        self, yourInput: str
    ) -> schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse:
        """Query Request"""

        response = self._http_client.get(url=f"/simple-query?yourInput={yourInput}")
        return http.handle_response(self.query_request_simple_query_get, response)

    def query_request_optional_query_get(
        self, yourInput: typing.Optional[str]
    ) -> schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse:
        """Optional Query Request"""

        response = self._http_client.get(url=f"/optional-query?yourInput={yourInput}")
        return http.handle_response(self.query_request_optional_query_get, response)

    def simple_request_simple_request_get(self) -> schemas.SimpleResponse:
        """Simple Request

        .. deprecated::
            This operation is deprecated and may be removed in a future version.
        """

        response = self._http_client.get(url="/simple-request")
        return http.handle_response(self.simple_request_simple_request_get, response)

    def parameter_request_simple_request(
        self, your_input: str
    ) -> schemas.HTTPValidationError | schemas.ParameterResponse:
        """Parameter Request"""

        response = self._http_client.get(url=f"/simple-request/{your_input}")
        return http.handle_response(self.parameter_request_simple_request, response)
