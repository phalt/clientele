"""Tests for additional CLI coverage."""

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
def openapi_v2_spec():
    """Fixture providing a Swagger/OpenAPI v2 spec (old version)."""
    return {
        "swagger": "2.0",
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


def test_load_openapi_spec_else_branch():
    """Test assertion in _load_openapi_spec when neither url nor file provided.

    Note: The else branch on line 35 is unreachable defensive code because
    the assertion on line 28 catches this case first. We test the assertion here.
    """
    # Test that assertion fires when neither url nor file is provided
    with pytest.raises(AssertionError):
        cli._load_openapi_spec(url=None, file=None)


def test_generate_command_with_swagger_spec(runner, openapi_v2_spec):
    """Test generate command with Swagger 2.0 spec (gets auto-converted to 3.0).

    Note: Cicerone automatically converts Swagger 2.0 to OpenAPI 3.0, so the version
    check on lines 96-97 would only trigger for malformed specs, not valid Swagger 2.0.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v2_spec, f)
        spec_file = f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        try:
            result = runner.invoke(
                cli.cli_group,
                ["generate", "--file", spec_file, "--output", str(output_dir), "--regen", "true"],
            )

            # Should succeed (Swagger 2.0 is auto-converted to 3.0)
            assert result.exit_code == 0
        finally:
            Path(spec_file).unlink()


def test_generate_class_command_with_swagger_spec(runner, openapi_v2_spec):
    """Test generate-class command with Swagger 2.0 spec (gets auto-converted to 3.0).

    Note: Cicerone automatically converts Swagger 2.0 to OpenAPI 3.0, so the version
    check on lines 144-145 would only trigger for malformed specs, not valid Swagger 2.0.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v2_spec, f)
        spec_file = f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        try:
            result = runner.invoke(
                cli.cli_group,
                ["generate-class", "--file", spec_file, "--output", str(output_dir), "--regen", "true"],
            )

            # Should succeed (Swagger 2.0 is auto-converted to 3.0)
            assert result.exit_code == 0
        finally:
            Path(spec_file).unlink()
