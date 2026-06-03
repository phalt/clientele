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


def test_generate_class_properties_with_defaults():
    """Test that explicit default values from OpenAPI specs are rendered."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "name": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}, "default": []},
            "count": {"type": "integer", "default": 0},
            "enabled": {"type": "boolean", "default": False},
            "label": {"type": "string", "default": ""},
            "description": {"type": "string", "default": None},
        }

        result = generator.generate_class_properties(properties, required=["name"])

        assert "name: str\n" in result
        assert "tags: list[str] = []\n" in result
        assert "count: int = 0\n" in result
        assert "enabled: bool = False\n" in result
        assert "label: str = ''\n" in result
        assert "description: str = None\n" in result


def test_generate_class_properties_default_with_alias():
    """Test that fields with both alias and default use pydantic.Field."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "my-field": {"type": "integer", "default": 42},
        }

        result = generator.generate_class_properties(properties, required=[])

        assert 'my_field: int = pydantic.Field(default=42, alias="my-field")' in result
        assert "model_config = pydantic.ConfigDict(populate_by_name=True)" in result


def test_generate_class_properties_no_required_array_with_defaults():
    """Test schema with no required array where all fields have defaults."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "tags": {"type": "array", "items": {"type": "string"}, "default": []},
            "count": {"type": "integer", "default": 0},
            "enabled": {"type": "boolean", "default": True},
        }

        result = generator.generate_class_properties(properties, required=None)

        assert "tags: list[str] = []\n" in result
        assert "count: int = 0\n" in result
        assert "enabled: bool = True\n" in result
        assert "typing.Optional" not in result


def test_generate_class_properties_with_const():
    """Test that const values generate typing.Literal types."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "action": {"type": "string", "const": "create"},
            "name": {"type": "string"},
        }

        result = generator.generate_class_properties(properties, required=["action", "name"])

        assert "action: typing.Literal['create']\n" in result
        assert "name: str\n" in result


def test_generate_class_properties_const_with_default():
    """Test that const + default generates Literal type with default value."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "action": {"type": "string", "const": "add-user", "default": "add-user"},
            "message": {"type": "string"},
        }

        result = generator.generate_class_properties(properties, required=["message"])

        assert "action: typing.Literal['add-user'] = 'add-user'\n" in result
        assert "message: str\n" in result


def test_generate_class_properties_const_with_alias():
    """Test that const field with alias uses pydantic.Field."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = _make_generator(spec, output_dir)

        properties = {
            "action-type": {"type": "string", "const": "delete", "default": "delete"},
        }

        result = generator.generate_class_properties(properties, required=[])

        assert (
            "action_type: typing.Literal['delete'] = pydantic.Field(default='delete', alias=\"action-type\")" in result
        )
        assert "model_config = pydantic.ConfigDict(populate_by_name=True)" in result
