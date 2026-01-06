import tempfile
from pathlib import Path

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator
from clientele.generators.standard.generator import StandardGenerator


@pytest.mark.parametrize("generator_class", [StandardGenerator, APIGenerator])
def test_openapi_31_null_type_in_anyof(generator_class):
    # OpenAPI 3.1.0 schema - FastAPI 0.125.0
    openapi_spec = """
openapi: 3.1.0
info:
  title: FastAPI Example
  version: 1.0.0
paths:
  /example:
    get:
      operationId: get_example
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Example'
components:
  schemas:
    Example:
      type: object
      properties:
        id:
          anyOf:
            - type: integer
            - type: "null"
          title: Id
        metadata:
          anyOf:
            - additionalProperties: true
              type: object
            - type: "null"
          title: Metadata
      title: Example
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write spec to file
        spec_file = Path(tmpdir) / "spec.yaml"
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

        # Verify that the Example schema exists
        assert "class Example" in schemas_content

        # Check that 'id' field uses None not null - handle different python union syntaxes
        assert "id: int | None" in schemas_content or "id: typing.Union[int, None]" in schemas_content

        # Check that 'metadata' field uses None not null
        assert (
            "metadata: dict[str, typing.Any] | None" in schemas_content
            or "metadata: typing.Union[dict[str, typing.Any], None]" in schemas_content
        )

        # Verify the schema compiles without errors
        compile(schemas_content, str(schemas_file), "exec")


@pytest.mark.parametrize("generator_class", [StandardGenerator, APIGenerator])
def test_openapi_31_null_only_type(generator_class):
    openapi_spec = """
openapi: 3.1.0
info:
  title: Test
  version: 1.0.0
paths:
  /test:
    get:
      operationId: get_test
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TestSchema'
components:
  schemas:
    TestSchema:
      type: object
      properties:
        always_null:
          type: "null"
          title: Always Null
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        spec_file = Path(tmpdir) / "spec.yaml"
        spec_file.write_text(openapi_spec)

        spec = cicerone_parse.parse_spec_from_file(str(spec_file))

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

        schemas_file = output_dir / "schemas.py"
        schemas_content = schemas_file.read_text()

        # A field that's only null should be None
        assert "always_null: None" in schemas_content

        # Verify it compiles
        compile(schemas_content, str(schemas_file), "exec")
