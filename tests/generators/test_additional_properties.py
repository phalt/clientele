"""
Tests for typed additionalProperties support.

OpenAPI object schemas with a schema-valued `additionalProperties` describe
map/dictionary types (e.g. error maps, translations, metrics keyed by id).
Historically these degraded to `dict[str, typing.Any]`, losing all value
validation.

Expected behaviour:
  - a property typed `{type: object, additionalProperties: <schema>}`
    generates `dict[str, <type>]`
  - a component schema that is purely a map (additionalProperties, no
    properties) generates a `DictResponse` root model class so it is a
    real type (usable in response_map) with mapping-style access
  - `additionalProperties: true`, `{}`, or absent keeps the existing
    `dict[str, typing.Any]` / plain BaseModel behaviour
"""

import sys
from contextlib import contextmanager

import pydantic
import pytest

from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_schema
from clientele.generators.shared import utils
from tests.generators.integration_utils import get_spec_path, load_spec


@contextmanager
def _import_generated_schemas(tmp_path):
    # Purge any generated modules cached by earlier tests before importing
    for mod in list(sys.modules):
        if mod in ("schemas", "client", "config"):
            del sys.modules[mod]
    sys.path.insert(0, str(tmp_path))
    try:
        yield
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod in ("schemas", "client", "config"):
                del sys.modules[mod]


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """Generate the additional_properties client once for the whole module."""
    tmp_path = tmp_path_factory.mktemp("additional_properties_client")
    spec = load_spec("additional_properties.json")
    generator = APIGenerator(
        spec=spec,
        output_dir=str(tmp_path),
        asyncio=False,
        regen=True,
        url=None,
        file=str(get_spec_path("additional_properties.json")),
    )
    generator.generate()
    return tmp_path


class TestGetTypeAdditionalProperties:
    """Unit tests for type resolution of additionalProperties."""

    @pytest.mark.parametrize(
        "type_spec,expected_output",
        [
            (
                {"type": "object", "additionalProperties": {"type": "integer"}},
                "dict[str, int]",
            ),
            (
                {"type": "object", "additionalProperties": {"type": "string"}},
                "dict[str, str]",
            ),
            (
                {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "string"}}},
                "dict[str, list[str]]",
            ),
            (
                {"type": "object", "additionalProperties": {"$ref": "#/components/schemas/Error"}},
                'dict[str, "Error"]',
            ),
            # Free-form objects keep the untyped behaviour
            ({"type": "object", "additionalProperties": True}, "dict[str, typing.Any]"),
            ({"type": "object", "additionalProperties": {}}, "dict[str, typing.Any]"),
            ({"type": "object"}, "dict[str, typing.Any]"),
        ],
    )
    def test_get_type(self, type_spec, expected_output):
        assert utils.get_type(type_spec) == expected_output

    def test_object_with_declared_properties_stays_untyped(self):
        # When an object declares its own properties, the schema describes a
        # structured object (generated elsewhere as a class), not a map.
        type_spec = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": {"type": "integer"},
        }
        assert utils.get_type(type_spec) == "dict[str, typing.Any]"


class TestOpenAPI31Normalization:
    """additionalProperties schemas must be normalized recursively."""

    def test_nullable_type_array_inside_additional_properties(self):
        schema = {
            "type": "object",
            "additionalProperties": {"type": ["string", "null"]},
        }
        normalized = normalize_openapi_31_schema(schema)
        assert normalized["additionalProperties"] == {"type": "string", "nullable": True}

    def test_boolean_additional_properties_pass_through(self):
        schema = {"type": "object", "additionalProperties": True}
        normalized = normalize_openapi_31_schema(schema)
        assert normalized["additionalProperties"] is True


class TestMapValuedModelProperties:
    """Model properties that are maps validate their values."""

    def test_typed_map_of_primitives(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            report = schemas.Report.model_validate({"scores": {"alice": 3, "bob": 5}})
            assert report.scores == {"alice": 3, "bob": 5}

    def test_typed_map_values_are_validated(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            with pytest.raises(pydantic.ValidationError):
                schemas.Report.model_validate({"scores": {"alice": "not-an-int"}})

    def test_typed_map_of_models_hydrates_values(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            report = schemas.Report.model_validate(
                {
                    "scores": {},
                    "errors_by_field": {"email": {"message": "invalid"}},
                }
            )
            assert isinstance(report.errors_by_field["email"], schemas.Error)
            assert report.errors_by_field["email"].message == "invalid"

    def test_typed_map_of_arrays(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            report = schemas.Report.model_validate({"scores": {}, "tag_groups": {"colours": ["red", "blue"]}})
            assert report.tag_groups == {"colours": ["red", "blue"]}

    def test_untyped_object_property_still_accepts_anything(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            report = schemas.Report.model_validate({"scores": {}, "metadata": {"anything": ["goes", 1, None]}})
            assert report.metadata == {"anything": ["goes", 1, None]}


class TestMapComponentSchemas:
    """Component schemas that are purely maps become DictResponse classes."""

    def test_map_schema_is_a_real_type(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            # Must be a class so pydantic accepts it in response_map
            assert isinstance(schemas.ScoreMap, type)

    def test_map_schema_validates_and_provides_mapping_access(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            scores = schemas.ScoreMap.model_validate({"alice": 3, "bob": 5})
            assert scores["alice"] == 3
            assert len(scores) == 2
            assert set(scores) == {"alice", "bob"}
            assert dict(scores.items()) == {"alice": 3, "bob": 5}

    def test_map_schema_rejects_bad_values(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            with pytest.raises(pydantic.ValidationError):
                schemas.ScoreMap.model_validate({"alice": "not-an-int"})

    def test_map_of_models_hydrates_values(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            errors = schemas.ErrorMap.model_validate({"email": {"message": "invalid"}})
            assert isinstance(errors["email"], schemas.Error)
            assert errors["email"].message == "invalid"

    def test_free_form_object_schema_keeps_basemodel_shape(self, generated):
        with _import_generated_schemas(generated):
            import schemas  # type: ignore

            # additionalProperties: true is not a typed map; the existing
            # empty BaseModel behaviour is preserved.
            assert issubclass(schemas.FreeForm, pydantic.BaseModel)


class TestClientReturnTypes:
    """Decorated client functions can use map schemas in response_map."""

    def test_client_imports_with_map_response(self, generated):
        # Importing client.py runs build_request_context which validates
        # every response_map entry is a real type - this fails if ScoreMap
        # were a plain type alias. The generated code is a package (it uses
        # relative imports), so import it as one.
        import importlib

        package_name = generated.name
        sys.path.insert(0, str(generated.parent))
        try:
            importlib.import_module(f"{package_name}.client")
        finally:
            sys.path.remove(str(generated.parent))
            for mod in list(sys.modules):
                if mod == package_name or mod.startswith(f"{package_name}."):
                    del sys.modules[mod]
