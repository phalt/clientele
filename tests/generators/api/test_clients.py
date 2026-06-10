"""Tests for the ClientsGenerator (clientele/generators/api/clients.py)."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from clientele.generators.api import clients as api_clients
from tests.generators.integration_utils import load_spec


def test_clients_generator_handles_optional_path_parameters():
    """Test that clients generator handles optional query parameters."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        from clientele.generators.api import writer as api_writer
        from clientele.generators.shared.schemas import SchemasGenerator

        schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)

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


def test_clients_generator_resolves_schema_refs_in_parameters():
    """Test that $ref schema types in parameters use schemas.X prefix."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        from clientele.generators.api import writer as api_writer
        from clientele.generators.shared.schemas import SchemasGenerator

        schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)

        generator = api_clients.ClientsGenerator(
            spec=spec,
            output_dir=str(output_dir),
            schemas_generator=schemas_gen,
            asyncio=False,
        )

        parameters = [
            {
                "name": "status",
                "in": "query",
                "required": False,
                "schema": {
                    "anyOf": [
                        {"$ref": "#/components/schemas/ActionStatus"},
                        {"type": "null"},
                    ],
                },
            }
        ]

        result = generator.generate_parameters(parameters, [])

        assert "status" in result.query_args
        param_type = result.query_args["status"]
        assert "schemas.ActionStatus" in param_type
        assert param_type.count("None") <= 1


def test_clients_generator_handles_multiple_input_classes():
    """Test that clients generator handles multiple input classes."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_client"
        output_dir.mkdir(parents=True)

        from clientele.generators.api import writer as api_writer
        from clientele.generators.shared.schemas import SchemasGenerator

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
