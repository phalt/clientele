"""
Regression tests for GitHub issue #278.

A discriminated `oneOf` is generated as `typing.Annotated[A | B, pydantic.Field(discriminator=...)]`,
and pydantic needs the discriminator on every member to be a `Literal`. `const` already became
`typing.Literal[...]`, but an inline multi-value `enum` (which pydantic/FastAPI emit for
`Literal["cat", "kitten"]`) became `str`, so importing `schemas.py` failed with
`PydanticUserError: Model 'Cat' needs field 'kind' to be of type Literal`.
"""

import json
import sys
from contextlib import contextmanager

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_spec
from clientele.generators.shared import utils

CLIENT_NAME = "issue_278_client"

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 278", "version": "0.1.0"},
    "paths": {
        "/things": {
            "get": {
                "operationId": "get_things",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Owner"}}},
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            # Repro from the issue
            "Cat": {
                "type": "object",
                "properties": {"kind": {"type": "string", "enum": ["cat", "kitten"]}},
                "required": ["kind"],
            },
            "Dog": {
                "type": "object",
                "properties": {"kind": {"type": "string", "const": "dog"}},
                "required": ["kind"],
            },
            "Owner": {
                "type": "object",
                "required": ["pet"],
                "properties": {
                    "pet": {
                        "oneOf": [{"$ref": "#/components/schemas/Cat"}, {"$ref": "#/components/schemas/Dog"}],
                        "discriminator": {
                            "propertyName": "kind",
                            "mapping": {
                                "cat": "#/components/schemas/Cat",
                                "kitten": "#/components/schemas/Cat",
                                "dog": "#/components/schemas/Dog",
                            },
                        },
                    }
                },
            },
            # Other inline enum shapes
            "Thing": {
                "type": "object",
                "required": ["letter", "number", "nullable_30", "nullable_31", "null_member"],
                "properties": {
                    "letter": {"type": "string", "enum": ["a", "b"]},
                    "number": {"type": "integer", "enum": [1, 2]},
                    "nullable_30": {"type": "string", "enum": ["a", "b"], "nullable": True},
                    "nullable_31": {"type": ["string", "null"], "enum": ["a", "b", None]},
                    "null_member": {"type": "string", "enum": ["a", "b", None]},
                    "letters": {"type": "array", "items": {"type": "string", "enum": ["x", "y"]}},
                },
            },
            # Top-level enum component stays an enum.Enum
            "Colour": {"type": "string", "enum": ["red", "dark-green"]},
        }
    },
}


@contextmanager
def _import_generated(path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))
        for mod in list(sys.modules):
            if mod.startswith(CLIENT_NAME):
                del sys.modules[mod]


@pytest.fixture
def generated(tmp_path):
    spec_path = tmp_path / "issue_278.json"
    spec_path.write_text(json.dumps(SPEC))
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_dict(normalize_openapi_31_spec(SPEC)),
        output_dir=str(tmp_path / CLIENT_NAME),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()
    return tmp_path


@pytest.fixture
def source(generated):
    return (generated / CLIENT_NAME / "schemas.py").read_text()


@pytest.fixture
def schemas(generated):
    with _import_generated(generated):
        from issue_278_client import schemas  # type: ignore

        yield schemas


def test_discriminated_union_with_multi_value_enum_tag_imports_and_validates(schemas):
    assert isinstance(schemas.Owner.model_validate({"pet": {"kind": "kitten"}}).pet, schemas.Cat)
    assert isinstance(schemas.Owner.model_validate({"pet": {"kind": "cat"}}).pet, schemas.Cat)
    assert isinstance(schemas.Owner.model_validate({"pet": {"kind": "dog"}}).pet, schemas.Dog)


def test_inline_string_enum_is_literal(source):
    assert 'kind: typing.Literal["cat", "kitten"]' in source
    assert 'letter: typing.Literal["a", "b"]' in source


def test_inline_integer_enum_is_literal(source):
    assert "number: typing.Literal[1, 2]" in source


def test_nullable_inline_enum_is_optional_literal(source):
    expected = 'typing.Optional[typing.Literal["a", "b"]]'
    assert f"nullable_30: {expected}" in source
    # OpenAPI 3.1: `type: ["string", "null"]` with `null` in the enum
    assert f"nullable_31: {expected}" in source
    # `null` in the enum list alone
    assert f"null_member: {expected}" in source


def test_inline_enum_in_array_items_is_literal(source):
    assert 'letters: typing.Optional[list[typing.Literal["x", "y"]]] = None' in source


def test_inline_enum_rejects_unknown_values(schemas):
    with pytest.raises(Exception):
        schemas.Thing.model_validate(
            {"letter": "z", "number": 1, "nullable_30": None, "nullable_31": None, "null_member": None}
        )
    thing = schemas.Thing.model_validate(
        {"letter": "a", "number": 2, "nullable_30": None, "nullable_31": "b", "null_member": None}
    )
    assert thing.letter == "a"
    assert thing.nullable_31 == "b"


def test_top_level_enum_component_is_unchanged(source, schemas):
    assert 'class Colour(str, enum.Enum):\n    RED = "red"\n    DARK_GREEN = "dark-green"\n' in source
    assert schemas.Colour.DARK_GREEN.value == "dark-green"


@pytest.mark.parametrize(
    "schema, expected",
    [
        ({"type": "string", "enum": ["a", "b"]}, "typing.Literal['a', 'b']"),
        ({"type": "integer", "enum": [1, 2]}, "typing.Literal[1, 2]"),
        ({"type": "string", "enum": ["a"], "nullable": True}, "typing.Optional[typing.Literal['a']]"),
        ({"type": "string", "enum": ["a", None]}, "typing.Optional[typing.Literal['a']]"),
        # Values that can't go in a Literal keep the old behaviour
        ({"type": "number", "enum": [1.5, 2.5]}, "float"),
        ({"type": "string", "enum": [None], "nullable": True}, "typing.Optional[str]"),
    ],
)
def test_get_type_inline_enum(schema, expected):
    assert utils.get_type(schema) == expected
