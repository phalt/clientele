"""Tests for deprecated operations support in generated clients."""

from __future__ import annotations

from .test_class_client.client import Client
from .test_client import client


def test_deprecated_function_has_deprecation_warning_in_docstring():
    """Test that deprecated operations have deprecation warning in docstring."""
    # Check the docstring contains deprecation warning
    assert client.deprecated_endpoint_deprecated_endpoint_get.__doc__ is not None
    docstring = client.deprecated_endpoint_deprecated_endpoint_get.__doc__
    assert "deprecated" in docstring.lower()


def test_non_deprecated_function_has_no_deprecation_warning():
    """Test that non-deprecated operations don't have deprecation warnings."""
    # Check the docstring does not contain deprecation warning
    assert client.simple_request_simple_request_get.__doc__ is not None
    docstring = client.simple_request_simple_request_get.__doc__
    # Should not contain deprecation warning
    assert "deprecated" not in docstring.lower()


def test_deprecated_class_method_has_deprecation_warning_in_docstring():
    """Test that deprecated operations in class-based client have deprecation warning."""
    test_client = Client()
    # Check the docstring contains deprecation warning
    assert test_client.deprecated_endpoint_deprecated_endpoint_get.__doc__ is not None
    docstring = test_client.deprecated_endpoint_deprecated_endpoint_get.__doc__
    assert "deprecated" in docstring.lower()
