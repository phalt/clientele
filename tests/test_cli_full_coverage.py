"""Tests for CLI module to achieve full coverage."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from clientele import cli


@pytest.fixture
def runner():
    """Fixture providing a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def openapi_v1_spec():
    """Fixture providing an OpenAPI v1 spec (old version that should fail)."""
    return {
        "openapi": "1.0.0",
        "info": {"title": "Old API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


@pytest.fixture
def openapi_v2_spec():
    """Fixture providing an OpenAPI v2 spec."""
    return {
        "openapi": "2.9.0",
        "info": {"title": "Old API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


@pytest.fixture
def openapi_v3_spec():
    """Fixture providing a valid OpenAPI v3 spec."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


def test_prepare_spec_returns_none_for_old_version(openapi_v2_spec):
    """Test that _prepare_spec returns None for OpenAPI version < 3.0."""
    from rich.console import Console

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v2_spec, f)
        spec_file = f.name

    try:
        console = Console()
        spec = cli._prepare_spec(console=console, file=spec_file)
        # Should return None for version < 3.0
        assert spec is None
    finally:
        Path(spec_file).unlink()


def test_load_openapi_spec_normalizes_openapi_31(openapi_v3_spec):
    """Test that _load_openapi_spec normalizes OpenAPI 3.1 specs."""
    # Create an OpenAPI 3.1 spec with nullable array syntax
    openapi_31_spec = {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": ["string", "null"],  # OpenAPI 3.1 nullable syntax
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_31_spec, f)
        spec_file = f.name

    try:
        spec = cli._load_openapi_spec(file=spec_file)
        # Should successfully load and normalize the spec
        assert spec is not None
        assert spec.info.title == "Test API"
    finally:
        Path(spec_file).unlink()
