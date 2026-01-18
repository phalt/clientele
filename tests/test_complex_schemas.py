"""
Comprehensive tests for oneOf, anyOf, and nullable schema handling.

This test module validates that clientele correctly handles oneOf, anyOf,
and nullable schema constructs with proper Python typing.
"""

import sys
from contextlib import contextmanager

import httpx
import pytest
from respx import MockRouter

from clientele.generators.api.generator import APIGenerator
from clientele.generators.classbase.generator import ClassbaseGenerator
from clientele.generators.standard.generator import StandardGenerator
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
        # Clean up sys.path
        sys.path.remove(str(tmp_path))
        if "schemas" in sys.modules:
            del sys.modules["schemas"]


class TestOneOfSchemas:
    """Test oneOf schema handling - discriminated unions."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, ClassbaseGenerator, APIGenerator])
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

        # Verify oneOf with discriminator creates Annotated type alias
        assert 'PetRequest = typing.Annotated[Cat | Dog, pydantic.Field(discriminator="type")]' in schemas_content
        assert "class Cat(pydantic.BaseModel):" in schemas_content
        assert "class Dog(pydantic.BaseModel):" in schemas_content

    @pytest.mark.parametrize("client_generator", [StandardGenerator, ClassbaseGenerator, APIGenerator])
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

        # Verify PaymentMethodRequest with discriminator (pipe syntax with Annotated)
        assert (
            "PaymentMethodRequest = typing.Annotated[CreditCard | BankTransfer | PayPal, "
            'pydantic.Field(discriminator="method")]'
        ) in schemas_content
        assert "class CreditCard(pydantic.BaseModel):" in schemas_content
        assert "class BankTransfer(pydantic.BaseModel):" in schemas_content
        assert "class PayPal(pydantic.BaseModel):" in schemas_content


class TestAnyOfSchemas:
    """Test anyOf schema handling - flexible unions."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Verify anyOf creates union type in properties
        assert "id: str | int" in schemas_content
        assert "class FlexibleIdResponse(pydantic.BaseModel):" in schemas_content

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # ValidationError.loc should be list[str | int], not list[Any]
        assert "loc: list[str | int]" in schemas_content
        assert "class ValidationError(pydantic.BaseModel):" in schemas_content


class TestNullableFields:
    """Test nullable field handling."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Verify nullable creates Optional wrapper
        assert "optional_nullable_field: typing.Optional[str]" in schemas_content
        assert "nullable_number: typing.Optional[int]" in schemas_content

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Should NOT have double Optional wrapping
        assert "typing.Optional[typing.Optional[" not in schemas_content


class TestRuntimeBehavior:
    """Test that generated code with oneOf/anyOf/nullable works at runtime."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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
            import schemas  # type: ignore[import-not-found]

            # Should be able to access classes
            assert hasattr(schemas, "Cat")
            assert hasattr(schemas, "Dog")
            assert hasattr(schemas, "FlexibleIdResponse")
            assert hasattr(schemas, "NullableFieldsResponse")

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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
            import schemas  # type: ignore[import-not-found]

            # Create instances with different union types
            cat = schemas.Cat(type_="cat", meow_volume=10)
            assert cat.type_ == "cat"
            assert cat.meow_volume == 10

            # FlexibleIdResponse with string ID
            resp1 = schemas.FlexibleIdResponse(id="abc123", data="test")
            assert resp1.id == "abc123"

            # FlexibleIdResponse with int ID
            resp2 = schemas.FlexibleIdResponse(id=12345, data="test")
            assert resp2.id == 12345

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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
            import schemas  # type: ignore[import-not-found]

            # Create instance with nullable fields
            resp = schemas.NullableFieldsResponse(
                required_field="test", optional_nullable_field=None, nullable_number=42
            )
            assert resp.required_field == "test"
            assert resp.optional_nullable_field is None
            assert resp.nullable_number == 42

            # Create instance omitting optional nullable fields
            resp2 = schemas.NullableFieldsResponse(required_field="test")
            assert resp2.required_field == "test"


class TestEdgeCases:
    """Test edge cases and complex combinations."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Both PetRequest and PaymentMethodRequest use oneOf
        assert "PetRequest" in schemas_content
        assert "PaymentMethodRequest" in schemas_content

        # Each schema should only be defined once
        assert schemas_content.count("class Cat(pydantic.BaseModel):") == 1
        assert schemas_content.count("class Dog(pydantic.BaseModel):") == 1


class TestArrayResponses:
    """Test top-level array response handling."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Verify array response creates a type alias (without quotes)
        assert "ResponseListUsers = list[User]" in schemas_content

        # Verify it's NOT an empty class
        assert "class ResponseListUsers(pydantic.BaseModel):" not in schemas_content

        # Verify the User schema is properly defined
        assert "class User(pydantic.BaseModel):" in schemas_content
        assert "id: int" in schemas_content
        assert "name: str" in schemas_content
        assert "email: str" in schemas_content

    @pytest.mark.parametrize("client_generator", [StandardGenerator, APIGenerator, ClassbaseGenerator])
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

        # Verify array response without title creates a type alias (without quotes)
        assert "ListUsersNoTitleListUsersNoTitleGet200Response = list[User]" in schemas_content

        # Verify it's NOT a class with a "test" property (the bug we're fixing)
        assert "class ListUsersNoTitleListUsersNoTitleGet200Response(pydantic.BaseModel):" not in schemas_content
        assert "test: list[" not in schemas_content


class TestNoContentResponses:
    """Test 204 No Content response handling."""

    @pytest.mark.parametrize("client_generator", [StandardGenerator, ClassbaseGenerator])
    def test_204_response_is_included_in_status_code_map(self, tmp_path, client_generator):
        """Test that 204 No Content responses are included in func_response_code_maps."""
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

        http_file = tmp_path / "http.py"
        http_content = http_file.read_text()

        # Verify the delete function is in the map
        assert '"delete_user_delete_user_user_id_delete":' in http_content

        # Verify it's NOT empty (the bug we're fixing)
        assert '"delete_user_delete_user_user_id_delete": {}' not in http_content

        # Verify it has the 204 status code mapped
        assert '"204":' in http_content

    @pytest.mark.parametrize("client_generator", [StandardGenerator, ClassbaseGenerator, APIGenerator])
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

        # Verify the function signature uses the type alias
        assert "-> schemas.ResponseListUsers:" in client_content

    @pytest.mark.respx(base_url="http://localhost:8000")
    def test_array_response_handle_response_runtime(self, respx_mock: MockRouter):
        """Test that handle_response works correctly with array type aliases at runtime."""
        # Use the already generated server_examples/fastapi/client
        from server_examples.fastapi.client import client

        # Create a mock response with array data
        return_value = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]

        respx_mock.get("/users").mock(return_value=httpx.Response(200, json=return_value))

        # Call handle_response with the list_users function
        result = client.list_users()

        # Verify the result is a list of UserResponse objects
        assert isinstance(result, list)
        assert len(result) == 2
        assert hasattr(result[0], "id")
        assert hasattr(result[0], "name")
        assert hasattr(result[0], "email")
        assert result[0].id == 1
        assert result[0].name == "Alice"
        assert result[1].id == 2
        assert result[1].name == "Bob"
