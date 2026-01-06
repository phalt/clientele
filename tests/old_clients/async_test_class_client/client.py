from __future__ import annotations

import typing  # noqa

from tests.old_clients.async_test_class_client import config as _config
from tests.old_clients.async_test_class_client import http, schemas  # noqa


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
        from tests.old_clients.async_test_class_client import config
        custom_config = config.Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token"
        )
        client = Client(config=custom_config)
    """

    def __init__(self, config: typing.Optional[_config.Config] = None):
        self.config = config or _config.Config()
        self._http_client = http.HTTPClient(self.config)

    async def complex_model_request_complex_model_request_get(self) -> schemas.ComplexModelResponse:
        """Complex Model Request

        A request that returns a complex model demonstrating various response types
        """

        response = await self._http_client.get(url="/complex-model-request")
        return http.handle_response(self.complex_model_request_complex_model_request_get, response)

    async def header_request_header_request_get(
        self, headers: typing.Optional[schemas.HeaderRequestHeaderRequestGetHeaders] = None
    ) -> schemas.HTTPValidationError | schemas.HeadersResponse:
        """Header Request"""
        headers_dict: dict | None = headers.model_dump(by_alias=True, exclude_unset=True) if headers else None
        response = await self._http_client.get(url="/header-request", headers=headers_dict)
        return http.handle_response(self.header_request_header_request_get, response)

    async def optional_parameters_request_optional_parameters_get(self) -> schemas.OptionalParametersResponse:
        """Optional Parameters Request

        A response with a a model that has optional input values
        """

        response = await self._http_client.get(url="/optional-parameters")
        return http.handle_response(self.optional_parameters_request_optional_parameters_get, response)

    async def request_data_request_data_post(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data

        An endpoint that takes input data from an HTTP POST request and returns it
        """

        response = await self._http_client.post(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_post, response)

    async def request_data_request_data_put(
        self, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataResponse:
        """Request Data

        An endpoint that takes input data from an HTTP PUT request and returns it
        """

        response = await self._http_client.put(url="/request-data", data=data.model_dump())
        return http.handle_response(self.request_data_request_data_put, response)

    async def request_data_path_request_data(
        self, path_parameter: str, data: schemas.RequestDataRequest
    ) -> schemas.HTTPValidationError | schemas.RequestDataAndParameterResponse:
        """Request Data Path

        An endpoint that takes input data from an HTTP POST request and also a path parameter
        """

        response = await self._http_client.post(url=f"/request-data/{path_parameter}", data=data.model_dump())
        return http.handle_response(self.request_data_path_request_data, response)

    async def request_delete_request_delete_delete(self) -> schemas.DeleteResponse:
        """Request Delete"""

        response = await self._http_client.delete(url="/request-delete")
        return http.handle_response(self.request_delete_request_delete_delete, response)

    async def security_required_request_security_required_get(self) -> schemas.SecurityRequiredResponse:
        """Security Required Request"""

        response = await self._http_client.get(url="/security-required")
        return http.handle_response(self.security_required_request_security_required_get, response)

    async def query_request_simple_query_get(
        self, your_input: str
    ) -> schemas.HTTPValidationError | schemas.SimpleQueryParametersResponse:
        """Query Request

        A request with a query parameters
        """

        response = await self._http_client.get(url=f"/simple-query?yourInput={your_input}")
        return http.handle_response(self.query_request_simple_query_get, response)

    async def query_request_optional_query_get(
        self, your_input: typing.Optional[str] = None
    ) -> schemas.HTTPValidationError | schemas.OptionalQueryParametersResponse:
        """Optional Query Request

        A request with a query parameters that are optional
        """

        response = await self._http_client.get(url=f"/optional-query?yourInput={your_input}")
        return http.handle_response(self.query_request_optional_query_get, response)

    async def simple_request_simple_request_get(self) -> schemas.SimpleResponse:
        """Simple Request

        A simple API request with no parameters.
        """

        response = await self._http_client.get(url="/simple-request")
        return http.handle_response(self.simple_request_simple_request_get, response)

    async def parameter_request_simple_request(
        self, your_input: str
    ) -> schemas.HTTPValidationError | schemas.ParameterResponse:
        """Parameter Request

        A request with a URL parameter
        """

        response = await self._http_client.get(url=f"/simple-request/{your_input}")
        return http.handle_response(self.parameter_request_simple_request, response)

    async def deprecated_endpoint_deprecated_endpoint_get(self) -> schemas.SimpleResponse:
        """Deprecated Endpoint

        An endpoint specifically for testing deprecated functionality

        .. deprecated::
            This operation is deprecated and may be removed in a future version.
        """

        response = await self._http_client.get(url="/deprecated-endpoint")
        return http.handle_response(self.deprecated_endpoint_deprecated_endpoint_get, response)

    async def nullable_fields_nullable_fields_post(
        self, data: schemas.NullableFieldsRequest
    ) -> schemas.HTTPValidationError | schemas.NullableFieldsResponse:
        """Nullable Fields Request

        A request with nullable fields using OpenAPI 3.1.0 format
        """

        response = await self._http_client.post(url="/nullable-fields", data=data.model_dump())
        return http.handle_response(self.nullable_fields_nullable_fields_post, response)
