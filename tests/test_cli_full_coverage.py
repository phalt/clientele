"""Tests for CLI module to achieve full coverage."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_generate_command_with_old_version_spec(runner, openapi_v2_spec):
    """Test generate command with OpenAPI version < 3.0."""
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

            # Should exit without generating because version is too old
            assert result.exit_code == 0
            # Output directory should not be created or be empty
            assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
        finally:
            Path(spec_file).unlink()


def test_generate_class_command_with_old_version_spec(runner, openapi_v2_spec):
    """Test generate-class command with OpenAPI version < 3.0."""
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

            # Should exit without generating because version is too old
            assert result.exit_code == 0
            # Output directory should not be created or be empty
            assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
        finally:
            Path(spec_file).unlink()


def test_explore_command_with_no_params(runner):
    """Test explore command with no parameters shows error."""
    result = runner.invoke(cli.cli_group, ["explore"])

    assert result.exit_code == 0
    assert "Error: Must provide either --client, --file, or --url" in result.output


def test_explore_command_with_nonexistent_client(runner):
    """Test explore command with nonexistent client directory."""
    result = runner.invoke(cli.cli_group, ["explore", "--client", "/nonexistent/path"])

    assert result.exit_code == 0
    assert "Client directory not found" in result.output


def test_explore_command_with_invalid_client(runner):
    """Test explore command with invalid client directory (missing client.py)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(cli.cli_group, ["explore", "--client", tmpdir])

        assert result.exit_code == 0
        assert "Not a valid client directory" in result.output or "missing client.py" in result.output


def test_explore_command_with_old_version_spec(runner, openapi_v2_spec):
    """Test explore command with OpenAPI version < 3.0."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v2_spec, f)
        spec_file = f.name

    try:
        result = runner.invoke(cli.cli_group, ["explore", "--file", spec_file])

        assert result.exit_code == 0
        # Should show error about version
        assert "3.0.0" in result.output or "version" in result.output.lower()
    finally:
        Path(spec_file).unlink()


def test_explore_command_with_exception_during_introspection(runner, openapi_v3_spec):
    """Test explore command handles exceptions during introspection."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v3_spec, f)
        spec_file = f.name

    try:
        with patch("clientele.explore.introspector.ClientIntrospector") as mock_introspector:
            # Make the introspector raise an exception
            mock_introspector.side_effect = Exception("Test exception")

            result = runner.invoke(cli.cli_group, ["explore", "--file", spec_file])

            assert result.exit_code == 0
            assert "Error:" in result.output
    finally:
        Path(spec_file).unlink()


def test_explore_command_temp_dir_cleanup_on_success(runner, openapi_v3_spec):
    """Test explore command cleans up temp directory after successful run."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v3_spec, f)
        spec_file = f.name

    try:
        with patch("clientele.explore.repl.ClienteleREPL") as mock_repl:
            # Make the REPL run without blocking
            mock_repl_instance = MagicMock()
            mock_repl.return_value = mock_repl_instance

            # Track temp directories created
            temp_dirs_created = []
            original_mkdtemp = tempfile.mkdtemp

            def track_mkdtemp(*args, **kwargs):
                temp_dir = original_mkdtemp(*args, **kwargs)
                temp_dirs_created.append(temp_dir)
                return temp_dir

            with patch("tempfile.mkdtemp", side_effect=track_mkdtemp):
                result = runner.invoke(cli.cli_group, ["explore", "--file", spec_file])

                assert result.exit_code == 0

                # Check that temp directories were cleaned up
                for temp_dir in temp_dirs_created:
                    assert not Path(temp_dir).exists()
    finally:
        Path(spec_file).unlink()


def test_explore_command_temp_dir_cleanup_on_exception(runner, openapi_v3_spec):
    """Test explore command cleans up temp directory even when exception occurs."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_v3_spec, f)
        spec_file = f.name

    try:
        temp_dirs_created = []
        original_mkdtemp = tempfile.mkdtemp

        def track_mkdtemp(*args, **kwargs):
            temp_dir = original_mkdtemp(*args, **kwargs)
            temp_dirs_created.append(temp_dir)
            return temp_dir

        with patch("tempfile.mkdtemp", side_effect=track_mkdtemp):
            with patch("clientele.explore.introspector.ClientIntrospector") as mock_introspector:
                # Make the introspector raise an exception
                mock_introspector.side_effect = Exception("Test exception")

                result = runner.invoke(cli.cli_group, ["explore", "--file", spec_file])

                assert result.exit_code == 0

                # Check that temp directories were cleaned up even after exception
                for temp_dir in temp_dirs_created:
                    assert not Path(temp_dir).exists()
    finally:
        Path(spec_file).unlink()


def test_explore_command_with_existing_client(runner):
    """Test explore command with an existing valid client."""
    # Use one of the test clients that already exists
    test_client_path = Path(__file__).parent / "test_client"

    if test_client_path.exists() and (test_client_path / "client.py").exists():
        with patch("clientele.explore.repl.ClienteleREPL") as mock_repl:
            # Make the REPL run without blocking
            mock_repl_instance = MagicMock()
            mock_repl.return_value = mock_repl_instance

            result = runner.invoke(cli.cli_group, ["explore", "--client", str(test_client_path)])

            # Should succeed
            assert result.exit_code == 0
            # REPL should have been started
            mock_repl_instance.run.assert_called_once()


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
