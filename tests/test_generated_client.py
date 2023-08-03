import json

import pytest
from httpx import Response
from respx import MockRouter

from .test_client import client, constants, schemas

BASE_URL = constants.api_base_url()


@pytest.mark.respx(base_url=BASE_URL)
def test_simple_request_simple_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.simple_request_simple_request_get()
    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.respx(base_url=BASE_URL)
def test_optional_parameters_request_optional_parameters_get(respx_mock: MockRouter):
    # Given
    mocked_response = {"optional_parameter": None, "required_parameter": "Hello"}
    mock_path = "/optional-parameters"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.optional_parameters_request_optional_parameters_get()
    # Then
    assert isinstance(response, schemas.OptionalParametersResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.respx(base_url=BASE_URL)
def test_parameter_request_simple_request(respx_mock: MockRouter):
    # Given
    your_input = "hello world"
    mocked_response = {"your_input": your_input}
    mock_path = f"/simple-request/{your_input}"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.parameter_request_simple_request(your_input=your_input)
    # Then
    assert isinstance(response, schemas.ParameterResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.respx(base_url=BASE_URL)
def test_query_request_simple_query_get(respx_mock: MockRouter):
    # Given
    your_input = "hello world"
    mocked_response = {"your_query": your_input}
    mock_path = f"/simple-query?your_input={your_input}"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.query_request_simple_query_get(your_input=your_input)
    # Then
    assert isinstance(response, schemas.SimpleQueryParametersResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path


@pytest.mark.respx(base_url=BASE_URL)
def test_complex_model_request_complex_model_request_get(respx_mock: MockRouter):
    # Given
    mocked_response = {
        "a_dict_response": {"dict": "response"},
        "a_enum": "ONE",
        "a_list_of_enums": ["ONE", "TWO"],
        "a_list_of_numbers": [1, 2, 3],
        "a_list_of_other_models": [{"key": "first"}],
        "a_list_of_strings": ["hello", "world"],
        "a_number": 13,
        "a_string": "hello world",
        "another_model": {"key": "value"},
    }
    mock_path = "/complex-model-request"
    respx_mock.get(mock_path).mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    # When
    response = client.complex_model_request_complex_model_request_get()
    # Then
    assert isinstance(response, schemas.ComplexModelResponse)
    # Get around the enums
    json.loads(json.dumps(response.model_dump())) == mocked_response
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == BASE_URL + mock_path
