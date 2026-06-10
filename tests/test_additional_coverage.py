"""Additional tests to reach even higher coverage."""

import tempfile
from pathlib import Path

from clientele.generators.api import writer as api_writer
from clientele.generators.shared import utils
from clientele.generators.shared.schemas import SchemasGenerator
from tests.generators.integration_utils import load_spec


def test_utils_get_type_with_allof_single_schema():
    """Test get_type with allOf containing a single schema."""
    type_spec = {"allOf": [{"type": "string"}]}
    result = utils.get_type(type_spec)
    assert result is not None


def test_utils_get_param_from_ref_missing():
    """Test get_param_from_ref with non-existent parameter."""
    spec = load_spec("simple.json")

    param = {"$ref": "#/components/parameters/NonExistentParam"}
    result = utils.get_param_from_ref(spec, param)

    assert result == {}


def test_utils_get_schema_from_ref_missing():
    """Test get_schema_from_ref with non-existent schema."""
    spec = load_spec("simple.json")

    result = utils.get_schema_from_ref(spec, "#/components/schemas/NonExistentSchema")

    assert result == {}


def test_schemas_generator_with_allof_object():
    """Test schemas generator handles allOf with object properties."""
    spec = load_spec("simple.json")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_schemas"
        output_dir.mkdir(parents=True)

        generator = SchemasGenerator(spec=spec, output_dir=str(output_dir), writer=api_writer)

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

        assert "TestAllOfProps" in generator.schemas
