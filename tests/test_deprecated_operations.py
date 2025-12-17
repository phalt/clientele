"""Tests for deprecated operations support in generated clients."""

import warnings

import pytest
from httpx import Response
from respx import MockRouter

from .test_client import client, config, schemas
from .test_class_client.client import Client

BASE_URL = config.api_base_url()


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_function_has_deprecation_warning_in_docstring():
    """Test that deprecated operations have deprecation warning in docstring."""
    # Check the docstring contains deprecation warning
    assert client.simple_request_simple_request_get.__doc__ is not None
    docstring = client.simple_request_simple_request_get.__doc__
    assert "deprecated" in docstring.lower() or "warning" in docstring.lower()


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_delete_function_has_deprecation_warning_in_docstring():
    """Test that deprecated DELETE operations have deprecation warning in docstring."""
    # Check the docstring contains deprecation warning
    assert client.request_delete_request_delete_delete.__doc__ is not None
    docstring = client.request_delete_request_delete_delete.__doc__
    assert "deprecated" in docstring.lower() or "warning" in docstring.lower()


@pytest.mark.respx(base_url=BASE_URL)
def test_non_deprecated_function_has_no_deprecation_warning():
    """Test that non-deprecated operations don't have deprecation warnings."""
    # Check the docstring does not contain deprecation warning
    assert client.parameter_request_simple_request.__doc__ is not None
    docstring = client.parameter_request_simple_request.__doc__
    # Should not contain deprecation warning
    assert "deprecated" not in docstring.lower() and "warning" not in docstring.lower()


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_class_method_has_deprecation_warning_in_docstring():
    """Test that deprecated operations in class-based client have deprecation warning."""
    test_client = Client()
    # Check the docstring contains deprecation warning
    assert test_client.simple_request_simple_request_get.__doc__ is not None
    docstring = test_client.simple_request_simple_request_get.__doc__
    assert "deprecated" in docstring.lower() or "warning" in docstring.lower()


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_class_delete_method_has_deprecation_warning_in_docstring():
    """Test that deprecated DELETE operations in class-based client have deprecation warning."""
    test_client = Client()
    # Check the docstring contains deprecation warning
    assert test_client.request_delete_request_delete_delete.__doc__ is not None
    docstring = test_client.request_delete_request_delete_delete.__doc__
    assert "deprecated" in docstring.lower() or "warning" in docstring.lower()


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_function_still_works(respx_mock: MockRouter):
    """Test that deprecated operations still function correctly."""
    # Given
    mocked_response = {"status": "hello world"}
    mock_path = "/simple-request"
    respx_mock.get(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    response = client.simple_request_simple_request_get()
    # Then
    assert isinstance(response, schemas.SimpleResponse)
    assert response.status == "hello world"
    assert len(respx_mock.calls) == 1


@pytest.mark.respx(base_url=BASE_URL)
def test_deprecated_delete_function_still_works(respx_mock: MockRouter):
    """Test that deprecated DELETE operations still function correctly."""
    # Given
    mocked_response = {"status": "deleted"}
    mock_path = "/request-delete"
    respx_mock.delete(mock_path).mock(return_value=Response(json=mocked_response, status_code=200))
    # When
    response = client.request_delete_request_delete_delete()
    # Then
    assert isinstance(response, schemas.DeleteResponse)
    assert len(respx_mock.calls) == 1
