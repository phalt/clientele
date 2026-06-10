"""
Tests for the `clientele validate` command.

Before this command existed, incompatible specs failed half-way through
generation (missing $refs crash with AttributeError or silently produce
broken output) and unsupported constructs (cookie parameters, multipart
bodies) were silently dropped. `clientele validate` is a pre-flight check:
it walks the spec, reports errors (things that break generation) and
warnings (things that degrade), and exits non-zero on errors so it can
gate CI.
"""

import json

import pytest
from cicerone import parse as cicerone_parse
from click.testing import CliRunner

from clientele import cli
from clientele.generators.validation import SpecValidator


@pytest.fixture
def runner():
    return CliRunner()


def _base_spec(**overrides):
    spec = {
        "openapi": "3.0.2",
        "info": {"title": "Validation Test API", "version": "1.0.0"},
        "paths": {
            "/things": {
                "get": {
                    "operationId": "listThings",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Thing": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    }
    spec.update(overrides)
    return spec


def _validate(spec_dict):
    spec = cicerone_parse.parse_spec_from_dict(spec_dict)
    return SpecValidator(spec=spec).validate()


def _write_spec(tmp_path, spec_dict):
    spec_path = tmp_path / "openapi.json"
    spec_path.write_text(json.dumps(spec_dict))
    return spec_path


class TestSpecValidatorCleanSpec:
    def test_clean_spec_has_no_findings(self):
        assert _validate(_base_spec()) == []


class TestSpecValidatorMissingRefs:
    def test_missing_schema_ref_in_response_is_an_error(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] = {
            "$ref": "#/components/schemas/DoesNotExist"
        }
        findings = _validate(spec)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert "DoesNotExist" in errors[0].message
        assert "GET /things" in errors[0].location

    def test_missing_schema_ref_in_component_property_is_an_error(self):
        spec = _base_spec()
        spec["components"]["schemas"]["Thing"]["properties"]["owner"] = {"$ref": "#/components/schemas/Missing"}
        findings = _validate(spec)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert "Missing" in errors[0].message
        assert "Thing" in errors[0].location

    def test_missing_schema_ref_in_array_items_is_an_error(self):
        spec = _base_spec()
        spec["components"]["schemas"]["Thing"]["properties"]["tags"] = {
            "type": "array",
            "items": {"$ref": "#/components/schemas/Tag"},
        }
        findings = _validate(spec)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert "Tag" in errors[0].message

    def test_missing_parameter_ref_is_an_error(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["parameters"] = [{"$ref": "#/components/parameters/NoSuchParam"}]
        findings = _validate(spec)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 1
        assert "NoSuchParam" in errors[0].message

    def test_resolvable_refs_are_not_reported(self):
        spec = _base_spec()
        spec["components"]["schemas"]["Owner"] = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        spec["components"]["schemas"]["Thing"]["properties"]["owner"] = {"$ref": "#/components/schemas/Owner"}
        assert _validate(spec) == []


class TestSpecValidatorUnsupportedRefs:
    def test_non_component_ref_is_a_warning(self):
        spec = _base_spec()
        spec["components"]["schemas"]["Thing"]["properties"]["odd"] = {"$ref": "#/paths/~1things/get/responses/200"}
        findings = _validate(spec)
        warnings = [f for f in findings if f.severity == "warning"]
        assert len(warnings) == 1
        assert "typing.Any" in warnings[0].message


class TestSpecValidatorParameters:
    def test_cookie_parameter_is_a_warning(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["parameters"] = [
            {
                "name": "session_id",
                "in": "cookie",
                "required": False,
                "schema": {"type": "string"},
            }
        ]
        findings = _validate(spec)
        warnings = [f for f in findings if f.severity == "warning"]
        assert len(warnings) == 1
        assert "session_id" in warnings[0].message
        assert "cookie" in warnings[0].message.lower()
        assert "GET /things" in warnings[0].location

    def test_query_path_and_header_parameters_are_supported(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["parameters"] = [
            {"name": "page", "in": "query", "schema": {"type": "integer"}},
            {"name": "X-Trace", "in": "header", "schema": {"type": "string"}},
        ]
        assert _validate(spec) == []


class TestSpecValidatorRequestBodies:
    def test_multipart_body_is_a_warning(self):
        spec = _base_spec()
        spec["paths"]["/things"]["post"] = {
            "operationId": "uploadThing",
            "requestBody": {
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {"file": {"type": "string", "format": "binary"}},
                        }
                    }
                }
            },
            "responses": {"204": {"description": "No Content"}},
        }
        findings = _validate(spec)
        warnings = [f for f in findings if f.severity == "warning"]
        assert len(warnings) == 1
        assert "multipart/form-data" in warnings[0].message
        assert "POST /things" in warnings[0].location


class TestSpecValidatorResponses:
    def test_operation_without_responses_is_a_warning(self):
        spec = _base_spec()
        del spec["paths"]["/things"]["get"]["responses"]
        findings = _validate(spec)
        warnings = [f for f in findings if f.severity == "warning"]
        assert len(warnings) == 1
        assert "responses" in warnings[0].message.lower()

    def test_response_content_without_schema_is_a_warning(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["responses"]["200"]["content"]["application/json"] = {}
        findings = _validate(spec)
        warnings = [f for f in findings if f.severity == "warning"]
        assert len(warnings) == 1
        assert "schema" in warnings[0].message.lower()

    def test_no_content_responses_are_fine(self):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["responses"] = {"204": {"description": "No Content"}}
        assert _validate(spec) == []


class TestValidateCommand:
    def test_requires_url_or_file(self, runner):
        result = runner.invoke(cli.cli_group, ["validate"])
        assert result.exit_code != 0

    def test_clean_spec_exits_zero(self, runner, tmp_path):
        spec_path = _write_spec(tmp_path, _base_spec())
        result = runner.invoke(cli.cli_group, ["validate", "--file", str(spec_path)])
        assert result.exit_code == 0
        assert "no issues" in result.output.lower()

    def test_spec_with_errors_exits_one(self, runner, tmp_path):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] = {
            "$ref": "#/components/schemas/DoesNotExist"
        }
        spec_path = _write_spec(tmp_path, spec)
        result = runner.invoke(cli.cli_group, ["validate", "--file", str(spec_path)])
        assert result.exit_code == 1
        assert "DoesNotExist" in result.output

    def test_spec_with_only_warnings_exits_zero(self, runner, tmp_path):
        spec = _base_spec()
        spec["paths"]["/things"]["get"]["parameters"] = [{"name": "sid", "in": "cookie", "schema": {"type": "string"}}]
        spec_path = _write_spec(tmp_path, spec)
        result = runner.invoke(cli.cli_group, ["validate", "--file", str(spec_path)])
        assert result.exit_code == 0
        assert "warning" in result.output.lower()

    def test_unparseable_file_exits_one_with_message(self, runner, tmp_path):
        bad = tmp_path / "openapi.json"
        bad.write_text("{ this is not json")
        result = runner.invoke(cli.cli_group, ["validate", "--file", str(bad)])
        assert result.exit_code == 1
        assert "could not" in result.output.lower() or "error" in result.output.lower()

    def test_swagger_2_spec_is_auto_converted_and_validates(self, runner, tmp_path):
        # cicerone auto-converts Swagger 2.0 specs to OpenAPI 3.0 at parse
        # time (the same path start-api uses), so validate accepts them.
        spec = {
            "swagger": "2.0",
            "info": {"title": "Old API", "version": "1.0.0"},
            "paths": {},
        }
        spec_path = _write_spec(tmp_path, spec)
        result = runner.invoke(cli.cli_group, ["validate", "--file", str(spec_path)])
        assert result.exit_code == 0

    def test_validates_real_example_spec(self, runner):
        from tests.generators.integration_utils import get_spec_path

        result = runner.invoke(cli.cli_group, ["validate", "--file", str(get_spec_path("best.json"))])
        assert result.exit_code == 0
