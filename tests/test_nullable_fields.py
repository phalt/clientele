"""Test that nullable fields are correctly handled in generated schemas.

This test specifically addresses the issue where nullable fields (like pagination's
'previous' and 'next' fields) should accept null values from API responses.

GitHub Issue: Nullable fields not generating Optional[] types
Real-world example: PokeAPI pagination response with {"previous": null}
"""

import tempfile
from pathlib import Path

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator
from clientele.generators.standard.generator import StandardGenerator


@pytest.mark.parametrize("generator_class", [StandardGenerator, APIGenerator])
def test_nullable_pagination_fields(generator_class):
    """Test that nullable pagination fields accept null values.

    This test uses a snippet from the PokeAPI schema to ensure that when
    an API returns {"previous": null, "next": "...url..."}, the generated
    Pydantic model correctly validates the response.

    The schema has nullable:true for these fields, which should generate
    Optional[str] types in Pydantic.
    """
    # OpenAPI 3.0 schema snippet from PokeAPI with nullable pagination fields
    openapi_spec = """
openapi: 3.0.0
info:
  title: Pokemon Pagination API
  version: 1.0.0
paths:
  /api/v2/pokemon/:
    get:
      operationId: pokemon_list
      summary: List Pokemon
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
        - name: offset
          in: query
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaginatedPokemonSummaryList'
components:
  schemas:
    PaginatedPokemonSummaryList:
      type: object
      properties:
        count:
          type: integer
        next:
          type: string
          nullable: true
          description: URL to the next page
        previous:
          type: string
          nullable: true
          description: URL to the previous page
        results:
          type: array
          items:
            $ref: '#/components/schemas/PokemonSummary'
    PokemonSummary:
      type: object
      properties:
        name:
          type: string
        url:
          type: string
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the spec to a temp file
        spec_file = Path(tmpdir) / "test_spec.yaml"
        spec_file.write_text(openapi_spec)

        # Parse the spec
        spec = cicerone_parse.parse_spec_from_file(str(spec_file))

        # Generate the client
        output_dir = Path(tmpdir) / "generated_client"
        generator = generator_class(
            spec=spec,
            output_dir=str(output_dir),
            asyncio=False,
            regen=True,
            url=None,
            file=str(spec_file),
        )
        generator.generate()

        # Read the generated schemas.py file
        schemas_file = output_dir / "schemas.py"
        assert schemas_file.exists(), "schemas.py was not generated"

        schemas_content = schemas_file.read_text()

        # Verify that the PaginatedPokemonSummaryList has Optional[] for nullable fields
        assert "PaginatedPokemonSummaryList" in schemas_content, "PaginatedPokemonSummaryList schema not found"

        # Check that 'next' field is Optional[str]
        assert "next: typing.Optional[str]" in schemas_content, (
            "Field 'next' should be typing.Optional[str] since it's nullable"
        )

        # Check that 'previous' field is Optional[str]
        assert "previous: typing.Optional[str]" in schemas_content, (
            "Field 'previous' should be typing.Optional[str] since it's nullable"
        )

        # Verify the schema compiles without errors
        compile(schemas_content, str(schemas_file), "exec")

        # Now test that the schema actually validates API response with null values
        # Import the generated module dynamically
        import sys

        sys.path.insert(0, str(output_dir))

        try:
            import schemas  # type: ignore[import-not-found]

            # Test with null 'previous' (first page response)
            response_data = {
                "count": 1350,
                "next": "https://pokeapi.co/api/v2/pokemon/?offset=20&limit=20",
                "previous": None,  # This should be valid!
                "results": [
                    {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
                    {"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon/2/"},
                ],
            }

            # This should NOT raise a ValidationError
            paginated_list = schemas.PaginatedPokemonSummaryList(**response_data)
            assert paginated_list.previous is None
            assert paginated_list.next == "https://pokeapi.co/api/v2/pokemon/?offset=20&limit=20"
            assert paginated_list.count == 1350

            # Test with null 'next' (last page response)
            last_page_data = {
                "count": 1350,
                "next": None,  # This should also be valid!
                "previous": "https://pokeapi.co/api/v2/pokemon/?offset=1320&limit=20",
                "results": [
                    {"name": "eternatus", "url": "https://pokeapi.co/api/v2/pokemon/890/"},
                ],
            }

            last_page = schemas.PaginatedPokemonSummaryList(**last_page_data)
            assert last_page.next is None
            assert last_page.previous == "https://pokeapi.co/api/v2/pokemon/?offset=1320&limit=20"

        finally:
            sys.path.remove(str(output_dir))


def test_nullable_with_openapi_31_array_type():
    """Test that OpenAPI 3.1 array-based type notation also works.

    OpenAPI 3.1 uses type: ['string', 'null'] instead of nullable: true.
    This should also generate Optional[str] in Pydantic.
    """
    # OpenAPI 3.1 schema using array-based type notation
    openapi_spec = """
openapi: 3.1.0
info:
  title: Test Nullable API
  version: 1.0.0
paths:
  /test:
    get:
      operationId: test_get
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestResponse'
components:
  schemas:
    TestResponse:
      type: object
      properties:
        id:
          type: integer
        optional_field:
          type:
            - string
            - 'null'
          description: Can be string or null
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "test_spec.yaml"
        spec_file.write_text(openapi_spec)

        # This test verifies the normalization handles OpenAPI 3.1 correctly
        import yaml

        from clientele.generators.cicerone_compat import normalize_openapi_31_spec

        raw_spec = yaml.safe_load(openapi_spec)
        normalized_spec = normalize_openapi_31_spec(raw_spec)

        # The optional_field should have been normalized
        test_response_schema = normalized_spec["components"]["schemas"]["TestResponse"]
        optional_field = test_response_schema["properties"]["optional_field"]

        # Should have type: string and nullable: true after normalization
        assert optional_field.get("type") == "string", "Array type should be converted to base type"
        assert optional_field.get("nullable") is True, "Should have nullable: true after normalization"
