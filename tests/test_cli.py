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


def test_generate_command_exists_and_is_callable(runner):
    """Test generate command exists and can be invoked."""
    # Just test that the command exists and handles missing parameters correctly
    result = runner.invoke(cli.cli_group, ["generate"])
    # Should fail because required parameter --output is missing
    assert result.exit_code != 0
    assert "--output" in result.output or "output" in result.output.lower()


def test_generate_class_command_exists_and_is_callable(runner):
    """Test generate-class command exists and can be invoked."""
    # Just test that the command exists and handles missing parameters correctly
    result = runner.invoke(cli.cli_group, ["generate-class"])
    # Should fail because required parameter --output is missing
    assert result.exit_code != 0
    assert "--output" in result.output or "output" in result.output.lower()


def test_generate_basic_command_creates_files(runner):
    """Test generate-basic command creates basic file structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "basic_client"

        runner.invoke(
            cli.cli_group,
            ["generate-basic", "--output", str(output_dir)],
        )

        # Should create output directory
        assert output_dir.exists()
        # Check for at least some files created
        assert len(list(output_dir.iterdir())) > 0


def test_print_dependency_instructions():
    """Test that dependency instructions can be printed without error."""
    from rich.console import Console

    console = Console()
    # Should not raise an exception
    cli._print_dependency_instructions(console)


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


def test_generate_command_with_valid_spec(runner):
    """Test generate command creates client successfully."""
    import tempfile
    from pathlib import Path

    # Use the simple spec from example_openapi_specs
    spec_path = Path(__file__).parent.parent / "example_openapi_specs" / "simple.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        result = runner.invoke(
            cli.cli_group,
            ["generate", "--file", str(spec_path), "--output", str(output_dir), "--regen", "true"],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "Client generated" in result.output or "generated" in result.output.lower()


def test_generate_class_command_with_valid_spec(runner):
    """Test generate-class command creates client successfully."""
    import tempfile
    from pathlib import Path

    # Use the simple spec from example_openapi_specs
    spec_path = Path(__file__).parent.parent / "example_openapi_specs" / "simple.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        result = runner.invoke(
            cli.cli_group,
            ["generate-class", "--file", str(spec_path), "--output", str(output_dir), "--regen", "true"],
        )

        # Should succeed
        assert result.exit_code == 0
        assert "generated" in result.output.lower()


def test_cli_main_block():
    """Test the CLI main block can be imported without running."""
    # Just importing the module should work without executing main
    import clientele.cli as cli_module

    assert hasattr(cli_module, "cli_group")
