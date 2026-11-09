"""
Regression tests for GitHub issue #282.

Generated models always subclassed `pydantic.BaseModel`, so an app-wide `model_config`
(`extra="forbid"`, `frozen=True`, an `alias_generator`, ...) meant rewriting `schemas.py`
after every regeneration. `start-api --base-class my_pkg.models.Base` now makes the generated
models subclass that class instead. Enums and `ListResponse` models are unchanged.
"""

import enum
import importlib
import json
import pathlib
import sys
import textwrap

import pydantic
import pytest
from click.testing import CliRunner

from clientele import cli
from clientele.schemas import ListResponse

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 282", "version": "0.1.0"},
    "paths": {
        "/things": {
            "get": {
                "operationId": "get_things",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Things"}}},
                    }
                },
            },
            "post": {
                "operationId": "create_thing",
                "requestBody": {
                    "content": {
                        "application/json": {
                            # Inline input class, generated while generating paths
                            "schema": {"type": "object", "properties": {"n": {"type": "integer"}}}
                        }
                    }
                },
                "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {}}}}},
            },
        }
    },
    "components": {
        "schemas": {
            "Thing": {
                "type": "object",
                "properties": {"n": {"type": "integer"}, "colour": {"$ref": "#/components/schemas/Colour"}},
                "required": ["n"],
            },
            "Aliased": {
                "type": "object",
                "properties": {"camelCase": {"type": "string"}},
                "required": ["camelCase"],
            },
            "Child": {"allOf": [{"$ref": "#/components/schemas/Thing"}]},
            "Colour": {"type": "string", "enum": ["red", "green"]},
            "Things": {"type": "array", "items": {"$ref": "#/components/schemas/Thing"}},
        }
    },
}

BASE_MODULE = """
import pydantic


class Base(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)
"""


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    package = tmp_path / "my_pkg"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "models.py").write_text(textwrap.dedent(BASE_MODULE))
    (tmp_path / "spec.json").write_text(json.dumps(SPEC))
    monkeypatch.syspath_prepend(str(tmp_path))
    yield tmp_path
    for mod in list(sys.modules):
        if mod.split(".")[0] in {"my_pkg", "issue_282_client"}:
            del sys.modules[mod]


def generate(workdir, *args: str, name: str = "issue_282_client"):
    return CliRunner().invoke(
        cli.cli_group,
        ["start-api", "-f", str(workdir / "spec.json"), "-o", str(workdir / name), "--regen", *args],
    )


def load_schemas(name: str = "issue_282_client"):
    return importlib.import_module(f"{name}.schemas")


def test_models_subclass_the_base_class(workdir):
    result = generate(workdir, "--base-class", "my_pkg.models.Base")
    assert result.exit_code == 0, result.output

    schemas = load_schemas()
    from my_pkg.models import Base  # type: ignore

    for model in (schemas.Thing, schemas.Aliased, schemas.Child, schemas.CreateThingApplicationJson):
        assert model.__mro__[1] is Base

    # The base's model_config applies
    with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
        schemas.Thing.model_validate({"n": 1, "unexpected": True})
    thing = schemas.Thing(n=1)
    with pytest.raises(pydantic.ValidationError, match="frozen_instance"):
        thing.n = 2


def test_enums_and_list_responses_do_not_use_the_base_class(workdir):
    assert generate(workdir, "--base-class", "my_pkg.models.Base").exit_code == 0

    schemas = load_schemas()
    from my_pkg.models import Base  # type: ignore

    assert schemas.Colour.__mro__[1:3] == (str, enum.Enum)
    assert not issubclass(schemas.Things, Base)
    assert issubclass(schemas.Things, ListResponse)
    things = schemas.Things.model_validate([{"n": 1, "colour": "red"}])
    assert isinstance(things[0], schemas.Thing)
    assert things[0].colour is schemas.Colour.RED


def test_aliased_models_still_serialize_by_alias(workdir):
    assert generate(workdir, "--base-class", "my_pkg.models.Base").exit_code == 0

    schemas = load_schemas()

    # The generated model_config is merged over the base's: populate_by_name and
    # serialize_by_alias come from the model, extra and frozen from the base
    aliased = schemas.Aliased(camel_case="x")
    assert aliased.model_dump() == {"camelCase": "x"}
    assert schemas.Aliased.model_validate({"camelCase": "y"}).camel_case == "y"
    assert schemas.Aliased.model_config["extra"] == "forbid"
    with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
        schemas.Aliased.model_validate({"camelCase": "y", "other": 1})


def test_base_class_is_imported_under_a_private_name(workdir):
    # A component called `Base` must not clash with the imported base class
    spec = json.loads((workdir / "spec.json").read_text())
    spec["components"]["schemas"]["Base"] = {"type": "object", "properties": {"x": {"type": "integer"}}}
    (workdir / "spec.json").write_text(json.dumps(spec))
    assert generate(workdir, "--base-class", "my_pkg.models.Base").exit_code == 0

    source = (workdir / "issue_282_client" / "schemas.py").read_text()
    assert "from my_pkg.models import Base as _ClienteleBase" in source
    schemas = load_schemas()
    from my_pkg.models import Base  # type: ignore

    assert schemas.Base.__mro__[1] is Base
    assert schemas.Thing.__mro__[1] is Base


def test_base_class_is_kept_in_the_manifest_regen_command(workdir):
    assert generate(workdir, "--base-class", "my_pkg.models.Base").exit_code == 0
    manifest = (workdir / "issue_282_client" / "MANIFEST.md").read_text()
    assert "--base-class my_pkg.models.Base" in manifest


def test_without_the_option_output_is_unchanged(workdir):
    result = CliRunner().invoke(
        cli.cli_group,
        [
            "start-api",
            "-f",
            str(REPO_ROOT / "example_openapi_specs" / "best.json"),
            "-o",
            str(workdir / "best_client"),
            "--regen",
        ],
    )
    assert result.exit_code == 0, result.output
    generated = (workdir / "best_client" / "schemas.py").read_text()
    committed = (REPO_ROOT / "tests" / "api_clients" / "test_client" / "schemas.py").read_text()
    assert generated == committed
    assert "_ClienteleBase" not in generated


@pytest.mark.parametrize(
    "base_class",
    ["Base", "my_pkg.", ".Base", "my_pkg..Base", "my-pkg.Base", "my_pkg.models.Base()", "my_pkg.class"],
)
def test_invalid_base_class_is_a_cli_error(workdir, base_class):
    result = generate(workdir, "--base-class", base_class)
    assert result.exit_code != 0
    assert "--base-class" in result.output
    assert not (workdir / "issue_282_client").exists()
