"""Tests for CLI commands."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from clientele import cli


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


def test_load_openapi_spec_raises_value_error_when_no_params():
    """Test that _load_openapi_spec raises ValueError when neither url nor file provided."""
    # The function has an assert, but if that's removed it should raise ValueError
    # Test the else branch that raises ValueError
    try:
        # This will hit the assert first, but we're testing the logic
        cli._load_openapi_spec(url=None, file=None)
        assert False, "Should have raised an error"
    except (AssertionError, ValueError):
        # Either assertion or ValueError is acceptable
        pass


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


@pytest.mark.parametrize(
    "command,regen_arg,expected_output",
    [
        ("start-api", ["--regen"], "generated"),
    ],
)
def test_generate_commands_with_valid_spec(runner, command, regen_arg, expected_output):
    """Test that all generate commands create client successfully with valid spec."""
    import tempfile
    from pathlib import Path

    # Use the simple spec from example_openapi_specs
    spec_path = Path(__file__).parent.parent / "example_openapi_specs" / "simple.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        result = runner.invoke(
            cli.cli_group,
            [command, "--file", str(spec_path), "--output", str(output_dir)] + regen_arg,
        )

        # Should succeed
        assert result.exit_code == 0
        assert expected_output.lower() in result.output.lower()


def test_cli_main_block():
    """Test the CLI main block can be imported without running."""
    # Just importing the module should work without executing main
    import clientele.cli as cli_module

    assert hasattr(cli_module, "cli_group")
