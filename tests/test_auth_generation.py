"""
Tests for authentication config generation from OpenAPI securitySchemes.

Most real-world APIs declare their authentication in
components.securitySchemes, but the generator previously ignored that
section entirely - every user had to hand-edit config.py following the
docs. The generator now reads the supported schemes and produces typed
credential fields on the generated Config that inject the right headers.

Expected behaviour:
  - http/bearer  -> `bearer_token` field; sets `Authorization: Bearer <token>`
  - http/basic   -> `basic_username`/`basic_password` fields; sets
                    `Authorization: Basic <base64>`
  - apiKey in header -> `api_key` field; sets the named header
  - oauth2, openIdConnect, apiKey in query/cookie -> not auto-generated;
    a comment in config.py points the user at manual configuration
  - credentials are only injected when set, and never override headers
    the user provided explicitly
  - fields are pydantic-settings fields, so environment variables work
    for free
"""

import base64
import importlib
import sys
from contextlib import contextmanager

import pytest
from cicerone import parse as cicerone_parse

from clientele.generators.api.generator import APIGenerator


@contextmanager
def _import_generated_config(tmp_path):
    sys.path.insert(0, str(tmp_path))
    try:
        yield importlib.import_module("config")
    finally:
        sys.path.remove(str(tmp_path))
        for mod in list(sys.modules):
            if mod in ("schemas", "client", "config"):
                del sys.modules[mod]


def _generate(tmp_path, security_schemes):
    spec_dict = {
        "openapi": "3.0.2",
        "info": {"title": "Auth Test API", "version": "1.0.0"},
        "servers": [{"url": "http://localhost"}],
        "paths": {
            "/ping": {
                "get": {
                    "operationId": "ping",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "title": "PingResponse",
                                        "properties": {"ok": {"type": "boolean"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {"schemas": {}, "securitySchemes": security_schemes},
    }
    spec = cicerone_parse.parse_spec_from_dict(spec_dict)
    generator = APIGenerator(
        spec=spec,
        output_dir=str(tmp_path),
        asyncio=False,
        regen=True,
        url=None,
        file="openapi.json",
    )
    generator.generate()
    return tmp_path


class TestBearerScheme:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("bearer_client")
        return _generate(tmp_path, {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}})

    def test_config_has_bearer_token_field(self, generated):
        with _import_generated_config(generated) as config:
            assert config.Config().bearer_token == ""

    def test_bearer_token_is_injected_into_headers(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(bearer_token="my-secret")
            assert cfg.headers["Authorization"] == "Bearer my-secret"

    def test_empty_token_injects_nothing(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config()
            assert "Authorization" not in cfg.headers

    def test_explicit_authorization_header_is_not_overridden(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(bearer_token="my-secret", headers={"Authorization": "custom-scheme abc"})
            assert cfg.headers["Authorization"] == "custom-scheme abc"

    def test_bearer_token_from_environment(self, generated, monkeypatch):
        monkeypatch.setenv("BEARER_TOKEN", "from-the-env")
        with _import_generated_config(generated) as config:
            cfg = config.Config()
            assert cfg.headers["Authorization"] == "Bearer from-the-env"


class TestBasicScheme:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("basic_client")
        return _generate(tmp_path, {"basicAuth": {"type": "http", "scheme": "basic"}})

    def test_config_has_username_and_password_fields(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config()
            assert cfg.basic_username == ""
            assert cfg.basic_password == ""

    def test_credentials_injected_as_basic_auth_header(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(basic_username="user", basic_password="pass")
            expected = base64.b64encode(b"user:pass").decode()
            assert cfg.headers["Authorization"] == f"Basic {expected}"

    def test_no_credentials_injects_nothing(self, generated):
        with _import_generated_config(generated) as config:
            assert "Authorization" not in config.Config().headers


class TestApiKeyScheme:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("apikey_client")
        return _generate(tmp_path, {"apiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}})

    def test_config_has_api_key_field(self, generated):
        with _import_generated_config(generated) as config:
            assert config.Config().api_key == ""

    def test_api_key_injected_into_named_header(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(api_key="key-123")
            assert cfg.headers["X-API-Key"] == "key-123"

    def test_explicit_header_is_not_overridden(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(api_key="key-123", headers={"X-API-Key": "explicit"})
            assert cfg.headers["X-API-Key"] == "explicit"


class TestMultipleSchemes:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("multi_client")
        return _generate(
            tmp_path,
            {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
                "apiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            },
        )

    def test_both_credentials_can_be_configured_together(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config(bearer_token="tok", api_key="key")
            assert cfg.headers["Authorization"] == "Bearer tok"
            assert cfg.headers["X-API-Key"] == "key"


class TestUnsupportedSchemes:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("unsupported_client")
        return _generate(
            tmp_path,
            {
                "oauth": {
                    "type": "oauth2",
                    "flows": {"clientCredentials": {"tokenUrl": "https://example.com/token", "scopes": {}}},
                },
                "queryKey": {"type": "apiKey", "in": "query", "name": "api_key"},
            },
        )

    def test_generation_succeeds(self, generated):
        assert (generated / "config.py").exists()

    def test_config_mentions_unsupported_schemes(self, generated):
        config_content = (generated / "config.py").read_text()
        assert "oauth" in config_content
        assert "queryKey" in config_content

    def test_config_has_no_credential_fields(self, generated):
        with _import_generated_config(generated) as config:
            cfg = config.Config()
            assert not hasattr(cfg, "bearer_token")
            assert not hasattr(cfg, "api_key")


class TestEndToEndRequestHeaders:
    """The generated Config must put credentials on the actual request."""

    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("e2e_client")
        return _generate(tmp_path, {"bearerAuth": {"type": "http", "scheme": "bearer"}})

    def test_bearer_token_is_sent_on_requests(self, generated):
        from clientele.api import APIClient
        from clientele.http.fake_backend import FakeHTTPBackend

        with _import_generated_config(generated) as config:
            fake_backend = FakeHTTPBackend()
            cfg = config.Config(bearer_token="my-secret", http_backend=fake_backend)
            client = APIClient(config=cfg)
            client.request("GET", "/ping", response_map={200: dict})

            assert len(fake_backend.requests) == 1
            sent_headers = fake_backend.requests[0]["kwargs"]["headers"]
            assert sent_headers["Authorization"] == "Bearer my-secret"


class TestNoSecuritySchemes:
    @pytest.fixture(scope="class")
    def generated(self, tmp_path_factory):
        tmp_path = tmp_path_factory.mktemp("plain_client")
        return _generate(tmp_path, {})

    def test_config_has_no_auth_fields_or_hooks(self, generated):
        config_content = (generated / "config.py").read_text()
        assert "bearer_token" not in config_content
        assert "model_post_init" not in config_content

    def test_config_instantiates(self, generated):
        with _import_generated_config(generated) as config:
            assert config.Config().base_url == "http://localhost"
