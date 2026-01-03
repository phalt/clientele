"""Additional tests for framework generator to increase coverage."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from clientele.generators.api.generator import APIGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def test_framework_generator_preserves_existing_config_py():
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


def test_framework_generator_removes_existing_manifest():
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


def test_framework_generator_handles_ruff_formatting_error():
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


def test_framework_generator_handles_ruff_not_found():
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
