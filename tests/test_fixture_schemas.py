"""Integration tests for fixture schemas to ensure clientele can handle real-world OpenAPI specs."""

import tempfile
from pathlib import Path

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator
from clientele.generators.standard.generator import StandardGenerator


def load_fixture_spec(spec_path: Path):
    """Load an OpenAPI spec from a fixture file."""
    return cicerone_parse.parse_spec_from_file(str(spec_path))


def get_regression_schemas() -> list[str]:
    """Discover all schema files in the regressions fixture directory."""
    regressions_dir = Path(__file__).parent / "fixtures" / "regression"
    if not regressions_dir.exists():
        return []
    schemas = []
    for ext in ["*.yaml", "*.yml", "*.json"]:
        schemas.extend(regressions_dir.glob(ext))
    return [str(p.relative_to(Path(__file__).parent.parent)) for p in sorted(schemas)]


# Define all fixture schemas to test
# Some schemas are marked as xfail due to advanced features or edge cases not yet supported
# Callback schemas are excluded as they define server-side webhook handlers, not client operations
FIXTURE_SCHEMAS = [
    # OpenAPI examples directory
    "tests/fixtures/openapi_examples/api-with-examples.json",
    "tests/fixtures/openapi_examples/non-oauth-scopes.json",
    "tests/fixtures/openapi_examples/petstore-expanded.json",
    "tests/fixtures/openapi_examples/petstore.json",
    "tests/fixtures/openapi_examples/tictactoe.json",
    "tests/fixtures/openapi_examples/uspto.json",
    "tests/fixtures/openapi_examples/webhook-example.json",
    # Root fixtures directory
    "tests/fixtures/complex_api.yaml",
    "tests/fixtures/petstore_openapi3.yaml",
    # Real-world schemas
    "tests/fixtures/realworld/1password.yaml",
    "tests/fixtures/realworld/ably.yaml",
    "tests/fixtures/realworld/google.yaml",
    "tests/fixtures/realworld/medium.yaml",
    "tests/fixtures/realworld/spacetraders.yaml",
    "tests/fixtures/realworld/twilio.yaml",
    # Auto-discovered regression schemas
    *get_regression_schemas(),
]


def validate_generated_python_file(file_path: Path, file_content: str, fixture_path: str) -> None:
    """
    Validate that a generated Python file is syntactically correct.

    Args:
        file_path: Path to the file being validated
        file_content: Content of the Python file
        fixture_path: Path to the original fixture schema (for error messages)

    Raises:
        AssertionError: If the file has syntax errors
    """
    try:
        compile(file_content, str(file_path), "exec")
    except SyntaxError as e:
        pytest.fail(f"Generated {file_path.name} has syntax errors for {fixture_path}: {e}")


@pytest.mark.parametrize("fixture_path", FIXTURE_SCHEMAS)
@pytest.mark.parametrize("client_generator", [APIGenerator, StandardGenerator])
def test_fixture_schema_generates_client(fixture_path, client_generator) -> None:
    """Test that each fixture schema can generate a working client."""
    base_path = Path(__file__).parent.parent
    spec_path = base_path / fixture_path

    # Skip if file doesn't exist or is empty
    if not spec_path.exists() or spec_path.stat().st_size == 0:
        pytest.skip(f"Schema file {fixture_path} does not exist or is empty")

    # Load the spec
    try:
        spec = load_fixture_spec(spec_path)
    except Exception as e:
        pytest.fail(f"Failed to load spec from {fixture_path}: {e}")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "generated_client"

        # Create generator
        generator = client_generator(
            spec=spec,
            asyncio=False,
            regen=True,
            output_dir=str(output_dir),
            url=None,
            file=str(spec_path),
        )

        # Generate client
        try:
            generator.generate()
        except Exception as e:
            pytest.fail(f"Failed to generate client from {fixture_path}: {e}")

        # Verify expected files were created
        assert (output_dir / "client.py").exists(), f"client.py not created for {fixture_path}"
        assert (output_dir / "schemas.py").exists(), f"schemas.py not created for {fixture_path}"
        assert (output_dir / "config.py").exists(), f"config.py not created for {fixture_path}"
        assert (output_dir / "__init__.py").exists(), f"__init__.py not created for {fixture_path}"

        # Verify files have content
        client_content = (output_dir / "client.py").read_text()
        assert len(client_content) > 0, f"client.py is empty for {fixture_path}"

        schemas_content = (output_dir / "schemas.py").read_text()
        assert len(schemas_content) > 0, f"schemas.py is empty for {fixture_path}"

        # Verify the generated files are valid Python
        validate_generated_python_file(output_dir / "client.py", client_content, fixture_path)
        validate_generated_python_file(output_dir / "schemas.py", schemas_content, fixture_path)
