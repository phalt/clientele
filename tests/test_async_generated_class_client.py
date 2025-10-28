"""
Identical to the normal class client tests but just using
the async client instead
"""

from decimal import Decimal

import pytest
from httpx import Response
from respx import MockRouter

from .async_test_class_client import config, http, schemas
from .async_test_class_client.client import Client

BASE_URL = config.api_base_url()


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_simple_request_simple_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.simple_request_simple_request_get()
    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_simple_request_simple_request_get_raises_exception(
    respx_mock: MockRouter,
):
    # Given
    mocked_response = {"bad": "response"}
    mock_path = "/simple-request"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=404))
    # Then
    client = Client()
    with pytest.raises(http.APIException) as raised_exception:
        await client.simple_request_simple_request_get()
    assert isinstance(raised_exception.value, http.APIException)
    # Make sure we have the response on the exception
    assert raised_exception.value.response.status_code == 404
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_optional_parameters_request_optional_parameters_get(
    respx_mock: MockRouter,
):
    # Given
    mocked_response = {"optional_parameter": None, "required_parameter": "Hello"}
    mock_path = "/optional-parameters"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.optional_parameters_request_optional_parameters_get()
    # Then
    assert isinstance(response, schemas.OptionalParametersResponse)
    assert response.required_parameter == "Hello"
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_parameter_request_simple_request(respx_mock: MockRouter):
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request/test_parameter"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.parameter_request_simple_request_parameter_get(
        parameter="test_parameter"
    )
    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_query_request_simple_query_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"response": "hello world"}
    mock_path = "/simple-query"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.query_request_simple_query_get(yourInput="test")
    # Then
    assert isinstance(response, schemas.SimpleQueryParametersResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path + "?yourInput=test"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_query_request_optional_query_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"response": "hello world"}
    mock_path = "/optional-query"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.query_request_optional_query_get(yourInput=None)
    # Then
    assert isinstance(response, schemas.SimpleQueryParametersResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    # No query parameter should be included in the URL since it's None
    assert call.request.url.path == "/optional-query"


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_complex_model_request_complex_model_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {
        "a_dict_response": {"key1": "value1", "key2": "value2"},
        "a_enum": "OPTION_A",
        "a_list_of_enums": ["OPTION_A", "OPTION_B"],
        "a_list_of_numbers": [1, 2, 3, 4, 5],
        "a_list_of_other_models": [{"key": "value"}],
        "a_model": {"key": "value"},
        "a_number": 42,
        "a_string": "Hello",
        "a_decimal": "1.23",
    }
    mock_path = "/complex-model-request"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.complex_model_request_complex_model_request_get()
    # Then
    assert isinstance(response, schemas.ComplexModelResponse)
    assert response.a_string == "Hello"
    assert response.a_number == 42
    assert response.a_decimal == Decimal("1.23")
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_request_data_request_data_post(respx_mock: MockRouter):
    # Given
    mocked_response = {"my_response": "hello world"}
    mock_path = "/request-data"
    respx_mock.post(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    request_data = schemas.RequestDataRequest(my_input="test")
    response = await client.request_data_request_data_post(data=request_data)
    # Then
    assert isinstance(response, schemas.RequestDataResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_request_data_request_data_put(respx_mock: MockRouter):
    # Given
    mocked_response = {"my_response": "hello world"}
    mock_path = "/request-data"
    respx_mock.put(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    request_data = schemas.RequestDataRequest(my_input="test")
    response = await client.request_data_request_data_put(data=request_data)
    # Then
    assert isinstance(response, schemas.RequestDataResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_request_data_path_request_data(respx_mock: MockRouter):
    # Given
    mocked_response = {"parameter": "test_parameter", "my_response": "hello world"}
    mock_path = "/request-data/test_parameter"
    respx_mock.post(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    request_data = schemas.RequestDataRequest(my_input="test")
    response = await client.request_data_path_request_data(
        path_parameter="test_parameter", data=request_data
    )
    # Then
    assert isinstance(response, schemas.RequestDataAndParameterResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_request_delete_request_delete_delete(respx_mock: MockRouter):
    # Given
    mocked_response = {"status": "deleted"}
    mock_path = "/request-delete"
    respx_mock.delete(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    response = await client.request_delete_request_delete_delete()
    # Then
    assert isinstance(response, schemas.DeleteResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.asyncio
@pytest.mark.respx(base_url=BASE_URL)
async def test_header_request_header_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"x_my_header": "test"}
    mock_path = "/header-request"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    client = Client()
    headers = schemas.HeaderRequestHeaderRequestGetHeaders(x_my_header="test")
    response = await client.header_request_header_request_get(headers=headers)
    # Then
    assert isinstance(response, schemas.HeadersResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path
    assert call.request.headers.get("x-my-header") == "test"
