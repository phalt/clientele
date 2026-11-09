"""
Regression tests for GitHub issue #281.

The generated `Config` subclassed `BaseConfig` without an `env_prefix`, so every generated
client read the same unprefixed variables (`BASE_URL`, `TIMEOUT`, ...) from the environment
and from `.env`. Two clients in one app shared them, and generic names collided with the
app's own settings. The generated `Config` now gets an `env_prefix` from the package name,
overridable with `start-api --env-prefix`.
"""

import importlib
import json
import sys

import pytest
from click.testing import CliRunner

from clientele import cli

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 281", "version": "0.1.0"},
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
    "components": {"schemas": {"Thing": {"type": "object", "properties": {}}}},
}

CONFIG_ENV_VARS = ["BASE_URL", "TIMEOUT", "HEADERS", "VERIFY", "HTTP2", "FOLLOW_REDIRECTS"]


@pytest.fixture(autouse=True)
def clean_env(tmp_path, monkeypatch):
    for name in CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    # Keep any .env in the repo out of these tests
    monkeypatch.chdir(tmp_path)


def generate(tmp_path, name: str, *args: str):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(SPEC))
    result = CliRunner().invoke(
        cli.cli_group, ["start-api", "-f", str(spec_path), "-o", str(tmp_path / name), "--regen", *args]
    )
    return result


def load_config(tmp_path, name: str):
    sys.path.insert(0, str(tmp_path))
    try:
        return importlib.import_module(f"{name}.config").Config
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod == name or mod.startswith(f"{name}."):
                del sys.modules[mod]


def config_source(tmp_path, name: str) -> str:
    return (tmp_path / name / "config.py").read_text()


def test_two_generated_clients_do_not_share_environment_variables(tmp_path, monkeypatch):
    assert generate(tmp_path, "billing_client").exit_code == 0
    assert generate(tmp_path, "search_client").exit_code == 0
    monkeypatch.setenv("BASE_URL", "https://billing.example.com")
    monkeypatch.setenv("TIMEOUT", "1")  # e.g. an unrelated app setting

    billing = load_config(tmp_path, "billing_client")()
    search = load_config(tmp_path, "search_client")()

    # Neither reads the unprefixed variables. (The issue's `search.base_url != billing.base_url`
    # can't hold here: both fall back to the same default base URL.)
    assert billing.base_url == "http://localhost"
    assert search.base_url == "http://localhost"
    assert billing.timeout == 5.0
    assert search.timeout == 5.0


def test_prefixed_variables_configure_only_their_client(tmp_path, monkeypatch):
    assert generate(tmp_path, "billing_client").exit_code == 0
    assert generate(tmp_path, "search_client").exit_code == 0
    monkeypatch.setenv("BILLING_CLIENT_BASE_URL", "https://billing.example.com")
    monkeypatch.setenv("BILLING_CLIENT_TIMEOUT", "1")

    billing = load_config(tmp_path, "billing_client")()
    search = load_config(tmp_path, "search_client")()

    assert billing.base_url == "https://billing.example.com"
    assert billing.timeout == 1.0
    assert search.base_url == "http://localhost"
    assert search.timeout == 5.0
    assert 'env_prefix="BILLING_CLIENT_"' in config_source(tmp_path, "billing_client")
    assert "export BILLING_CLIENT_BASE_URL=" in config_source(tmp_path, "billing_client")


def test_dot_env_is_prefixed_too(tmp_path):
    assert generate(tmp_path, "billing_client").exit_code == 0
    (tmp_path / ".env").write_text("BASE_URL=https://wrong.example.com\nBILLING_CLIENT_TIMEOUT=2\n")

    billing = load_config(tmp_path, "billing_client")()

    assert billing.base_url == "http://localhost"
    assert billing.timeout == 2.0


def test_prefix_is_derived_from_the_output_directory_name(tmp_path, monkeypatch):
    # Trailing slash, and characters that aren't valid in an environment variable name
    assert generate(tmp_path, "my-api.client/").exit_code == 0
    assert 'env_prefix="MY_API_CLIENT_"' in config_source(tmp_path, "my-api.client")


def test_env_prefix_option(tmp_path, monkeypatch):
    result = generate(tmp_path, "billing_client", "--env-prefix", "FOO_")
    assert result.exit_code == 0, result.output
    assert 'env_prefix="FOO_"' in config_source(tmp_path, "billing_client")
    assert "--env-prefix FOO_" in (tmp_path / "billing_client" / "MANIFEST.md").read_text()

    monkeypatch.setenv("FOO_BASE_URL", "https://foo.example.com")
    monkeypatch.setenv("BILLING_CLIENT_BASE_URL", "https://billing.example.com")
    assert load_config(tmp_path, "billing_client")().base_url == "https://foo.example.com"


def test_empty_env_prefix_reads_unprefixed_variables(tmp_path, monkeypatch):
    result = generate(tmp_path, "billing_client", "--env-prefix", "")
    assert result.exit_code == 0, result.output
    assert "env_prefix" not in config_source(tmp_path, "billing_client")
    assert "export BASE_URL=" in config_source(tmp_path, "billing_client")

    monkeypatch.setenv("BASE_URL", "https://unprefixed.example.com")
    assert load_config(tmp_path, "billing_client")().base_url == "https://unprefixed.example.com"


@pytest.mark.parametrize("prefix", ['FOO"', "FOO BAR_", "FOO-"])
def test_invalid_env_prefix_is_rejected(tmp_path, prefix):
    result = generate(tmp_path, "billing_client", "--env-prefix", prefix)
    assert result.exit_code != 0
    assert "--env-prefix" in result.output
    assert not (tmp_path / "billing_client").exists()


def test_existing_config_is_not_overwritten_on_regen(tmp_path):
    assert generate(tmp_path, "billing_client").exit_code == 0
    config_path = tmp_path / "billing_client" / "config.py"
    custom = config_path.read_text() + "\n\nMY_SETTING = 1\n"
    config_path.write_text(custom)

    assert generate(tmp_path, "billing_client", "--env-prefix", "OTHER_").exit_code == 0

    assert config_path.read_text() == custom
    assert "OTHER_" not in custom
