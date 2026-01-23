"""Additional tests for edge cases to reach 100% coverage."""

import json
import tempfile
from pathlib import Path

import pytest

from clientele import cli


@pytest.fixture
def openapi_30_spec():
    """Fixture providing a pure OpenAPI 3.0 spec (no 3.1 features)."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_get",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


def test_load_openapi_spec_no_normalization_needed(openapi_30_spec):
    """Test that _load_openapi_spec returns original spec when no normalization needed."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(openapi_30_spec, f)
        spec_file = f.name

    try:
        spec = cli._load_openapi_spec(file=spec_file)
        # Should successfully load without normalization (line 46 coverage)
        assert spec is not None
        assert spec.info.title == "Test API"
    finally:
        Path(spec_file).unlink()


def test_schemas_generator_no_schemas_branch():
    """Test schemas generator when components has no schemas attribute."""
    from clientele.generators.standard.generators.schemas import SchemasGenerator

    # Create a spec with components that has schemas=None
    spec_dict = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "components": {},
        "paths": {},
    }

    from cicerone import parse as cicerone_parse

    spec = cicerone_parse.parse_spec_from_dict(spec_dict)

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SchemasGenerator(spec=spec, output_dir=str(tmpdir))

        # This should exercise lines 231-232 (no schemas in components)
        # The method should return early without generating anything
        generator.generate_schema_classes()

        # Should complete without error
