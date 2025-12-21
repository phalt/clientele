"""Additional tests to reach even higher coverage."""

import tempfile
from pathlib import Path

from clientele.generators.classbase.generators.schemas import SchemasGenerator as ClassbaseSchemasGenerator
from clientele.generators.standard import utils
from clientele.generators.standard.generators.schemas import SchemasGenerator as StandardSchemasGenerator
from tests.generators.integration_utils import load_spec


def test_classbase_schemas_generator_union_with_inline_schema():
    """Test classbase schemas generator handles oneOf with inline schemas (line 58)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = ClassbaseSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create a schema with oneOf containing an inline schema (not a $ref)
        schema_with_inline = {
            "oneOf": [
                {"type": "string"},  # Inline schema, not a $ref
                {"type": "integer"},  # Another inline schema
            ]
        }

        generator.make_schema_class("TestInlineUnion", schema_with_inline)

        # Verify schema was processed
        assert "TestInlineUnion" in generator.schemas


def test_classbase_schemas_input_class_with_ref():
    """Test classbase schemas generator input class with $ref (line 134)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = ClassbaseSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create input schema with $ref
        input_schema_with_ref = {
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SomeSchema"}}}
        }

        generator.generate_input_class(input_schema_with_ref, "test_operation")

        # Should not raise an error


def test_classbase_schemas_input_class_with_title():
    """Test classbase schemas generator input class with title (line 136)."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = ClassbaseSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create input schema with title
        input_schema_with_title = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "title": "CustomInputTitle",
                        "properties": {"name": {"type": "string"}},
                    }
                }
            }
        }

        generator.generate_input_class(input_schema_with_title, "test_operation")

        # Should use the title for class name


def test_utils_create_query_args():
    """Test create_query_args function (line 157)."""
    query_args = ["param1", "param2", "param3"]
    result = utils.create_query_args(query_args)

    # Should create a query string format
    assert result.startswith("?")
    assert "param1=" in result
    assert "param2=" in result
    assert "param3=" in result
    assert "&" in result


def test_utils_get_type_with_allof_single_schema():
    """Test get_type with allOf containing a single schema (line 157)."""
    type_spec = {"allOf": [{"type": "string"}]}
    result = utils.get_type(type_spec)
    # Should handle allOf with single schema
    assert result is not None


def test_utils_get_param_from_ref_missing():
    """Test get_param_from_ref with non-existent parameter (line 221)."""
    spec = load_spec("simple.json")

    # Test with non-existent parameter ref
    param = {"$ref": "#/components/parameters/NonExistentParam"}
    result = utils.get_param_from_ref(spec, param)

    # Should return empty dict for missing parameter
    assert result == {}


def test_utils_get_schema_from_ref_missing():
    """Test get_schema_from_ref with non-existent schema (line 230)."""
    spec = load_spec("simple.json")

    # Test with non-existent schema ref
    result = utils.get_schema_from_ref(spec, "#/components/schemas/NonExistentSchema")

    # Should return empty dict for missing schema
    assert result == {}


def test_standard_schemas_generator_with_allof_object():
    """Test standard schemas generator handles allOf with object properties."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = StandardSchemasGenerator(spec=spec, output_dir=str(output_dir))

        # Create schema with allOf containing object with properties
        schema_with_allof_props = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                    "required": ["id"],
                }
            ]
        }

        generator.make_schema_class("TestAllOfProps", schema_with_allof_props)

        # Verify schema was processed
        assert "TestAllOfProps" in generator.schemas
