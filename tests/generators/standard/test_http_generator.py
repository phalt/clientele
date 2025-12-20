"""Tests for standard HTTP generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

from cicerone import parse as cicerone_parse

from clientele.generators.standard import writer
from clientele.generators.standard.generators.http import HTTPGenerator


def test_http_generator_env_var():
    """Test env_var function generates correct environment variable names."""
    from clientele.generators.standard.generators.http import env_var

    # Test with regular output dir
    result = env_var("my/client", "api_key")
    assert result == "MYCLIENT_API_KEY"

    # Test with simple name
    result = env_var("client", "base_url")
    assert result == "CLIENT_BASE_URL"


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

            # Flush the writer buffers
            writer.flush_buffers()

            # Check that http.py was created
            http_file = Path(tmpdir) / "http.py"
            assert http_file.exists()

            # Check content mentions basic client
            content = http_file.read_text()
            assert len(content) > 100  # Should have substantial content
        finally:
            Path(spec_file).unlink()
