"""Tests for classbase HTTP generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cicerone import parse as cicerone_parse

from clientele.generators.classbase.generators.http import HTTPGenerator


def test_http_generator_with_basic_auth():
    """Test HTTPGenerator handles basic authentication."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a spec with basic auth
        spec_dict = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
            "components": {"securitySchemes": {"basicAuth": {"type": "http", "scheme": "basic"}}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json

            json.dump(spec_dict, f)
            spec_file = f.name

        try:
            spec = cicerone_parse.parse_spec_from_file(spec_file)

            generator = HTTPGenerator(spec=spec, output_dir=tmpdir, asyncio=False)

            # Call generate_http_content which should handle basic auth
            generator.generate_http_content()

            # Check that http.py was created
            http_file = Path(tmpdir) / "http.py"
            assert http_file.exists()

            # Check content has something
            content = http_file.read_text()
            assert len(content) > 100  # Should have substantial content
        finally:
            Path(spec_file).unlink()
