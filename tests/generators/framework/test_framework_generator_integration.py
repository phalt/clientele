"""Integration tests for standard generator."""

import tempfile
from pathlib import Path

from clientele.generators.api.generator import APIGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def test_framework_generator_with_simple_spec():
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


def test_standard_generator_with_best_spec():
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


def test_standard_generator_async_mode():
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


def test_standard_generator_prevents_accidental_regen():
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


def test_standard_generator_with_yaml_spec():
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


def test_standard_generator_creates_manifest():
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
