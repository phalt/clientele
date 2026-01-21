"""Additional tests for schema generators to increase coverage."""

import tempfile
from pathlib import Path

from clientele.generators.standard.generators.schemas import SchemasGenerator as StandardSchemasGenerator
from tests.generators.integration_utils import load_spec


def test_standard_schemas_generator_handles_anyof():
    """Test standard schemas generator handles anyOf schemas (lines 141-142)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = StandardSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create a schema with anyOf
        schema_with_anyof = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
            ]
        }

        generator.make_schema_class("TestAnyOf", schema_with_anyof)

        # Verify schema was processed
        assert "TestAnyOf" in generator.schemas


def test_standard_schemas_generator_handles_ref_in_input_class():
    """Test standard schemas generator handles $ref in input class (line 87)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = StandardSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create input schema with $ref
        input_schema = {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserInput"}}}}

        # Just test that it doesn't raise an exception
        generator.generate_input_class(input_schema, "create_user")


def test_standard_schemas_generator_handles_inline_schema_in_union():
    """Test standard schemas generator handles inline schemas in unions (line 119)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = StandardSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create a schema with oneOf containing both refs and inline schemas
        schema_with_mixed_oneof = {
            "oneOf": [
                {"type": "string"},  # Inline schema
                {"type": "integer"},  # Inline schema
            ]
        }

        generator.make_schema_class("TestMixedUnion", schema_with_mixed_oneof)

        # Verify schema was processed
        assert "TestMixedUnion" in generator.schemas


def test_standard_schemas_generator_handles_allof_with_object_properties():
    """Test standard schemas generator handles allOf with object properties (lines 202-203)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = StandardSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create a schema with allOf containing object with properties
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

        # Verify schema was processed
        assert "TestAllOfObject" in generator.schemas
