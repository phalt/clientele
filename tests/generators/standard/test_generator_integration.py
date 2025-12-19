"""Integration tests for standard generator."""

import tempfile
from pathlib import Path

from clientele.generators.standard.generator import StandardGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def test_standard_generator_with_simple_spec():
    """Test StandardGenerator can generate a complete client from simple spec."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated_client"

        # Create generator
        generator = StandardGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Generate client
        generator.generate()

        # Verify expected files were created
        assert (output_dir / "client.py").exists()
        assert (output_dir / "schemas.py").exists()
        assert (output_dir / "http.py").exists()
        assert (output_dir / "config.py").exists()
        assert (output_dir / "__init__.py").exists()
        assert (output_dir / "MANIFEST.md").exists()

        # Verify files have content
        client_content = (output_dir / "client.py").read_text()
        assert len(client_content) > 100
        assert "def " in client_content

        schemas_content = (output_dir / "schemas.py").read_text()
        assert len(schemas_content) > 50

        http_content = (output_dir / "http.py").read_text()
        assert len(http_content) > 100
        assert "APIException" in http_content


def test_standard_generator_with_best_spec():
    """Test StandardGenerator with the comprehensive 'best' spec."""
    spec = load_spec("best.json")
    spec_path = get_spec_path("best.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "best_client"

        generator = StandardGenerator(
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


def test_standard_generator_async_mode():
    """Test StandardGenerator generates async client."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "async_client"

        generator = StandardGenerator(
            spec=spec, asyncio=True, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify async client was generated
        client_content = (output_dir / "client.py").read_text()
        assert "async def " in client_content
        assert "await " in client_content

        http_content = (output_dir / "http.py").read_text()
        assert "AsyncClient" in http_content


def test_standard_generator_prevents_accidental_regen():
    """Test that generator prevents accidental regeneration."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "protected_client"

        # First generation with regen=True
        generator1 = StandardGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )
        generator1.generate()

        # Second generation without regen should be prevented
        generator2 = StandardGenerator(
            spec=spec, asyncio=False, regen=False, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # prevent_accidental_regens should return False (blocked)
        assert generator2.prevent_accidental_regens() is False


def test_standard_generator_with_yaml_spec():
    """Test StandardGenerator works with YAML spec."""
    spec = load_spec("test_303.yaml")
    spec_path = get_spec_path("test_303.yaml")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "yaml_client"

        generator = StandardGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify generation succeeded
        assert (output_dir / "client.py").exists()
        assert (output_dir / "schemas.py").exists()


def test_standard_generator_creates_manifest():
    """Test that generator creates proper MANIFEST.md."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "manifest_test"

        generator = StandardGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        manifest_path = output_dir / "MANIFEST.md"
        assert manifest_path.exists()

        manifest_content = manifest_path.read_text()
        assert "clientele" in manifest_content
        assert "Generated" in manifest_content or "generated" in manifest_content
