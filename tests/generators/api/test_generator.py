"""Tests for the APIGenerator (clientele/generators/api/generator.py)."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from clientele.generators.api.generator import APIGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def test_api_generator_with_simple_spec():
    """Test APIGenerator can generate a complete client from simple spec."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated_client"

        # Create generator
        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Generate client
        generator.generate()

        # Verify expected files were created
        assert (output_dir / "client.py").exists()
        assert (output_dir / "schemas.py").exists()
        assert (output_dir / "config.py").exists()
        assert (output_dir / "__init__.py").exists()
        assert (output_dir / "MANIFEST.md").exists()

        # Verify files have content
        client_content = (output_dir / "client.py").read_text()
        assert len(client_content) > 100
        assert "def " in client_content

        schemas_content = (output_dir / "schemas.py").read_text()
        assert len(schemas_content) > 50


def test_api_generator_with_best_spec():
    """Test APIGenerator with the comprehensive 'best' spec."""
    spec = load_spec("best.json")
    spec_path = get_spec_path("best.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "best_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify generation succeeded
        assert (output_dir / "client.py").exists()
        assert (output_dir / "schemas.py").exists()

        # Check for specific expected operations
        client_content = (output_dir / "client.py").read_text()
        assert "def simple_request_simple_request_get" in client_content
        assert "def parameter_request_simple_request" in client_content


def test_api_generator_async_mode():
    """Test APIGenerator generates async client."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "async_client"

        generator = APIGenerator(
            spec=spec, asyncio=True, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify async client was generated
        client_content = (output_dir / "client.py").read_text()
        assert "async def " in client_content


def test_api_generator_prevents_accidental_regen():
    """Test that generator prevents accidental regeneration."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "protected_client"

        # First generation with regen=True
        generator1 = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )
        generator1.generate()

        # Second generation without regen should be prevented
        generator2 = APIGenerator(
            spec=spec, asyncio=False, regen=False, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # prevent_accidental_regens should return False (blocked)
        assert generator2.prevent_accidental_regens() is False


def test_api_generator_with_yaml_spec():
    """Test APIGenerator works with YAML spec."""
    spec = load_spec("test_303.yaml")
    spec_path = get_spec_path("test_303.yaml")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "yaml_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify generation succeeded
        assert (output_dir / "client.py").exists()
        assert (output_dir / "schemas.py").exists()


def test_post_without_request_body_omits_data_parameter():
    """POST/PUT/PATCH endpoints without a request body must not generate a `data` parameter."""
    spec = load_spec("best.json")
    spec_path = get_spec_path("best.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "no_body_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )
        generator.generate()

        client_content = (output_dir / "client.py").read_text()
        assert "def post_without_body(" in client_content
        # Extract the full function signature (may span multiple lines until ->)
        sig_start = client_content.index("def post_without_body(")
        sig_end = client_content.index("->", sig_start)
        signature = client_content[sig_start:sig_end]
        assert "data:" not in signature, f"Unexpected 'data' parameter in: {signature}"
        assert "item_id: str" in signature
        assert "force:" in signature


def test_api_generator_creates_manifest():
    """Test that generator creates proper MANIFEST.md."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "manifest_test"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        manifest_path = output_dir / "MANIFEST.md"
        assert manifest_path.exists()

        manifest_content = manifest_path.read_text()
        assert "clientele" in manifest_content
        assert "Generated" in manifest_content or "generated" in manifest_content


def test_api_generator_preserves_existing_config_py():
    """Test that generator preserves existing config.py."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing config.py with custom content
        existing_config = output_dir / "config.py"
        custom_content = "base_url: str = 'https://custom.example.com'\n"
        existing_config.write_text(custom_content)
        assert existing_config.exists()

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify existing config.py was NOT replaced
        preserved_content = existing_config.read_text()
        # Check for the key part - custom URL should still be there
        assert "custom.example.com" in preserved_content


def test_api_generator_removes_existing_manifest():
    """Test that generator removes existing MANIFEST.md."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing MANIFEST.md file
        existing_manifest = output_dir / "MANIFEST.md"
        existing_manifest.write_text("# Old manifest content\n")
        assert existing_manifest.exists()

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify file was replaced
        assert existing_manifest.exists()
        new_content = existing_manifest.read_text()
        assert "Old manifest content" not in new_content
        assert "Generated" in new_content or "generated" in new_content


def test_api_generator_handles_ruff_formatting_error():
    """Test that generator handles Ruff formatting errors gracefully."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Mock subprocess.run to raise CalledProcessError on first call (format)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["ruff", "format"], stderr="Formatting error occurred"
            )

            # Should not raise exception, just log warning
            generator.generate()

            # Verify client was still generated despite formatting error
            assert (Path(output_dir) / "client.py").exists()


def test_api_generator_handles_ruff_not_found():
    """Test that generator handles missing Ruff gracefully."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Mock subprocess.run to raise FileNotFoundError
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ruff: command not found")

            # Should not raise exception, just log warning
            generator.generate()

            # Verify client was still generated despite missing ruff
            assert (Path(output_dir) / "client.py").exists()


def test_api_generator_removes_existing_files():
    """Test that the generator removes existing files before regenerating."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )
        generator.generate()

        assert (output_dir / "client.py").exists()

        test_file = output_dir / "schemas.py"
        test_file.write_text("# Old content")

        generator2 = APIGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )
        generator2.generate()

        assert test_file.exists()
        assert "# Old content" not in test_file.read_text()


def test_api_generator_uses_server_url_from_spec():
    """Test that the base URL from the spec servers ends up in config.py."""
    from cicerone import parse as cicerone_parse

    spec = cicerone_parse.parse_spec_from_dict(
        {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test_get",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = APIGenerator(spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=None)
        generator.generate()

        assert (output_dir / "config.py").exists()
        config_content = (output_dir / "config.py").read_text()
        assert "api.example.com" in config_content
