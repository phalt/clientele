"""Tests for the ClientsGenerator (clientele/generators/api/clients.py)."""

from unittest.mock import patch

from clientele.generators.api import clients as api_clients
from clientele.generators.api import writer as api_writer
from clientele.generators.shared.schemas import SchemasGenerator
from tests.generators.integration_utils import load_spec


def _make_clients_generator(spec, output_dir) -> api_clients.ClientsGenerator:
    schemas_gen = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)
    return api_clients.ClientsGenerator(
        spec=spec,
        output_dir=str(output_dir),
        schemas_generator=schemas_gen,
        asyncio=False,
    )


def test_clients_generator_handles_optional_path_parameters(tmp_path):
    """Test that clients generator handles optional query parameters."""
    generator = _make_clients_generator(load_spec("simple.json"), tmp_path)

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


def test_clients_generator_resolves_schema_refs_in_parameters(tmp_path):
    """Test that $ref schema types in parameters use schemas.X prefix."""
    generator = _make_clients_generator(load_spec("simple.json"), tmp_path)

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


def test_clients_generator_adds_query_alias_for_camel_case_names(tmp_path):
    """A camelCase query parameter must become a snake_case arg annotated with Query(alias=...)."""
    generator = _make_clients_generator(load_spec("simple.json"), tmp_path)

    parameters = [
        {
            "name": "orderBy",
            "in": "query",
            "required": True,
            "schema": {"type": "string"},
        }
    ]

    result = generator.generate_parameters(parameters, [])

    assert "order_by" in result.query_args
    assert "order_by" not in result.optional_keys
    assert result.query_args["order_by"] == 'typing.Annotated[str, clientele_api.Query(alias="orderBy")]'


def test_clients_generator_skips_query_alias_for_already_snake_case_names(tmp_path):
    """A query parameter that already matches its sanitized name needs no alias annotation."""
    generator = _make_clients_generator(load_spec("simple.json"), tmp_path)

    parameters = [
        {
            "name": "limit",
            "in": "query",
            "required": True,
            "schema": {"type": "integer"},
        }
    ]

    result = generator.generate_parameters(parameters, [])

    assert result.query_args["limit"] == "int"


def test_clients_generator_handles_multiple_input_classes(tmp_path):
    """Test that clients generator handles multiple input classes."""
    generator = _make_clients_generator(load_spec("simple.json"), tmp_path)

    request_body = {
        "content": {
            "application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
            "application/xml": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}},
        }
    }

    with patch.object(generator, "get_input_class_names", return_value=["InputClass1", "InputClass2"]):
        result = generator.generate_input_types(request_body, "test_func")

        assert "Union" in result or "|" in result
