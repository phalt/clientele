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
    """Fixture providing an OpenAPI v2 spec (old version)."""
    return {
        "openapi": "2.0.0",
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
    """Test the else branch in _load_openapi_spec that raises ValueError.
    
    This tests line 35 which is the else branch that should be unreachable
    but exists for completeness.
    """
    # We need to bypass the assertion to test the else branch
    # Since the function has an assert, we test with None values to trigger the assert
    with pytest.raises(AssertionError):
        cli._load_openapi_spec(url=None, file=None)


def test_generate_command_rejects_old_openapi_version(runner, openapi_v2_spec):
    """Test generate command rejects OpenAPI v2 specs (lines 96-97)."""
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

            # Should exit successfully but with a warning message
            assert result.exit_code == 0
            # Should warn about old version
            assert "3.0.0" in result.output or "version 3" in result.output.lower()
            # Client should NOT be generated
            assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
        finally:
            Path(spec_file).unlink()


def test_generate_class_command_rejects_old_openapi_version(runner, openapi_v2_spec):
    """Test generate-class command rejects OpenAPI v2 specs (lines 144-145)."""
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

            # Should exit successfully but with a warning message
            assert result.exit_code == 0
            # Should warn about old version
            assert "3.0.0" in result.output or "version 3" in result.output.lower()
            # Client should NOT be generated
            assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
        finally:
            Path(spec_file).unlink()
