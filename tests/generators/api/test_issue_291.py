"""
Regression tests for GitHub issue #291.

`schemas.py` defined components in spec order. `oneOf`/`anyOf` components are module-level
type aliases and `type: array` components subclass `ListResponse[Item]`; both are evaluated
at import time, so one that came before a component it references failed to import with
`NameError: name '...' is not defined`. FastAPI sorts components alphabetically, so a union
named after its members (`Notification` before `NotificationAddUser`) broke out of the box.
"""

import ast
import collections
import importlib
import json
import sys

import pydantic
import pytest
from cicerone import parse as cicerone_parse

from clientele.generators import cicerone_compat
from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_spec
from clientele.generators.shared import schemas as schemas_module


def ref(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def tagged(tag: str) -> dict:
    return {
        "type": "object",
        "properties": {"kind": {"type": "string", "const": tag}, "value": {"type": "integer"}},
        "required": ["kind"],
    }


def spec_with(components: dict) -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Issue 291", "version": "0.1.0"},
        "paths": {
            "/things": {
                "get": {
                    "operationId": "get_things",
                    "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {}}}}},
                }
            }
        },
        "components": {"schemas": components},
    }


UNION_MEMBERS = {"UA": tagged("a"), "UB": tagged("b")}


def _generate(tmp_path, name: str, components: dict) -> str:
    spec = spec_with(components)
    spec_path = tmp_path / f"{name}.json"
    spec_path.write_text(json.dumps(spec))
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_dict(normalize_openapi_31_spec(spec)),
        output_dir=str(tmp_path / name),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()
    return (tmp_path / name / "schemas.py").read_text()


def _spec_order_generate_schema_classes(self) -> None:
    """The generator's loop before #291: components in spec order."""
    for schema_key, schema in self.spec.components.schemas.items():
        self.make_schema_class(schema_key=schema_key, schema=cicerone_compat.schema_to_dict(schema))


def _generate_in_spec_order(tmp_path, monkeypatch, name: str, components: dict) -> str:
    with monkeypatch.context() as m:
        m.setattr(schemas_module.SchemasGenerator, "generate_schema_classes", _spec_order_generate_schema_classes)
        return _generate(tmp_path, name, components)


def _import(tmp_path, name: str):
    sys.path.insert(0, str(tmp_path))
    try:
        return importlib.import_module(f"{name}.schemas")
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == name or mod.startswith(f"{name}."):
                del sys.modules[mod]


def _definitions(source: str) -> list[str]:
    """Names of the top-level classes and aliases in a generated schemas.py, in order."""
    names = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            names.append(node.name)
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            names.append(node.targets[0].id)
    return names


def _blocks(source: str) -> collections.Counter:
    """Every top-level statement's source, ignoring order."""
    tree = ast.parse(source)
    return collections.Counter(ast.get_source_segment(source, node) for node in tree.body)


@pytest.fixture
def build(tmp_path, monkeypatch):
    """Generate components, check only the order changed, and import the result."""

    def _build(name: str, components: dict):
        source = _generate(tmp_path, name, components)
        spec_order_source = _generate_in_spec_order(tmp_path, monkeypatch, f"{name}_spec_order", components)
        # Each definition is generated exactly as before; only the order differs.
        assert _blocks(source) == _blocks(spec_order_source)
        return source, _import(tmp_path, name)

    return _build


def test_one_of_with_discriminator_before_members(build):
    components = {
        "U": {"oneOf": [ref("UA"), ref("UB")], "discriminator": {"propertyName": "kind"}},
        **UNION_MEMBERS,
    }
    source, schemas = build("issue_291_one_of", components)
    assert _definitions(source)[:3] == ["UA", "UB", "U"]
    adapter = pydantic.TypeAdapter(schemas.U)
    assert isinstance(adapter.validate_python({"kind": "a"}), schemas.UA)
    assert isinstance(adapter.validate_python({"kind": "b"}), schemas.UB)


def test_any_of_before_members(build):
    components = {"U": {"anyOf": [ref("UA"), ref("UB")]}, **UNION_MEMBERS}
    source, schemas = build("issue_291_any_of", components)
    assert _definitions(source)[:3] == ["UA", "UB", "U"]
    adapter = pydantic.TypeAdapter(schemas.U)
    assert isinstance(adapter.validate_python({"kind": "b", "value": 1}), schemas.UB)


def test_array_before_item(build):
    components = {"L": {"type": "array", "items": ref("UA")}, "UA": tagged("a")}
    source, schemas = build("issue_291_array", components)
    assert _definitions(source)[:2] == ["UA", "L"]
    result = schemas.L.model_validate([{"kind": "a", "value": 1}])
    assert isinstance(result[0], schemas.UA)


def test_alias_of_alias_before_both(build):
    components = {
        "V": {"anyOf": [ref("U"), {"type": "string"}]},
        "U": {"anyOf": [ref("UA"), ref("UB")]},
        **UNION_MEMBERS,
    }
    source, schemas = build("issue_291_alias_of_alias", components)
    assert _definitions(source)[:4] == ["UA", "UB", "U", "V"]
    adapter = pydantic.TypeAdapter(schemas.V)
    assert adapter.validate_python("plain") == "plain"
    assert isinstance(adapter.validate_python({"kind": "a"}), schemas.UA)


def test_issue_276_shape_in_fastapi_alphabetical_order(build):
    notification = lambda action: {  # noqa: E731
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": [action], "default": action},
            "message": {"type": "string"},
        },
        "required": ["message"],
    }
    components = {
        "Notification": {
            "oneOf": [ref("NotificationAddUser"), ref("NotificationRemoveUser")],
            "discriminator": {"propertyName": "action"},
        },
        "NotificationAddUser": notification("add-user"),
        "NotificationRemoveUser": notification("remove-user"),
    }
    source, schemas = build("issue_291_fastapi", components)
    assert _definitions(source)[:3] == ["NotificationAddUser", "NotificationRemoveUser", "Notification"]
    adapter = pydantic.TypeAdapter(schemas.Notification)
    added = adapter.validate_python({"action": "add-user", "message": "hi"})
    removed = adapter.validate_python({"action": "remove-user", "message": "bye"})
    assert isinstance(added, schemas.NotificationAddUser)
    assert isinstance(removed, schemas.NotificationRemoveUser)


def test_nested_refs_in_inline_members_and_items(build):
    components = {
        "N": {"anyOf": [{"type": "array", "items": ref("UA")}, {"type": "null"}]},
        "L": {"type": "array", "items": {"oneOf": [ref("UA"), ref("pet-cat")]}},
        "UA": tagged("a"),
        "pet-cat": tagged("cat"),
    }
    source, schemas = build("issue_291_nested", components)
    names = _definitions(source)
    assert names.index("UA") < names.index("N")
    assert names.index("UA") < names.index("L")
    # Refs map to generated class names (`pet-cat` -> `PetCat`)
    assert names.index("PetCat") < names.index("L")
    adapter = pydantic.TypeAdapter(schemas.N)
    assert isinstance(adapter.validate_python([{"kind": "a"}])[0], schemas.UA)
    assert adapter.validate_python(None) is None
    assert isinstance(schemas.L.model_validate([{"kind": "cat"}])[0], schemas.PetCat)


def test_object_enum_and_all_of_components_do_not_move(build):
    components = {
        # allOf inlines its parents' properties, whether or not they were generated first
        "Child": {"allOf": [ref("Parent"), {"type": "object", "properties": {"extra": {"type": "string"}}}]},
        "Parent": {"allOf": [ref("UA")]},
        "Box": {"type": "object", "properties": {"u": ref("U")}},
        "U": {"oneOf": [ref("UA"), ref("UB")], "discriminator": {"propertyName": "kind"}},
        "Colour": {"type": "string", "enum": ["red", "green"]},
        **UNION_MEMBERS,
    }
    source, schemas = build("issue_291_stable", components)
    assert _definitions(source)[:7] == ["Child", "Parent", "Box", "Colour", "UA", "UB", "U"]
    assert isinstance(schemas.Box.model_validate({"u": {"kind": "b"}}).u, schemas.UB)


def test_valid_order_is_byte_identical(tmp_path, monkeypatch):
    components = {
        **UNION_MEMBERS,
        "Box": {"type": "object", "properties": {"u": ref("U")}},
        "U": {"oneOf": [ref("UA"), ref("UB")], "discriminator": {"propertyName": "kind"}},
        "L": {"type": "array", "items": ref("U")},
        "C": {"allOf": [ref("UA")]},
        "Colour": {"type": "string", "enum": ["red", "green"]},
    }
    source = _generate(tmp_path, "issue_291_valid", components)
    spec_order_source = _generate_in_spec_order(tmp_path, monkeypatch, "issue_291_valid", components)
    assert source == spec_order_source
    assert _definitions(source)[:7] == ["UA", "UB", "Box", "U", "L", "C", "Colour"]


@pytest.mark.parametrize(
    "components",
    [
        pytest.param(
            {"U": {"anyOf": [ref("UA"), ref("V")]}, "V": {"anyOf": [ref("U"), {"type": "string"}]}, "UA": tagged("a")},
            id="mutual",
        ),
        pytest.param({"T": {"anyOf": [ref("T"), {"type": "string"}]}}, id="self"),
    ],
)
def test_alias_cycle_generates_with_warning(tmp_path, monkeypatch, components):
    messages = []
    monkeypatch.setattr(
        schemas_module.console, "log", lambda *args, **kwargs: messages.append(" ".join(map(str, args)))
    )
    source = _generate(tmp_path, "issue_291_cycle", components)
    assert set(components) <= set(_definitions(source))
    assert any("cycle" in message.lower() for message in messages)
