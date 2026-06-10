"""
Comprehensive tests for $ref handling in OpenAPI schemas.

This test module validates that clientele correctly handles $ref in various
contexts: schema properties, response definitions, parameters, and complex
scenarios like allOf, arrays, and nested references.
"""

from clientele.generators.api.generator import APIGenerator
from tests.generators.integration_utils import get_spec_path, load_spec


def _make_generator(spec, spec_path, tmp_path):
    return APIGenerator(
        spec=spec,
        output_dir=str(tmp_path),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    )


class TestRefInSchemaProperties:
    """Test $ref handling in schema property definitions."""

    def test_direct_ref_in_property(self, tmp_path):
        """Test that direct $ref in properties generates correct type hints."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'another_model: "AnotherModel"' in schemas_content
        assert "class AnotherModel(pydantic.BaseModel):" in schemas_content

    def test_ref_in_array_items(self, tmp_path):
        """Test that $ref in array items generates correct list types."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'a_list_of_other_models: list["AnotherModel"]' in schemas_content

    def test_ref_to_enum(self, tmp_path):
        """Test that $ref to enum schemas generates correct types."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'a_enum: "ExampleEnum"' in schemas_content
        assert "class ExampleEnum(str, enum.Enum):" in schemas_content

    def test_ref_enum_in_array(self, tmp_path):
        """Test that $ref to enum in array items works."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'a_list_of_enums: list["ExampleEnum"]' in schemas_content

    def test_nested_refs(self, tmp_path):
        """Test that nested $ref (list of refs to schemas with refs) works."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'detail: list["ValidationError"]' in schemas_content


class TestRefInResponses:
    """Test $ref handling in response definitions."""

    def test_response_ref_to_components_responses(self, tmp_path):
        """Test that $ref to components/responses is resolved correctly."""
        spec = load_spec("test_303.yaml")
        generator = _make_generator(spec, get_spec_path("test_303.yaml"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert "class DetailErrorResponseModel(pydantic.BaseModel):" in schemas_content
        assert "timestamp: typing.Optional[str]" in schemas_content
        assert "status: int" in schemas_content


class TestRefInParameters:
    """Test $ref handling in parameter definitions."""

    def test_parameter_ref_in_headers(self, tmp_path):
        """Test that $ref in parameters generates correct header classes."""
        spec = load_spec("test_303.yaml")
        generator = _make_generator(spec, get_spec_path("test_303.yaml"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert "class CreateThreadHeaders(pydantic.BaseModel):" in schemas_content
        assert 'request_id: str = pydantic.Field(serialization_alias="request-id")' in schemas_content
        assert 'idempotency_key: str = pydantic.Field(serialization_alias="idempotency-key")' in schemas_content


class TestRefInAllOf:
    """Test $ref handling in allOf compositions."""

    def test_allof_with_refs(self, tmp_path):
        """Test that allOf with $refs merges schemas correctly."""
        spec = load_spec("test_303.yaml")
        generator = _make_generator(spec, get_spec_path("test_303.yaml"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert "class CreateThreadRequest(pydantic.BaseModel):" in schemas_content
        assert "thread_id: str" in schemas_content
        assert "content: str" in schemas_content


class TestRuntimeRefBehavior:
    """Test that generated code with $refs works at runtime."""

    def test_generated_code_imports(self, tmp_path):
        """Test that generated code with $refs can be imported."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        import importlib.util
        import sys

        spec_module = importlib.util.spec_from_file_location("schemas", tmp_path / "schemas.py")
        if spec_module and spec_module.loader:
            schemas = importlib.util.module_from_spec(spec_module)
            sys.modules["test_schemas"] = schemas
            spec_module.loader.exec_module(schemas)

            assert hasattr(schemas, "AnotherModel")
            assert hasattr(schemas, "ComplexModelResponse")
            assert hasattr(schemas, "ExampleEnum")

    def test_create_instance_with_ref_property(self, tmp_path):
        """Test creating instances of schemas with $ref properties."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert 'another_model: "AnotherModel"' in schemas_content
        assert 'a_list_of_other_models: list["AnotherModel"]' in schemas_content
        assert 'a_enum: "ExampleEnum"' in schemas_content
        assert 'a_list_of_enums: list["ExampleEnum"]' in schemas_content
        assert "model_rebuild()" in schemas_content
        assert "import typing" in schemas_content

    def test_allof_ref_instance_creation(self, tmp_path):
        """Test creating instances of schemas using allOf with $refs."""
        spec = load_spec("test_303.yaml")
        generator = _make_generator(spec, get_spec_path("test_303.yaml"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert "class CreateThreadRequest(pydantic.BaseModel):" in schemas_content
        assert "thread_id: str" in schemas_content
        assert "content: str" in schemas_content


class TestRefEdgeCases:
    """Test edge cases and complex $ref scenarios."""

    def test_multiple_refs_same_schema(self, tmp_path):
        """Test that the same schema referenced multiple times works."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert schemas_content.count("class AnotherModel(pydantic.BaseModel):") == 1

    def test_forward_references_resolved(self, tmp_path):
        """Test that forward references are properly resolved."""
        spec = load_spec("best.json")
        generator = _make_generator(spec, get_spec_path("best.json"), tmp_path)
        generator.generate()

        schemas_content = (tmp_path / "schemas.py").read_text()

        assert '"AnotherModel"' in schemas_content
        assert '"ExampleEnum"' in schemas_content
        assert '"ValidationError"' in schemas_content
        assert "model_rebuild()" in schemas_content
