"""
Comprehensive tests for oneOf, anyOf, and nullable schema handling.

This test module validates that clientele correctly handles oneOf, anyOf,
and nullable schema constructs with proper Python typing.
"""

import sys
from contextlib import contextmanager

import pytest

from clientele.generators.api.generator import APIGenerator
from clientele.testing import ResponseFactory, configure_client_for_testing
from tests.generators.integration_utils import get_spec_path, load_spec


@contextmanager
def import_generated_schemas(tmp_path):
    """
    Context manager to temporarily add tmp_path to sys.path for importing generated schemas.

    Automatically cleans up sys.path and sys.modules after use.

    Args:
        tmp_path: Path to directory containing generated schemas.py

    Yields:
        None - use 'import schemas' within the context
    """
    sys.path.insert(0, str(tmp_path))
    try:
        yield
    finally:
        sys.path.remove(str(tmp_path))
        if "schemas" in sys.modules:
            del sys.modules["schemas"]


class TestOneOfSchemas:
    """Test oneOf schema handling - discriminated unions."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_oneof_at_schema_level(self, tmp_path, client_generator):
        """Test that oneOf at schema level generates a type alias with discriminator."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert 'PetRequest = typing.Annotated[Cat | Dog, pydantic.Field(discriminator="type")]' in schemas_content
        assert "class Cat(pydantic.BaseModel):" in schemas_content
        assert "class Dog(pydantic.BaseModel):" in schemas_content

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_oneof_with_multiple_types(self, tmp_path, client_generator):
        """Test oneOf with three or more schema options and discriminator."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert (
            "PaymentMethodRequest = typing.Annotated[CreditCard | BankTransfer | PayPal, "
            'pydantic.Field(discriminator="method")]'
        ) in schemas_content
        assert "class CreditCard(pydantic.BaseModel):" in schemas_content
        assert "class BankTransfer(pydantic.BaseModel):" in schemas_content
        assert "class PayPal(pydantic.BaseModel):" in schemas_content


class TestAnyOfSchemas:
    """Test anyOf schema handling - flexible unions."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_anyof_in_property(self, tmp_path, client_generator):
        """Test that anyOf in property generates union types."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "id: str | int" in schemas_content
        assert "class FlexibleIdResponse(pydantic.BaseModel):" in schemas_content

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_anyof_existing_validation_error(self, tmp_path, client_generator):
        """Test that existing ValidationError uses anyOf correctly."""
        spec = load_spec("best.json")
        spec_path = get_spec_path("best.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "loc: list[str | int]" in schemas_content
        assert "class ValidationError(pydantic.BaseModel):" in schemas_content


class TestNullableFields:
    """Test nullable field handling."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_nullable_string(self, tmp_path, client_generator):
        """Test that nullable fields generate Optional types."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "optional_nullable_field: typing.Optional[str]" in schemas_content
        assert "nullable_number: typing.Optional[int]" in schemas_content

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_nullable_no_double_wrapping(self, tmp_path, client_generator):
        """Test that nullable fields don't get double-wrapped in Optional."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "typing.Optional[typing.Optional[" not in schemas_content


class TestRuntimeBehavior:
    """Test that generated code with oneOf/anyOf/nullable works at runtime."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_generated_code_imports(self, tmp_path, client_generator):
        """Test that generated code can be imported without errors."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        with import_generated_schemas(tmp_path):
            import schemas  # type: ignore

            assert hasattr(schemas, "Cat")
            assert hasattr(schemas, "Dog")
            assert hasattr(schemas, "FlexibleIdResponse")
            assert hasattr(schemas, "NullableFieldsResponse")

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_create_instances_with_union_types(self, tmp_path, client_generator):
        """Test creating instances with union types."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        with import_generated_schemas(tmp_path):
            import schemas  # type: ignore

            cat = schemas.Cat(type_="cat", meow_volume=10)
            assert cat.type_ == "cat"
            assert cat.meow_volume == 10

            resp1 = schemas.FlexibleIdResponse(id="abc123", data="test")
            assert resp1.id == "abc123"

            resp2 = schemas.FlexibleIdResponse(id=12345, data="test")
            assert resp2.id == 12345

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_nullable_field_instances(self, tmp_path, client_generator):
        """Test creating instances with nullable fields."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        with import_generated_schemas(tmp_path):
            import schemas  # type: ignore

            resp = schemas.NullableFieldsResponse(
                required_field="test", optional_nullable_field=None, nullable_number=42
            )
            assert resp.required_field == "test"
            assert resp.optional_nullable_field is None
            assert resp.nullable_number == 42

            resp2 = schemas.NullableFieldsResponse(required_field="test")
            assert resp2.required_field == "test"


class TestEdgeCases:
    """Test edge cases and complex combinations."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_multiple_schemas_same_type(self, tmp_path, client_generator):
        """Test that schemas defining the same union types work."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "PetRequest" in schemas_content
        assert "PaymentMethodRequest" in schemas_content

        assert schemas_content.count("class Cat(pydantic.BaseModel):") == 1
        assert schemas_content.count("class Dog(pydantic.BaseModel):") == 1


class TestArrayResponses:
    """Test top-level array response handling."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_array_response_generates_type_alias(self, tmp_path, client_generator):
        """Test that top-level array responses generate type aliases, not empty classes."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "ResponseListUsers = list[User]" in schemas_content
        assert "class ResponseListUsers(pydantic.BaseModel):" not in schemas_content
        assert "class User(pydantic.BaseModel):" in schemas_content
        assert "id: int" in schemas_content
        assert "name: str" in schemas_content
        assert "email: str" in schemas_content

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_array_response_without_title_generates_type_alias(self, tmp_path, client_generator):
        """Test that array responses without title also generate type aliases correctly."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        schemas_file = tmp_path / "schemas.py"
        schemas_content = schemas_file.read_text()

        assert "ListUsersNoTitleListUsersNoTitleGet200Response = list[User]" in schemas_content
        assert "class ListUsersNoTitleListUsersNoTitleGet200Response(pydantic.BaseModel):" not in schemas_content
        assert "test: list[" not in schemas_content


class TestNoContentResponses:
    """Test 204 No Content response handling."""

    @pytest.mark.parametrize("client_generator", [APIGenerator])
    def test_array_response_client_function(self, tmp_path, client_generator):
        """Test that client functions use array type aliases correctly."""
        spec = load_spec("complex_schemas.json")
        spec_path = get_spec_path("complex_schemas.json")
        generator = client_generator(
            spec=spec,
            output_dir=str(tmp_path),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_path),
        )
        generator.generate()

        client_file = tmp_path / "client.py"
        client_content = client_file.read_text()

        assert "-> schemas.ResponseListUsers:" in client_content

    def test_array_response_handle_response_runtime(self):
        """Test that handle_response works correctly with array type aliases at runtime."""
        from server_examples.fastapi.client import client

        fake_backend = configure_client_for_testing(client.client)

        return_value = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        fake_backend.queue_response(
            path="/users",
            response_obj=ResponseFactory.ok(data=return_value),
        )

        result = client.list_users()

        assert isinstance(result, list)
        assert len(result) == 2
        assert hasattr(result[0], "id")
        assert hasattr(result[0], "name")
        assert hasattr(result[0], "email")
        assert result[0].id == 1
        assert result[0].name == "Alice"
        assert result[1].id == 2
        assert result[1].name == "Bob"
