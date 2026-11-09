"""
Regression tests for GitHub issue #277.

Enum member names are built by upper-casing each value and dropping characters
that aren't valid in an identifier. Two values that differ only by those
characters (e.g. "AAA" and "AA|A") got the same member name, so the generated
`schemas.py` failed to import with `TypeError: 'AAA' already defined`.
"""

import json
import sys
from contextlib import contextmanager

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator
from clientele.generators.shared.schemas import SchemasGenerator

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 277", "version": "0.1.0"},
    "paths": {
        "/ratings": {
            "get": {
                "operationId": "get_rating",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Rating"}}},
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            "Rating": {"type": "string", "enum": ["AAA", "AA|A"]},
            "ThreeWay": {"type": "string", "enum": ["X", "X|", "X!"]},
            "Status": {"type": "string", "enum": ["active", "in-progress", "on.hold", "class"]},
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
            if mod.startswith("issue_277_client"):
                del sys.modules[mod]


@pytest.fixture
def generated(tmp_path):
    spec_path = tmp_path / "issue_277.json"
    spec_path.write_text(json.dumps(SPEC))
    output_dir = tmp_path / "issue_277_client"
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_file(str(spec_path)),
        output_dir=str(output_dir),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()
    return tmp_path


@pytest.fixture
def schemas(generated):
    with _import_generated(generated):
        from issue_277_client import schemas  # type: ignore

        yield schemas


def test_values_differing_only_by_punctuation_get_distinct_members(schemas):
    assert {m.value for m in schemas.Rating} == {"AAA", "AA|A"}
    assert schemas.Rating.AAA.value == "AAA"
    assert schemas.Rating.AAA_2.value == "AA|A"


def test_three_colliding_values_get_numbered_suffixes(schemas):
    assert {m.name: m.value for m in schemas.ThreeWay} == {"X": "X", "X_2": "X|", "X_3": "X!"}


def test_non_colliding_enum_output_is_unchanged(generated):
    source = (generated / "issue_277_client" / "schemas.py").read_text()

    expected = (
        "class Status(str, enum.Enum):\n"
        '    ACTIVE = "active"\n'
        '    IN_PROGRESS = "in-progress"\n'
        '    ON_HOLD = "on.hold"\n'
        '    CLASS_ = "class"\n'
    )
    assert expected in source


def test_generate_enum_properties_dedupes_member_names():
    generator = SchemasGenerator(spec=cicerone_parse.parse_spec_from_dict(SPEC), output_dir="", writer=None)
    values = ["AAA", "AA|A", "A|AA", "B"]

    result = generator.generate_enum_properties({v: {"type": f'"{v}"'} for v in values})

    assert result == ('    AAA = "AAA"\n    AAA_2 = "AA|A"\n    AAA_3 = "A|AA"\n    B = "B"\n')


def test_generate_enum_properties_suffix_does_not_clash_with_real_value():
    generator = SchemasGenerator(spec=cicerone_parse.parse_spec_from_dict(SPEC), output_dir="", writer=None)
    values = ["X", "X|", "X_2"]

    result = generator.generate_enum_properties({v: {"type": f'"{v}"'} for v in values})

    names = [line.split(" = ")[0].strip() for line in result.splitlines()]
    assert len(names) == len(set(names))
    assert names[:2] == ["X", "X_2"]
