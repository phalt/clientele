"""
Regression tests for GitHub issue #268.

A property is required only when it is listed in its schema's `required`
array. When a schema had no `required` array (or an empty one), the generator
treated every property as required instead of optional.
"""

import json
import sys
from contextlib import contextmanager

import pydantic
import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 268", "version": "0.1.0"},
    "paths": {
        "/foos": {
            "post": {
                "operationId": "create_foo",
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FooCreateParams"}}}
                },
                "responses": {"201": {"description": "Created"}},
            },
            "patch": {
                "operationId": "update_foo",
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FooUpdateParams"}}}
                },
                "responses": {"200": {"description": "OK"}},
            },
            "put": {
                "operationId": "replace_foo",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "title": "InlineReplaceParams",
                                "properties": {"name": {"type": "string"}},
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}},
            },
        }
    },
    "components": {
        "schemas": {
            "FooCreateParams": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
            },
            "FooUpdateParams": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
            },
            "FooEmptyRequired": {
                "type": "object",
                "required": [],
                "properties": {"name": {"type": "string"}},
            },
            "FooAllOf": {
                "allOf": [
                    {"$ref": "#/components/schemas/FooUpdateParams"},
                    {"type": "object", "properties": {"count": {"type": "integer"}}},
                ]
            },
        }
    },
}


@pytest.fixture
def schemas(tmp_path):
    spec_path = tmp_path / "issue_268.json"
    spec_path.write_text(json.dumps(SPEC))
    output_dir = tmp_path / "issue_268_client"
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_file(str(spec_path)),
        output_dir=str(output_dir),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()

    with _import_generated(tmp_path):
        from issue_268_client import schemas  # type: ignore

        yield schemas


@contextmanager
def _import_generated(path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))
        for mod in list(sys.modules):
            if mod.startswith("issue_268_client"):
                del sys.modules[mod]


def test_schema_without_required_array_has_optional_properties(schemas):
    params = schemas.FooUpdateParams()

    assert params.name is None
    assert params.description is None


def test_schema_with_empty_required_array_has_optional_properties(schemas):
    assert schemas.FooEmptyRequired().name is None


def test_listed_required_properties_stay_required(schemas):
    with pytest.raises(pydantic.ValidationError):
        schemas.FooCreateParams()

    params = schemas.FooCreateParams(name="foo")
    assert params.name == "foo"
    assert params.description is None


def test_inline_request_body_without_required_array_has_optional_properties(schemas):
    assert schemas.InlineReplaceParams().name is None


def test_allof_parts_without_required_array_have_optional_properties(schemas):
    params = schemas.FooAllOf()

    assert params.name is None
    assert params.count is None


def test_optional_nullable_property_is_not_wrapped_in_optional_twice(tmp_path, schemas):
    source = (tmp_path / "issue_268_client" / "schemas.py").read_text()

    assert "description: str | None = None" in source
    assert "typing.Optional[str | None]" not in source
