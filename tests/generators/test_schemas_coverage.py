"""Additional tests for schema generators to increase coverage."""

import tempfile
from pathlib import Path

from clientele.generators.api import writer as api_writer
from clientele.generators.shared.generators.schemas import SchemasGenerator
from tests.generators.integration_utils import load_spec


def _make_generator(spec, output_dir):
    return SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)


def test_schemas_generator_handles_anyof():
    """Test schemas generator handles anyOf schemas."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        schema_with_anyof = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }

        generator.make_schema_class("TestAnyOf", schema_with_anyof)

        assert "TestAnyOf" in generator.schemas


def test_schemas_generator_handles_ref_in_input_class():
    """Test schemas generator handles $ref in input class."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        input_schema = {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserInput"}}}}

        generator.generate_input_class(input_schema, "create_user")


def test_schemas_generator_handles_inline_schema_in_union():
    """Test schemas generator handles inline schemas in unions."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        schema_with_mixed_oneof = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }

        generator.make_schema_class("TestMixedUnion", schema_with_mixed_oneof)

        assert "TestMixedUnion" in generator.schemas


def test_schemas_generator_handles_allof_with_object_properties():
    """Test schemas generator handles allOf with object properties."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        schema_with_allof_object = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                    "required": ["id"],
                }
            ]
        }

        generator.make_schema_class("TestAllOfObject", schema_with_allof_object)

        assert "TestAllOfObject" in generator.schemas
