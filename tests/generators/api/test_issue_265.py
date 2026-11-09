"""
Regression tests for GitHub issue #265.

A DELETE that returns 204 (no body) on success and 403/422 (JSON) on error generated
`response_map={403: ..., 422: ...}` and a return type without `None`, so a successful call
raised `APIException: Unexpected status code 204`. A response given as a `$ref` to
`#/components/responses/...` was never dereferenced, so it looked like a no-content response
and was dropped as well (from a comment on the issue).
"""

import json
import sys
from contextlib import contextmanager

import pytest
import respx
from cicerone import parse as cicerone_parse

from clientele.api import exceptions as api_exceptions
from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_spec

CLIENT_NAME = "issue_265_client"
ASYNC_CLIENT_NAME = "issue_265_async_client"
BASE_URL = "https://api.example.com"

JSON_ERROR = {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorList"}}}

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 265", "version": "0.1.0"},
    "servers": [{"url": BASE_URL}],
    "paths": {
        # Repro from the issue: 204 on success, JSON on error
        "/uploads/{id}": {
            "delete": {
                "operationId": "delete_upload",
                "parameters": [{"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "204": {"description": "Deleted"},
                    "403": {"description": "Forbidden", "content": JSON_ERROR},
                    "422": {
                        "description": "Invalid",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/JsonErrorResponse"}}},
                    },
                },
            }
        },
        # Only 204: already worked, must keep working
        "/ping": {
            "post": {
                "operationId": "ping",
                "responses": {"204": {"description": "No content"}},
            }
        },
        # From the issue comment: a shared `components/responses` 429
        "/things": {
            "get": {
                "operationId": "get_thing",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}},
                    },
                    "429": {"$ref": "#/components/responses/RateLimited"},
                },
            }
        },
        # A no-content *error* code stays out of response_map, so it still raises
        "/things/{id}": {
            "delete": {
                "operationId": "delete_thing",
                "parameters": [{"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}},
                    },
                    "403": {"description": "Forbidden", "content": JSON_ERROR},
                    "404": {"description": "Not found"},
                },
            },
            # One content class plus 204: the map is now generated so 204 is accepted explicitly
            "put": {
                "operationId": "put_thing",
                "parameters": [{"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}},
                    },
                    "204": {"description": "Unchanged"},
                },
            },
        },
    },
    "components": {
        "schemas": {
            "ErrorList": {
                "type": "object",
                "required": ["errors"],
                "properties": {"errors": {"type": "array", "items": {"type": "string"}}},
            },
            "JsonErrorResponse": {
                "type": "object",
                "required": ["detail"],
                "properties": {"detail": {"type": "string"}},
            },
            "Thing": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            },
            "RateLimitError": {
                "type": "object",
                "required": ["retry_after"],
                "properties": {"retry_after": {"type": "integer"}},
            },
        },
        "responses": {
            "RateLimited": {
                "description": "Too many requests",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RateLimitError"}}},
            }
        },
    },
}


@contextmanager
def _import_generated(path, name):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))
        for mod in list(sys.modules):
            if mod.startswith(name):
                del sys.modules[mod]


def _generate(tmp_path, name, asyncio):
    spec_path = tmp_path / "issue_265.json"
    spec_path.write_text(json.dumps(SPEC))
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_dict(normalize_openapi_31_spec(json.loads(json.dumps(SPEC)))),
        output_dir=str(tmp_path / name),
        asyncio=asyncio,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()
    return tmp_path


@pytest.fixture
def generated(tmp_path):
    return _generate(tmp_path, CLIENT_NAME, asyncio=False)


@pytest.fixture
def async_generated(tmp_path):
    return _generate(tmp_path, ASYNC_CLIENT_NAME, asyncio=True)


@pytest.fixture
def client_source(generated):
    return (generated / CLIENT_NAME / "client.py").read_text()


@pytest.fixture
def client(generated):
    with _import_generated(generated, CLIENT_NAME):
        from issue_265_client import client  # type: ignore

        yield client


@pytest.fixture
def async_client(async_generated):
    with _import_generated(async_generated, ASYNC_CLIENT_NAME):
        from issue_265_async_client import client  # type: ignore

        yield client


# Generated source


def test_mixed_204_endpoint_keeps_204_in_response_map(client_source):
    assert "response_map={204: None, 403: schemas.ErrorList, 422: schemas.JsonErrorResponse}" in client_source


def test_mixed_204_endpoint_return_type_includes_none(client_source):
    expected = "schemas.ErrorList | schemas.JsonErrorResponse | None"
    assert f"result: {expected}," in client_source
    assert f"-> {expected}:" in client_source


def test_only_204_endpoint_is_unchanged(client_source):
    assert '@client.post("/ping")\ndef ping(result: None) -> None:' in client_source


def test_components_responses_ref_is_dereferenced(client_source):
    assert "response_map={200: schemas.Thing, 429: schemas.RateLimitError}" in client_source
    assert "-> schemas.RateLimitError | schemas.Thing:" in client_source


def test_no_content_error_code_is_not_mapped_to_none(client_source):
    assert "response_map={200: schemas.Thing, 403: schemas.ErrorList}" in client_source
    assert "-> schemas.ErrorList | schemas.Thing:" in client_source


def test_single_class_with_204_gets_response_map(client_source):
    assert "response_map={200: schemas.Thing, 204: None}" in client_source
    assert "-> schemas.Thing | None:" in client_source


# Generated client at runtime


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_returns_none_on_204(client, httpx2_mock: respx.Router):
    httpx2_mock.delete("/uploads/abc").respond(204)
    assert client.delete_upload(id="abc") is None


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_returns_error_model_on_403(client, httpx2_mock: respx.Router):
    httpx2_mock.delete("/uploads/abc").respond(403, json={"errors": ["nope"]})
    result = client.delete_upload(id="abc")
    assert type(result).__name__ == "ErrorList"
    assert result.errors == ["nope"]


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_unknown_status_still_raises(client, httpx2_mock: respx.Router):
    httpx2_mock.delete("/uploads/abc").respond(500, json={"detail": "boom"})
    with pytest.raises(api_exceptions.APIException) as excinfo:
        client.delete_upload(id="abc")
    assert excinfo.value.reason.startswith("Unexpected status code 500")


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_only_204_still_works(client, httpx2_mock: respx.Router):
    httpx2_mock.post("/ping").respond(204)
    assert client.ping() is None


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_parses_ref_response(client, httpx2_mock: respx.Router):
    httpx2_mock.get("/things").respond(429, json={"retry_after": 3})
    result = client.get_thing()
    assert type(result).__name__ == "RateLimitError"
    assert result.retry_after == 3


@pytest.mark.asyncio
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_generated_async_client_returns_none_on_204(async_client, httpx2_mock: respx.Router):
    httpx2_mock.delete("/uploads/abc").respond(204)
    assert await async_client.delete_upload(id="abc") is None


@pytest.mark.asyncio
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_generated_async_client_returns_error_model_on_422(async_client, httpx2_mock: respx.Router):
    httpx2_mock.delete("/uploads/abc").respond(422, json={"detail": "bad id"})
    result = await async_client.delete_upload(id="abc")
    assert type(result).__name__ == "JsonErrorResponse"
    assert result.detail == "bad id"
