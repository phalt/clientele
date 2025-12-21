"""Additional tests for classbase generator to increase coverage."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from clientele.generators.classbase.generator import ClassbaseGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def test_classbase_generator_removes_existing_client_py():
    """Test that generator removes existing client.py (line 71)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing client.py file
        existing_file = output_dir / "client.py"
        existing_file.write_text("# Old client content\n")
        assert existing_file.exists()

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify file was replaced with new content
        assert existing_file.exists()
        new_content = existing_file.read_text()
        assert "Old client content" not in new_content
        assert "class Client" in new_content


def test_classbase_generator_removes_existing_schemas_py():
    """Test that generator removes existing schemas.py (line 81)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing schemas.py file
        existing_file = output_dir / "schemas.py"
        existing_file.write_text("# Old schemas content\n")
        assert existing_file.exists()

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify file was replaced
        assert existing_file.exists()
        new_content = existing_file.read_text()
        assert "Old schemas content" not in new_content


def test_classbase_generator_preserves_existing_config_py():
    """Test that generator preserves existing config.py (lines 97-99)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing config.py with custom content
        existing_config = output_dir / "config.py"
        custom_content = "# Custom config\nclass Config:\n    custom_setting = 'preserved'\n"
        existing_config.write_text(custom_content)
        assert existing_config.exists()

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify existing config.py was NOT replaced
        preserved_content = existing_config.read_text()
        # Check for the key part - custom_setting should still be there
        assert "custom_setting" in preserved_content
        assert "Custom config" in preserved_content


def test_classbase_generator_removes_existing_manifest():
    """Test that generator removes existing MANIFEST.md (line 109)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        # Create an existing MANIFEST.md file
        existing_manifest = output_dir / "MANIFEST.md"
        existing_manifest.write_text("# Old manifest\n")
        assert existing_manifest.exists()

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        generator.generate()

        # Verify file was replaced
        assert existing_manifest.exists()
        new_content = existing_manifest.read_text()
        assert "Old manifest" not in new_content
        assert "Generated" in new_content or "generated" in new_content


def test_classbase_generator_handles_ruff_formatting_error():
    """Test that generator handles Ruff formatting errors gracefully (lines 151-154)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Mock subprocess.run to raise CalledProcessError
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1, cmd=["ruff", "format"], stderr="Ruff formatting failed"
            )

            # Should not raise exception, just log warning
            generator.generate()

            # Verify client was still generated despite formatting error
            assert (Path(output_dir) / "client.py").exists()


def test_classbase_generator_handles_ruff_not_found():
    """Test that generator handles missing Ruff gracefully (lines 155-156)."""
    spec = load_spec("simple.json")
    spec_path = get_spec_path("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"

        generator = ClassbaseGenerator(
            spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=str(spec_path)
        )

        # Mock subprocess.run to raise FileNotFoundError
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ruff: command not found")

            # Should not raise exception, just log warning
            generator.generate()

            # Verify client was still generated despite missing ruff
            assert (Path(output_dir) / "client.py").exists()
