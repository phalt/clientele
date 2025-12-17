"""Tests for operation description support in generated clients."""

from __future__ import annotations

from .test_class_client.client import Client
from .test_client import client


def test_function_with_description_has_description_in_docstring():
    """Test that operations with descriptions have them in docstrings."""
    # Check the docstring contains both summary and description
    assert client.complex_model_request_complex_model_request_get.__doc__ is not None
    docstring = client.complex_model_request_complex_model_request_get.__doc__
    # Should contain the summary
    assert "Complex Model Request" in docstring
    # Should contain the description
    assert "A request that returns a complex model demonstrating various response types" in docstring


def test_function_with_only_summary_has_no_extra_content():
    """Test that operations with only summary don't have extra blank lines."""
    # Check the docstring for an operation that has only a summary
    assert client.header_request_header_request_get.__doc__ is not None
    docstring = client.header_request_header_request_get.__doc__
    # Should contain the summary
    assert "Header Request" in docstring
    # Should not contain any extended description
    # The docstring should be relatively short (just the summary)
    lines = [line.strip() for line in docstring.strip().split("\n") if line.strip()]
    assert len(lines) == 1  # Only the summary line


def test_post_method_with_description_has_description_in_docstring():
    """Test that POST operations with descriptions have them in docstrings."""
    # Check the docstring contains both summary and description
    assert client.request_data_request_data_post.__doc__ is not None
    docstring = client.request_data_request_data_post.__doc__
    # Should contain the summary
    assert "Request Data" in docstring
    # Should contain the description
    assert "An endpoint that takes input data from an HTTP POST request and returns it" in docstring


def test_deprecated_with_description_has_both():
    """Test that deprecated operations with descriptions have both in docstrings."""
    # Check the docstring contains summary, description, and deprecation warning
    assert client.deprecated_endpoint_deprecated_endpoint_get.__doc__ is not None
    docstring = client.deprecated_endpoint_deprecated_endpoint_get.__doc__
    # Should contain the summary
    assert "Deprecated Endpoint" in docstring
    # Should contain the description
    assert "An endpoint specifically for testing deprecated functionality" in docstring
    # Should contain deprecation warning
    assert "deprecated" in docstring.lower()


def test_class_method_with_description_has_description_in_docstring():
    """Test that class-based client operations with descriptions have them in docstrings."""
    test_client = Client()
    # Check the docstring contains both summary and description
    assert test_client.complex_model_request_complex_model_request_get.__doc__ is not None
    docstring = test_client.complex_model_request_complex_model_request_get.__doc__
    # Should contain the summary
    assert "Complex Model Request" in docstring
    # Should contain the description
    assert "A request that returns a complex model demonstrating various response types" in docstring


def test_class_method_deprecated_with_description_has_both():
    """Test that deprecated class-based operations with descriptions have both in docstrings."""
    test_client = Client()
    # Check the docstring contains summary, description, and deprecation warning
    assert test_client.deprecated_endpoint_deprecated_endpoint_get.__doc__ is not None
    docstring = test_client.deprecated_endpoint_deprecated_endpoint_get.__doc__
    # Should contain the summary
    assert "Deprecated Endpoint" in docstring
    # Should contain the description
    assert "An endpoint specifically for testing deprecated functionality" in docstring
    # Should contain deprecation warning
    assert "deprecated" in docstring.lower()
