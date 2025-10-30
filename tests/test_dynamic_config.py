"""
Tests for dynamic configuration feature in class-based clients.
"""

import pytest
from httpx import Response
from respx import MockRouter

from .async_test_class_client import config as async_config
from .async_test_class_client import schemas as async_schemas
from .async_test_class_client.client import Client as AsyncClient
from .test_class_client import config, schemas
from .test_class_client.client import Client


def test_client_with_custom_base_url(respx_mock: MockRouter):
    """Test that client respects custom base URL from config"""
    # Given
    custom_url = "https://api.example.com"
    custom_config = config.Config(api_base_url=custom_url)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(f"{custom_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = Client(config=custom_config)
    response = client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == f"{custom_url}{mock_path}"


def test_client_with_custom_bearer_token(respx_mock: MockRouter):
    """Test that client uses custom bearer token from config"""
    # Given
    custom_token = "my-custom-token-12345"
    custom_config = config.Config(bearer_token=custom_token)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    base_url = "http://localhost"

    respx_mock.get(f"{base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = Client(config=custom_config)
    response = client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.headers.get("Authorization") == f"Bearer {custom_token}"


def test_client_with_additional_headers(respx_mock: MockRouter):
    """Test that client includes additional headers from config"""
    # Given
    custom_headers = {"X-Custom-Header": "custom-value", "X-Another": "another-value"}
    custom_config = config.Config(additional_headers=custom_headers)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    base_url = "http://localhost"

    respx_mock.get(f"{base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = Client(config=custom_config)
    response = client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.headers.get("X-Custom-Header") == "custom-value"
    assert call.request.headers.get("X-Another") == "another-value"


def test_multiple_clients_with_different_configs(respx_mock: MockRouter):
    """Test that multiple client instances can have different configurations"""
    # Given
    config1 = config.Config(api_base_url="https://api1.example.com", bearer_token="token1")
    config2 = config.Config(api_base_url="https://api2.example.com", bearer_token="token2")

    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"

    respx_mock.get(f"https://api1.example.com{mock_path}").mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    respx_mock.get(f"https://api2.example.com{mock_path}").mock(
        return_value=Response(json=mocked_response, status_code=200)
    )

    # When
    client1 = Client(config=config1)
    client2 = Client(config=config2)

    response1 = client1.simple_request_simple_request_get()
    response2 = client2.simple_request_simple_request_get()

    # Then
    assert isinstance(response1, schemas.SimpleResponse)
    assert isinstance(response2, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 2

    # Verify each client used its own configuration
    call1 = respx_mock.calls[0]
    assert call1.request.url == f"https://api1.example.com{mock_path}"
    assert call1.request.headers.get("Authorization") == "Bearer token1"

    call2 = respx_mock.calls[1]
    assert call2.request.url == f"https://api2.example.com{mock_path}"
    assert call2.request.headers.get("Authorization") == "Bearer token2"


def test_client_with_default_config(respx_mock: MockRouter):
    """Test that client works with default config when none provided"""
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    default_base_url = "http://localhost"

    respx_mock.get(f"{default_base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = Client()  # No config provided, should use defaults
    response = client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == f"{default_base_url}{mock_path}"
    # Should still have the default bearer token
    assert call.request.headers.get("Authorization") == "Bearer token"


# Async client tests


@pytest.mark.asyncio
async def test_async_client_with_custom_base_url(respx_mock: MockRouter):
    """Test that async client respects custom base URL from config"""
    # Given
    custom_url = "https://api.example.com"
    custom_config = async_config.Config(api_base_url=custom_url)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(f"{custom_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = AsyncClient(config=custom_config)
    response = await client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, async_schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == f"{custom_url}{mock_path}"


@pytest.mark.asyncio
async def test_async_client_with_custom_bearer_token(respx_mock: MockRouter):
    """Test that async client uses custom bearer token from config"""
    # Given
    custom_token = "my-async-token-12345"
    custom_config = async_config.Config(bearer_token=custom_token)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    base_url = "http://localhost"

    respx_mock.get(f"{base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = AsyncClient(config=custom_config)
    response = await client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, async_schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.headers.get("Authorization") == f"Bearer {custom_token}"


@pytest.mark.asyncio
async def test_async_client_with_additional_headers(respx_mock: MockRouter):
    """Test that async client includes additional headers from config"""
    # Given
    custom_headers = {"X-Async-Header": "async-value", "X-Test": "test-value"}
    custom_config = async_config.Config(additional_headers=custom_headers)
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    base_url = "http://localhost"

    respx_mock.get(f"{base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = AsyncClient(config=custom_config)
    response = await client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, async_schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.headers.get("X-Async-Header") == "async-value"
    assert call.request.headers.get("X-Test") == "test-value"


@pytest.mark.asyncio
async def test_async_multiple_clients_with_different_configs(respx_mock: MockRouter):
    """Test that multiple async client instances can have different configurations"""
    # Given
    config1 = async_config.Config(api_base_url="https://async1.example.com", bearer_token="async-token1")
    config2 = async_config.Config(api_base_url="https://async2.example.com", bearer_token="async-token2")

    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"

    respx_mock.get(f"https://async1.example.com{mock_path}").mock(
        return_value=Response(json=mocked_response, status_code=200)
    )
    respx_mock.get(f"https://async2.example.com{mock_path}").mock(
        return_value=Response(json=mocked_response, status_code=200)
    )

    # When
    client1 = AsyncClient(config=config1)
    client2 = AsyncClient(config=config2)

    response1 = await client1.simple_request_simple_request_get()
    response2 = await client2.simple_request_simple_request_get()

    # Then
    assert isinstance(response1, async_schemas.SimpleResponse)
    assert isinstance(response2, async_schemas.SimpleResponse)
    assert len(respx_mock.calls) == 2

    # Verify each client used its own configuration
    call1 = respx_mock.calls[0]
    assert call1.request.url == f"https://async1.example.com{mock_path}"
    assert call1.request.headers.get("Authorization") == "Bearer async-token1"

    call2 = respx_mock.calls[1]
    assert call2.request.url == f"https://async2.example.com{mock_path}"
    assert call2.request.headers.get("Authorization") == "Bearer async-token2"


@pytest.mark.asyncio
async def test_async_client_with_default_config(respx_mock: MockRouter):
    """Test that async client works with default config when none provided"""
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    default_base_url = "http://localhost"

    respx_mock.get(f"{default_base_url}{mock_path}").mock(return_value=Response(json=mocked_response, status_code=200))

    # When
    client = AsyncClient()  # No config provided, should use defaults
    response = await client.simple_request_simple_request_get()

    # Then
    assert isinstance(response, async_schemas.SimpleResponse)
    assert len(respx_mock.calls) == 1
    call = respx_mock.calls[0]
    assert call.request.url == f"{default_base_url}{mock_path}"
    # Should still have the default bearer token
    assert call.request.headers.get("Authorization") == "Bearer token"
