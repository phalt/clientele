"""Integration tests for fixture schemas to ensure clientele can handle real-world OpenAPI specs."""

import tempfile
from pathlib import Path

import pytest
from openapi_core import Spec

from clientele.generators.standard.generator import StandardGenerator


def load_fixture_spec(spec_path: Path) -> Spec:
    """Load an OpenAPI spec from a fixture file."""
    with open(spec_path, "r") as f:
        return Spec.from_file(f)


# Define all fixture schemas to test
# Some schemas are marked as xfail due to advanced features or edge cases not yet supported
FIXTURE_SCHEMAS = [
    # OpenAPI examples directory
    pytest.param(
        "tests/fixtures/openapi_examples/api-with-examples.json",
        marks=pytest.mark.xfail(reason="Missing 'schema' key in response definitions"),
    ),
    pytest.param(
        "tests/fixtures/openapi_examples/callback-example.json",
        marks=pytest.mark.xfail(reason="Callbacks feature not yet supported"),
    ),
    pytest.param(
        "tests/fixtures/openapi_examples/non-oauth-scopes.json",
        marks=pytest.mark.xfail(reason="Missing 'responses' key in path definitions"),
    ),
    "tests/fixtures/openapi_examples/petstore-expanded.json",
    "tests/fixtures/openapi_examples/petstore.json",
    "tests/fixtures/openapi_examples/tictactoe.json",
    "tests/fixtures/openapi_examples/uspto.json",
    "tests/fixtures/openapi_examples/webhook-example.json",
    # Root fixtures directory
    pytest.param(
        "tests/fixtures/callback_example.yaml",
        marks=pytest.mark.xfail(reason="Callbacks feature not yet supported"),
    ),
    "tests/fixtures/complex_api.yaml",
    "tests/fixtures/petstore_openapi3.yaml",
    # Real-world schemas
    "tests/fixtures/realworld/1password.yaml",
    "tests/fixtures/realworld/ably.yaml",
    "tests/fixtures/realworld/google.yaml",
    "tests/fixtures/realworld/medium.yaml",
    "tests/fixtures/realworld/spacetraders.yaml",
    pytest.param(
        "tests/fixtures/realworld/twilio.yaml",
        marks=pytest.mark.xfail(reason="Very large complex schema with edge case syntax error"),
    ),
]


@pytest.mark.parametrize("fixture_path", FIXTURE_SCHEMAS)
def test_fixture_schema_generates_client(fixture_path):
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
        generator = StandardGenerator(
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
        assert (output_dir / "http.py").exists(), f"http.py not created for {fixture_path}"
        assert (output_dir / "config.py").exists(), f"config.py not created for {fixture_path}"
        assert (output_dir / "__init__.py").exists(), f"__init__.py not created for {fixture_path}"

        # Verify files have content
        client_content = (output_dir / "client.py").read_text()
        assert len(client_content) > 0, f"client.py is empty for {fixture_path}"

        schemas_content = (output_dir / "schemas.py").read_text()
        assert len(schemas_content) > 0, f"schemas.py is empty for {fixture_path}"

        # Verify the generated files are valid Python
        try:
            compile(client_content, str(output_dir / "client.py"), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated client.py has syntax errors for {fixture_path}: {e}")

        try:
            compile(schemas_content, str(output_dir / "schemas.py"), "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated schemas.py has syntax errors for {fixture_path}: {e}")
