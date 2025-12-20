"""
Comprehensive tests for $ref handling in OpenAPI schemas.

This test module validates that clientele correctly handles $ref in various
contexts: schema properties, response definitions, parameters, and complex
scenarios like allOf, arrays, and nested references.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from clientele.generators.standard.generator import StandardGenerator


class TestRefInSchemaProperties:
    """Test $ref handling in schema property definitions."""

    def test_direct_ref_in_property(self, tmp_path):
        """Test that direct $ref in properties generates correct type hints."""
        # best.json has ComplexModelResponse.another_model: $ref to AnotherModel
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        # Read generated schemas
        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Verify AnotherModel is referenced correctly
        assert 'another_model: "AnotherModel"' in schemas_content
        assert "class AnotherModel(pydantic.BaseModel):" in schemas_content

    def test_ref_in_array_items(self, tmp_path):
        """Test that $ref in array items generates correct list types."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Verify array of refs is typed correctly
        assert 'a_list_of_other_models: list["AnotherModel"]' in schemas_content

    def test_ref_to_enum(self, tmp_path):
        """Test that $ref to enum schemas generates correct types."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Verify enum ref
        assert 'a_enum: "ExampleEnum"' in schemas_content
        assert "class ExampleEnum(str, enum.Enum):" in schemas_content

    def test_ref_enum_in_array(self, tmp_path):
        """Test that $ref to enum in array items works."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Verify array of enum refs
        assert 'a_list_of_enums: list["ExampleEnum"]' in schemas_content

    def test_nested_refs(self, tmp_path):
        """Test that nested $ref (list of refs to schemas with refs) works."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # HTTPValidationError has detail: list[$ref to ValidationError]
        assert 'detail: list["ValidationError"]' in schemas_content


class TestRefInResponses:
    """Test $ref handling in response definitions."""

    def test_response_ref_to_components_responses(self, tmp_path):
        """Test that $ref to components/responses is resolved correctly."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/test_303.yaml"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # The response $ref should result in the schema being generated
        assert "class DetailErrorResponseModel(pydantic.BaseModel):" in schemas_content
        assert "timestamp: typing.Optional[str]" in schemas_content
        assert "status: int" in schemas_content


class TestRefInParameters:
    """Test $ref handling in parameter definitions."""

    def test_parameter_ref_in_headers(self, tmp_path):
        """Test that $ref in parameters generates correct header classes."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/test_303.yaml"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Parameters should be included in header classes
        assert "class CreateThreadHeaders(pydantic.BaseModel):" in schemas_content
        # request-id from $ref parameter
        assert 'request_id: str = pydantic.Field(serialization_alias="request-id")' in schemas_content
        # idempotency-key from $ref parameter
        assert 'idempotency_key: str = pydantic.Field(serialization_alias="idempotency-key")' in schemas_content


class TestRefInAllOf:
    """Test $ref handling in allOf compositions."""

    def test_allof_with_refs(self, tmp_path):
        """Test that allOf with $refs merges schemas correctly."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/test_303.yaml"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # CreateThreadRequest uses allOf with two $refs
        # Should have fields from both thread and thread-request
        assert "class CreateThreadRequest(pydantic.BaseModel):" in schemas_content
        # From thread schema
        assert "thread_id: str" in schemas_content
        # From thread-request schema
        assert "content: str" in schemas_content


class TestRuntimeRefBehavior:
    """Test that generated code with $refs works at runtime."""

    def test_generated_code_imports(self, tmp_path):
        """Test that generated code with $refs can be imported."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        # Import should not raise
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("schemas", tmp_path / "schemas.py")
        if spec and spec.loader:
            schemas = importlib.util.module_from_spec(spec)
            sys.modules["test_schemas"] = schemas
            spec.loader.exec_module(schemas)

            # Should be able to access classes
            assert hasattr(schemas, "AnotherModel")
            assert hasattr(schemas, "ComplexModelResponse")
            assert hasattr(schemas, "ExampleEnum")

    def test_create_instance_with_ref_property(self, tmp_path):
        """Test creating instances of schemas with $ref properties."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("schemas", tmp_path / "schemas.py")
        if spec and spec.loader:
            schemas = importlib.util.module_from_spec(spec)
            sys.modules["test_schemas_instance"] = schemas
            spec.loader.exec_module(schemas)

            # Create instance with $ref property
            another = schemas.AnotherModel(key="test_key")
            assert another.key == "test_key"

            # Create complex model with multiple $ref types
            response = schemas.ComplexModelResponse(
                a_string="test",
                a_number=42,
                a_decimal=Decimal("3.14"),
                a_float=2.718,
                a_list_of_strings=["a", "b"],
                a_list_of_numbers=[1, 2, 3],
                another_model=another,
                a_list_of_other_models=[another, schemas.AnotherModel(key="key2")],
                a_dict_response={"key": "value"},
                a_enum=schemas.ExampleEnum.ONE,
                a_list_of_enums=[schemas.ExampleEnum.ONE, schemas.ExampleEnum.TWO],
            )

            # Verify types
            assert isinstance(response.another_model, schemas.AnotherModel)
            assert isinstance(response.a_list_of_other_models[0], schemas.AnotherModel)
            assert isinstance(response.a_enum, schemas.ExampleEnum)

    def test_allof_ref_instance_creation(self, tmp_path):
        """Test creating instances of schemas using allOf with $refs."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/test_303.yaml"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("schemas", tmp_path / "schemas.py")
        if spec and spec.loader:
            schemas = importlib.util.module_from_spec(spec)
            sys.modules["test_schemas_allof"] = schemas
            spec.loader.exec_module(schemas)

            # Create instance of allOf schema
            thread_req = schemas.CreateThreadRequest(
                thread_id="123e4567-e89b-12d3-a456-426614174000", content="Test content"
            )

            # Should have both fields from merged schemas
            assert thread_req.thread_id == "123e4567-e89b-12d3-a456-426614174000"
            assert thread_req.content == "Test content"


class TestRefEdgeCases:
    """Test edge cases and complex $ref scenarios."""

    def test_multiple_refs_same_schema(self, tmp_path):
        """Test that the same schema referenced multiple times works."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # AnotherModel is referenced in both direct property and array
        # Should only be defined once
        assert schemas_content.count("class AnotherModel(pydantic.BaseModel):") == 1

    def test_forward_references_resolved(self, tmp_path):
        """Test that forward references are properly resolved."""
        generator = StandardGenerator(
            file_path=Path("example_openapi_specs/best.json"),
            output_dir=str(tmp_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        # Forward references should be in quotes
        assert '"AnotherModel"' in schemas_content
        assert '"ExampleEnum"' in schemas_content
        assert '"ValidationError"' in schemas_content

        # model_rebuild should be called to resolve forward refs
        assert "model_rebuild()" in schemas_content
