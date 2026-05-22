"""Tests for generator modules to achieve full coverage."""

import json
import tempfile
from pathlib import Path

import pytest

from clientele.generators.api import writer as api_writer
from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_schema, normalize_openapi_31_spec
from clientele.generators.shared.generators.schemas import SchemasGenerator


def test_normalize_openapi_31_schema_only_null_type():
    """Test schema with only null type becomes nullable string."""
    schema = {"type": ["null"]}
    result = normalize_openapi_31_schema(schema)
    assert result["type"] == "string"
    assert result["nullable"] is True


def test_normalize_openapi_31_schema_preserves_existing_nullable():
    """Test that existing nullable: true is preserved."""
    schema = {"type": "string", "nullable": True}
    result = normalize_openapi_31_schema(schema)
    assert result["nullable"] is True


def test_normalize_openapi_31_schema_items():
    """Test normalization of array items."""
    schema = {"type": "array", "items": {"type": ["string", "null"]}}
    result = normalize_openapi_31_schema(schema)
    assert result["items"]["type"] == "string"
    assert result["items"]["nullable"] is True


def test_normalize_openapi_31_schema_allof():
    """Test normalization of allOf schemas."""
    schema = {"allOf": [{"type": ["string", "null"]}, {"minLength": 1}]}
    result = normalize_openapi_31_schema(schema)
    assert result["allOf"][0]["type"] == "string"
    assert result["allOf"][0]["nullable"] is True


def test_normalize_openapi_31_schema_oneof():
    """Test normalization of oneOf schemas."""
    schema = {"oneOf": [{"type": ["integer", "null"]}, {"type": "string"}]}
    result = normalize_openapi_31_schema(schema)
    assert result["oneOf"][0]["type"] == "integer"
    assert result["oneOf"][0]["nullable"] is True


def test_normalize_openapi_31_schema_anyof():
    """Test normalization of anyOf schemas."""
    schema = {"anyOf": [{"type": ["boolean", "null"]}, {"type": "number"}]}
    result = normalize_openapi_31_schema(schema)
    assert result["anyOf"][0]["type"] == "boolean"
    assert result["anyOf"][0]["nullable"] is True


def test_normalize_openapi_31_spec_components_schemas():
    """Test normalization of schemas in components."""
    spec = {
        "openapi": "3.1.0",
        "components": {"schemas": {"NullableString": {"type": ["string", "null"]}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["components"]["schemas"]["NullableString"]["type"] == "string"
    assert result["components"]["schemas"]["NullableString"]["nullable"] is True


def test_normalize_openapi_31_spec_request_body():
    """Test normalization of request body schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "post": {"requestBody": {"content": {"application/json": {"schema": {"type": ["string", "null"]}}}}}
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    schema = result["paths"]["/test"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert schema["type"] == "string"
    assert schema["nullable"] is True


def test_normalize_openapi_31_spec_response_schemas():
    """Test normalization of response schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "get": {
                    "responses": {"200": {"content": {"application/json": {"schema": {"type": ["integer", "null"]}}}}}
                }
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    schema = result["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "integer"
    assert schema["nullable"] is True


def test_normalize_openapi_31_spec_parameter_schemas():
    """Test normalization of parameter schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {
                            "name": "test_param",
                            "in": "query",
                            "schema": {"type": ["boolean", "null"]},
                        }
                    ]
                }
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    param_schema = result["paths"]["/test"]["get"]["parameters"][0]["schema"]
    assert param_schema["type"] == "boolean"
    assert param_schema["nullable"] is True


def test_normalize_openapi_31_spec_non_dict_path_item():
    """Test that non-dict path items are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": "not a dict",
        },
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"] == "not a dict"


def test_normalize_openapi_31_spec_dollar_prefixed_keys():
    """Test that $-prefixed keys (like $ref) are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"$ref": "#/components/paths/TestPath"}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["$ref"] == "#/components/paths/TestPath"


def test_normalize_openapi_31_spec_non_dict_response():
    """Test that non-dict responses are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"get": {"responses": {"200": "not a dict"}}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["get"]["responses"]["200"] == "not a dict"


def test_normalize_openapi_31_spec_non_dict_parameter():
    """Test that non-dict parameters are handled."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"get": {"parameters": ["not a dict"]}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["get"]["parameters"][0] == "not a dict"


class TestGeneratorCoverage:
    """Tests for generator module coverage."""

    @pytest.mark.parametrize("generator_class", [APIGenerator])
    def test_generator_removes_existing_file(self, generator_class):
        """Test that generators removes existing files before regenerating."""

        openapi_spec = {
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(openapi_spec, f)
            spec_file = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_client"

            try:
                from cicerone import parse as cicerone_parse

                spec = cicerone_parse.parse_spec_from_file(spec_file)

                generator = generator_class(
                    spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=spec_file
                )
                generator.generate()

                assert (output_dir / "client.py").exists()

                test_file = output_dir / "schemas.py"
                test_file.write_text("# Old content")

                generator2 = generator_class(
                    spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=spec_file
                )
                generator2.generate()

                assert test_file.exists()
                assert "# Old content" not in test_file.read_text()

            finally:
                Path(spec_file).unlink()

    @pytest.mark.parametrize("generator_class", [APIGenerator])
    def test_generator_with_servers(self, generator_class):
        """Test generator with servers in spec."""

        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test_get",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(openapi_spec, f)
            spec_file = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "test_client"

            try:
                from cicerone import parse as cicerone_parse

                spec = cicerone_parse.parse_spec_from_file(spec_file)

                generator = generator_class(
                    spec=spec, asyncio=False, regen=True, output_dir=str(output_dir), url=None, file=spec_file
                )
                generator.generate()

                assert (output_dir / "config.py").exists()
                client_content = (output_dir / "config.py").read_text()
                assert "api.example.com" in client_content  # nosec: B113

            finally:
                Path(spec_file).unlink()

    def test_schemas_generator_no_components(self):
        """Test schemas generator with no components in spec."""

        openapi_spec = {
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(openapi_spec, f)
            spec_file = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                from cicerone import parse as cicerone_parse

                spec = cicerone_parse.parse_spec_from_file(spec_file)

                generator = SchemasGenerator(spec=spec, output_dir=str(tmpdir), writer=api_writer)

                generator.generate_schema_classes()

            finally:
                Path(spec_file).unlink()

    def test_schemas_generator_no_schemas_in_components(self):
        """Test schemas generator with components but no schemas."""

        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "components": {},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test_get",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(openapi_spec, f)
            spec_file = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                from cicerone import parse as cicerone_parse

                spec = cicerone_parse.parse_spec_from_file(spec_file)

                generator = SchemasGenerator(spec=spec, output_dir=str(tmpdir), writer=api_writer)

                generator.generate_schema_classes()

            finally:
                Path(spec_file).unlink()
