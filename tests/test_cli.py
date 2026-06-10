"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from clientele import cli
from tests.generators.integration_utils import get_spec_path


@pytest.fixture
def runner():
    """Fixture providing a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def simple_openapi_spec():
    """Fixture providing a simple OpenAPI spec."""
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


@pytest.fixture
def write_spec_file(tmp_path, simple_openapi_spec):
    """Create an OpenAPI spec file with the requested suffix."""

    def _write(suffix: str, spec: dict | None = None) -> Path:
        spec_path = tmp_path / f"spec{suffix}"
        payload = spec or simple_openapi_spec
        if suffix in {".yaml", ".yml"}:
            spec_path.write_text(yaml.dump(payload))
        else:
            spec_path.write_text(json.dumps(payload))
        return spec_path

    return _write


def test_version_command(runner):
    """Test the version command displays version."""
    from clientele import settings

    result = runner.invoke(cli.cli_group, ["version"])
    assert result.exit_code == 0
    assert "clientele" in result.output
    assert settings.VERSION in result.output


@pytest.mark.parametrize("command", ["start-api"])
def test_generate_commands_require_output_parameter(runner, command):
    """Test that all generate commands require --output parameter."""
    result = runner.invoke(cli.cli_group, [command])
    # Should fail because required parameter --output is missing
    assert result.exit_code != 0
    assert "--output" in result.output or "output" in result.output.lower()


def test_generate_basic_command_creates_files(runner):
    """Test start-api command creates basic file structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "basic_client"

        runner.invoke(
            cli.cli_group,
            ["start-api", "--output", str(output_dir)],
        )

        # Should create output directory
        assert output_dir.exists()
        # Check for at least some files created
        assert len(list(output_dir.iterdir())) > 0


@pytest.mark.parametrize("suffix", [".json", ".yaml"])
def test_load_openapi_spec_from_file(write_spec_file, suffix):
    """Test loading OpenAPI spec from a file."""

    spec_file = write_spec_file(suffix)
    spec = cli._load_openapi_spec(file=str(spec_file))
    assert spec is not None
    assert spec.info.title == "Test API"


def test_load_openapi_spec_requires_url_or_file():
    """Test that _load_openapi_spec requires either URL or file."""
    with pytest.raises(AssertionError):
        cli._load_openapi_spec()


def test_load_openapi_spec_normalizes_openapi_31(write_spec_file):
    """Test that _load_openapi_spec normalizes OpenAPI 3.1 specs."""
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

    spec_file = write_spec_file(".json", spec=openapi_31_spec)
    spec = cli._load_openapi_spec(file=str(spec_file))
    # Should successfully load and normalize the spec
    assert spec is not None
    assert spec.info.title == "Test API"


@pytest.mark.parametrize(
    "content_type,serializer",
    [
        ("application/x-yaml", yaml.dump),
        ("application/json", json.dumps),
    ],
)
def test_load_openapi_spec_from_url(simple_openapi_spec, httpserver, content_type, serializer):
    """Test loading OpenAPI spec from URL for multiple content types."""

    httpserver.expect_request("/openapi").respond_with_data(
        serializer(simple_openapi_spec),
        content_type=content_type,
    )

    url = httpserver.url_for("/openapi")
    spec = cli._load_openapi_spec(url=url)
    assert spec is not None
    assert spec.info.title == "Test API"


def test_prepare_spec_returns_none_for_old_version(write_spec_file):
    """Test that _prepare_spec returns None for OpenAPI version < 3.0."""
    from rich.console import Console

    openapi_v2_spec = {
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

    spec_file = write_spec_file(".json", spec=openapi_v2_spec)
    spec = cli._prepare_spec(console=Console(), file=str(spec_file))
    # Should return None for version < 3.0
    assert spec is None


@pytest.mark.parametrize(
    "command,regen_arg,expected_output",
    [
        ("start-api", ["--regen"], "generated"),
    ],
)
def test_generate_commands_with_valid_spec(runner, command, regen_arg, expected_output):
    """Test that all generate commands create client successfully with valid spec."""
    # Use the simple spec from example_openapi_specs
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        result = runner.invoke(
            cli.cli_group,
            [command, "--file", str(spec_path), "--output", str(output_dir)] + regen_arg,
        )

        # Should succeed
        assert result.exit_code == 0
        assert expected_output.lower() in result.output.lower()


def test_start_api_command_with_swagger_spec(runner, write_spec_file):
    """Test start-api command with Swagger 2.0 spec (gets auto-converted to 3.0).

    Note: Cicerone automatically converts Swagger 2.0 to OpenAPI 3.0, so the
    pre-3.0 version check would only trigger for malformed specs, not valid
    Swagger 2.0.
    """
    swagger_v2_spec = {
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

    spec_file = write_spec_file(".json", spec=swagger_v2_spec)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        result = runner.invoke(
            cli.cli_group,
            ["start-api", "--file", str(spec_file), "--output", str(output_dir), "--regen"],
        )

        # Should succeed (Swagger 2.0 is auto-converted to 3.0)
        assert result.exit_code == 0
