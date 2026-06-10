"""Tests for the BasicGenerator (clientele/generators/basic/generator.py)."""

import tempfile
from pathlib import Path

from clientele.generators.basic.generator import BasicGenerator


def test_basic_generator_removes_existing_manifest():
    """Test that basic generator replaces an existing MANIFEST.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "basic_client"
        output_dir.mkdir(parents=True)

        existing_manifest = output_dir / "MANIFEST.md"
        existing_manifest.write_text("# Old manifest\n")
        assert existing_manifest.exists()

        generator = BasicGenerator(output_dir=str(output_dir))
        generator.generate()

        assert existing_manifest.exists()
        new_content = existing_manifest.read_text()
        assert "Old manifest" not in new_content


def test_basic_generator_removes_existing_files():
    """Test that basic generator removes existing files before regenerating."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "basic_client"
        output_dir.mkdir(parents=True)

        (output_dir / "client.py").write_text("# Old client\n")
        (output_dir / "schemas.py").write_text("# Old schemas\n")
        (output_dir / "http.py").write_text("# Old http\n")
        (output_dir / "config.py").write_text("# Old config\n")

        generator = BasicGenerator(output_dir=str(output_dir))
        generator.generate()

        assert "Old client" not in (output_dir / "client.py").read_text()
        assert "Old schemas" not in (output_dir / "schemas.py").read_text()
