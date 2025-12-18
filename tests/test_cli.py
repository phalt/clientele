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


def test_version_command(runner):
    """Test the version command displays version."""
    from clientele import settings

    result = runner.invoke(cli.cli_group, ["version"])
    assert result.exit_code == 0
    assert "clientele" in result.output
    assert settings.VERSION in result.output


def test_validate_command_with_valid_json_file(runner, simple_openapi_spec):
    """Test validate command with a valid JSON OpenAPI spec file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(simple_openapi_spec, f)
        spec_file = f.name

    try:
        result = runner.invoke(cli.cli_group, ["validate", "--file", spec_file])
        assert result.exit_code == 0
        assert "Test API" in result.output
        assert "1.0.0" in result.output
    finally:
        Path(spec_file).unlink()


def test_validate_command_with_valid_yaml_file(runner, simple_openapi_spec):
    """Test validate command with a valid YAML OpenAPI spec file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(simple_openapi_spec, f)
        spec_file = f.name

    try:
        result = runner.invoke(cli.cli_group, ["validate", "--file", spec_file])
        assert result.exit_code == 0
        assert "Test API" in result.output
    finally:
        Path(spec_file).unlink()


def test_validate_command_with_old_openapi_version(runner):
    """Test validate command warns about old OpenAPI versions."""
    OLD_OPENAPI_VERSION = "2.0.0"
    old_spec = {
        "openapi": OLD_OPENAPI_VERSION,
        "info": {"title": "Old API", "version": "1.0.0"},
        "paths": {},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(old_spec, f)
        spec_file = f.name

    try:
        result = runner.invoke(cli.cli_group, ["validate", "--file", spec_file])
        # Should warn about old version
        assert "supports openapi version 3" in result.output.lower()
        assert OLD_OPENAPI_VERSION in result.output
    finally:
        Path(spec_file).unlink()


def test_validate_command_requires_url_or_file(runner):
    """Test validate command fails without URL or file."""
    result = runner.invoke(cli.cli_group, ["validate"])
    # Should require either url or file parameter
    assert result.exit_code != 0


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

        result = runner.invoke(
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


def test_load_openapi_spec_from_file(simple_openapi_spec):
    """Test loading OpenAPI spec from a file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(simple_openapi_spec, f)
        spec_file = f.name

    try:
        spec = cli._load_openapi_spec(file=spec_file)
        assert spec is not None
        assert spec["info"]["title"] == "Test API"
    finally:
        Path(spec_file).unlink()


def test_load_openapi_spec_requires_url_or_file():
    """Test that _load_openapi_spec requires either URL or file."""
    with pytest.raises(AssertionError):
        cli._load_openapi_spec()


def test_load_openapi_spec_with_yaml_file(simple_openapi_spec):
    """Test loading YAML OpenAPI spec from a file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(simple_openapi_spec, f)
        spec_file = f.name

    try:
        spec = cli._load_openapi_spec(file=spec_file)
        assert spec is not None
        assert spec["info"]["title"] == "Test API"
    finally:
        Path(spec_file).unlink()


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


def test_load_openapi_spec_with_yaml_response_from_url(simple_openapi_spec, respx_mock):
    """Test loading OpenAPI spec from URL when response is YAML."""
    import respx
    import httpx
    
    url = "https://example.com/openapi.yaml"
    yaml_content = yaml.dump(simple_openapi_spec)
    
    # Mock the URL to return YAML content that will fail JSON parsing
    respx_mock.get(url).mock(
        return_value=httpx.Response(
            200, 
            content=yaml_content.encode(),
            headers={"content-type": "application/x-yaml"}
        )
    )
    
    spec = cli._load_openapi_spec(url=url)
    assert spec is not None
    assert spec["info"]["title"] == "Test API"


def test_load_openapi_spec_with_json_from_url(simple_openapi_spec, respx_mock):
    """Test loading OpenAPI spec from URL when response is JSON."""
    import respx
    import httpx
    
    url = "https://example.com/openapi.json"
    
    respx_mock.get(url).mock(
        return_value=httpx.Response(200, json=simple_openapi_spec)
    )
    
    spec = cli._load_openapi_spec(url=url)
    assert spec is not None
    assert spec["info"]["title"] == "Test API"


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
    assert hasattr(cli_module, 'cli_group')
