"""Additional tests for base clients and basic generator coverage."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from clientele.generators.api.generators import clients as api_clients
from clientele.generators.basic.generator import BasicGenerator
from tests.generators.integration_utils import load_spec


def test_basic_generator_removes_existing_manifest():
    """Test that basic generator removes existing MANIFEST.md (line 32)."""
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
    """Test that basic generator removes existing files (line 43)."""
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


def test_clients_generator_handles_optional_path_parameters():
    """Test that clients generator handles optional query parameters."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        from clientele.generators.api import writer as api_writer
        from clientele.generators.shared.generators.schemas import SchemasGenerator

        schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)

        api_clients.FrameworkHTTPPlaceholder()

        generator = api_clients.ClientsGenerator(
            spec=spec,
            output_dir=str(output_dir),
            schemas_generator=schemas_gen,
            asyncio=False,
        )

        parameters = [
            {
                "name": "filter",
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
            }
        ]

        result = generator.generate_parameters(parameters, [])

        assert "filter" in result.query_args
        assert "Optional" in result.query_args["filter"]


def test_clients_generator_handles_multiple_input_classes():
    """Test that clients generator handles multiple input classes."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        from clientele.generators.api import writer as api_writer
        from clientele.generators.shared.generators.schemas import SchemasGenerator

        schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)

        generator = api_clients.ClientsGenerator(
            spec=spec,
            output_dir=str(output_dir),
            schemas_generator=schemas_gen,
            asyncio=False,
        )

        request_body = {
            "content": {
                "application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
                "application/xml": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
            }
        }

        with patch.object(generator, "get_input_class_names", return_value=["InputClass1", "InputClass2"]):
            result = generator.generate_input_types(request_body, "test_func")

            assert "Union" in result or "|" in result
