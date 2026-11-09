"""
Regression tests for GitHub issue #279.

The generator formatted its output by running whichever `ruff` was first on
`PATH`. When the venv wasn't activated (e.g. `.venv/bin/python -m clientele.cli`)
ruff wasn't found, formatting was silently skipped, and the same spec produced
different code depending on how the generator was launched.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from cicerone import parse as cicerone_parse

from clientele.generators.api import generator as api_generator

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 279", "version": "0.1.0"},
    "paths": {
        "/things": {
            "get": {
                "operationId": "get_things",
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
                "properties": {"note": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
            }
        }
    },
}


def _generate_in_subprocess(tmp_path: Path, path_env: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    spec_path = tmp_path / "issue_279.json"
    spec_path.write_text(json.dumps(SPEC))
    output_dir = tmp_path / "issue_279_client"
    subprocess.run(
        [sys.executable, "-m", "clientele.cli", "start-api", "-f", str(spec_path), "-o", str(output_dir), "--regen"],
        check=True,
        capture_output=True,
        env={**os.environ, "PATH": path_env},
    )
    return output_dir


def test_output_is_formatted_when_ruff_is_not_on_path(tmp_path):
    # The venv's bin dir holds the ruff installed with clientele[cli].
    venv_bin = str(Path(sys.executable).parent)
    with_ruff = _generate_in_subprocess(tmp_path / "with_ruff", venv_bin + os.pathsep + "/usr/bin:/bin")
    # The interpreter is still run by its full path, but no ruff script is on PATH.
    without_ruff = _generate_in_subprocess(tmp_path / "without_ruff", "/usr/bin:/bin")

    for name in ("schemas.py", "client.py", "config.py"):
        assert (without_ruff / name).read_text() == (with_ruff / name).read_text(), name


def test_find_ruff_bin_prefers_the_installed_ruff_package():
    with (
        mock.patch("ruff.find_ruff_bin", return_value="/venv/bin/ruff"),
        mock.patch("shutil.which", return_value="/somewhere/else/ruff") as which,
    ):
        assert api_generator.find_ruff_bin() == "/venv/bin/ruff"
    which.assert_not_called()


def test_find_ruff_bin_falls_back_to_path():
    with (
        mock.patch("ruff.find_ruff_bin", side_effect=FileNotFoundError),
        mock.patch("shutil.which", return_value="/usr/local/bin/ruff"),
    ):
        assert api_generator.find_ruff_bin() == "/usr/local/bin/ruff"


def test_find_ruff_bin_falls_back_to_path_when_ruff_is_not_importable():
    with (
        mock.patch.dict(sys.modules, {"ruff": None}),
        mock.patch("shutil.which", return_value="/usr/local/bin/ruff"),
    ):
        assert api_generator.find_ruff_bin() == "/usr/local/bin/ruff"


def test_find_ruff_bin_returns_none_when_ruff_is_unavailable():
    with (
        mock.patch("ruff.find_ruff_bin", side_effect=FileNotFoundError),
        mock.patch("shutil.which", return_value=None),
    ):
        assert api_generator.find_ruff_bin() is None


def test_format_client_warns_and_skips_when_ruff_is_unavailable(tmp_path):
    spec_path = tmp_path / "issue_279.json"
    spec_path.write_text(json.dumps(SPEC))
    output_dir = tmp_path / "issue_279_client"
    generator = api_generator.APIGenerator(
        spec=cicerone_parse.parse_spec_from_file(str(spec_path)),
        output_dir=str(output_dir),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    )
    with (
        mock.patch.object(api_generator, "find_ruff_bin", return_value=None),
        mock.patch("subprocess.run") as run,
        mock.patch.object(api_generator.console, "log") as log,
    ):
        generator.generate()

    run.assert_not_called()
    assert any("Ruff not found" in str(call.args[0]) for call in log.call_args_list)
    assert (output_dir / "client.py").exists()


def test_format_client_runs_the_resolved_ruff_binary(tmp_path):
    spec_path = tmp_path / "issue_279.json"
    spec_path.write_text(json.dumps(SPEC))
    output_dir = tmp_path / "issue_279_client"
    generator = api_generator.APIGenerator(
        spec=cicerone_parse.parse_spec_from_file(str(spec_path)),
        output_dir=str(output_dir),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    )
    with (
        mock.patch.object(api_generator, "find_ruff_bin", return_value="/venv/bin/ruff"),
        mock.patch("subprocess.run") as run,
    ):
        generator.generate()

    commands = [call.args[0] for call in run.call_args_list]
    assert [cmd[:2] for cmd in commands] == [["/venv/bin/ruff", "format"], ["/venv/bin/ruff", "check"]]
