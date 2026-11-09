"""
Regression tests for GitHub issue #276.

2.3.1 serialised request bodies with `model_dump(mode="json", exclude_unset=True)`, so a field
whose value came from its declared default was left out of the body. Discriminator fields such as
`action: Literal["add-user"] = "add-user"` disappeared and servers rejected the request with
`union_tag_not_found`.

Defaults are included again by default (as in 2.3.0). `BaseConfig.request_body_exclude_unset=True`
opts in to leaving out fields that weren't set, for PATCH-style partial updates.
"""

import json
import sys
import typing
from contextlib import contextmanager

import pydantic
import pytest
import respx
from cicerone import parse as cicerone_parse

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_spec

BASE_URL = "https://api.example.com"
CLIENT_NAME = "issue_276_client"


class Notification(pydantic.BaseModel):
    """The issue's repro: a plain defaulted field."""

    action: str = "add-user"
    message: str


class AddUser(pydantic.BaseModel):
    action: typing.Literal["add-user"] = "add-user"
    message: str


class RemoveUser(pydantic.BaseModel):
    action: typing.Literal["remove-user"] = "remove-user"
    message: str


class Patch(pydantic.BaseModel):
    """What #268 generates for a schema with no `required` list, plus an alias."""

    model_config = pydantic.ConfigDict(populate_by_name=True, serialize_by_alias=True)

    username: typing.Optional[str] = None
    is_active: bool = True
    display_name: typing.Optional[str] = pydantic.Field(default=None, alias="display-name")


# (exclude_unset, expected body for Notification(message="hi"))
MODES = [
    pytest.param(False, {"action": "add-user", "message": "hi"}, id="default"),
    pytest.param(True, {"message": "hi"}, id="exclude_unset"),
]


# A plain dict passed as `data`, which `_prepare_body` validates into the annotated model.
DICT_BODY: dict[str, typing.Any] = {"data": {"message": "hi"}}


def _make_client(exclude_unset: bool | None) -> api_client.APIClient:
    if exclude_unset is None:
        return api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL))
    return api_client.APIClient(
        config=api_config.BaseConfig(base_url=BASE_URL, request_body_exclude_unset=exclude_unset)
    )


def _body(route: respx.Route) -> typing.Any:
    return json.loads(route.calls.last.request.content)


def test_default_config_includes_defaults():
    assert api_config.BaseConfig().request_body_exclude_unset is False
    assert api_config.get_default_config(BASE_URL).request_body_exclude_unset is False


def test_flag_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("REQUEST_BODY_EXCLUDE_UNSET", "true")
    assert api_config.BaseConfig().request_body_exclude_unset is True


# _prepare_data_payload (request / arequest)


@pytest.mark.parametrize("exclude_unset, expected", MODES)
def test_prepare_data_payload(exclude_unset, expected):
    client = _make_client(exclude_unset)
    assert client._prepare_data_payload(Notification(message="hi")) == expected


def test_prepare_data_payload_issue_repro_uses_default_config():
    # The exact repro from the issue: a client built without a config.
    client = api_client.APIClient(base_url="http://localhost")
    assert client._prepare_data_payload(Notification(message="hi")) == {"action": "add-user", "message": "hi"}


@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_request_sync(exclude_unset, expected, httpx2_mock: respx.Router):
    route = httpx2_mock.post("/notify").respond(json={})
    _make_client(exclude_unset).request("POST", "/notify", response_map={200: dict}, data=Notification(message="hi"))
    assert _body(route) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_request_async(exclude_unset, expected, httpx2_mock: respx.Router):
    route = httpx2_mock.post("/notify").respond(json={})
    client = _make_client(exclude_unset)
    await client.arequest("POST", "/notify", response_map={200: dict}, data=Notification(message="hi"))
    await client.aclose()
    assert _body(route) == expected


# _prepare_body: a model instance passed as `data` (single model, and a union annotation)


@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorated_model_instance_sync(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    def notify(result: dict, data: Notification) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    notify(data=Notification(message="hi"))
    assert _body(route) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_decorated_model_instance_async(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    async def notify(result: dict, data: Notification) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    await notify(data=Notification(message="hi"))
    await client.aclose()
    assert _body(route) == expected


@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorated_union_annotation_sync(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    def notify(
        result: dict, data: typing.Annotated[AddUser | RemoveUser, pydantic.Field(discriminator="action")]
    ) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    notify(data=AddUser(message="hi"))
    assert _body(route) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_decorated_union_annotation_async(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    async def notify(result: dict, data: AddUser | RemoveUser) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    await notify(data=AddUser(message="hi"))
    await client.aclose()
    assert _body(route) == expected


# _prepare_body: a dict passed as `data`, validated into the annotated model (`model_instance`)


@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorated_dict_validated_into_model_sync(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    def notify(result: dict, data: Notification) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    notify(**DICT_BODY)
    assert _body(route) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("exclude_unset, expected", MODES)
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_decorated_dict_validated_into_model_async(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.post("/notify")
    async def notify(result: dict, data: Notification) -> dict:
        return result

    route = httpx2_mock.post("/notify").respond(json={})
    await notify(**DICT_BODY)
    await client.aclose()
    assert _body(route) == expected


# Explicit None and aliases (2.3.1's by-alias change) in both modes


@pytest.mark.parametrize(
    "exclude_unset, expected",
    [
        pytest.param(False, {"username": None, "is_active": True, "display-name": None}, id="default"),
        pytest.param(True, {"display-name": None}, id="exclude_unset"),
    ],
)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_explicit_none_is_sent_as_null_by_alias(exclude_unset, expected, httpx2_mock: respx.Router):
    client = _make_client(exclude_unset)

    @client.patch("/users/1")
    def update(result: dict, data: Patch) -> dict:
        return result

    route = httpx2_mock.patch("/users/1").respond(json={})
    update(data=Patch.model_validate({"display_name": None}))
    assert _body(route) == expected


@pytest.mark.parametrize(
    "exclude_unset, expected",
    [
        pytest.param(False, {"username": "ada", "is_active": True, "display-name": "Ada"}, id="default"),
        pytest.param(True, {"username": "ada", "display-name": "Ada"}, id="exclude_unset"),
    ],
)
def test_aliases_in_both_modes(exclude_unset, expected):
    client = _make_client(exclude_unset)
    # Set by field name and by alias: both are serialised under the alias.
    assert client._prepare_data_payload(Patch.model_validate({"username": "ada", "display_name": "Ada"})) == expected
    assert client._prepare_data_payload(Patch.model_validate({"username": "ada", "display-name": "Ada"})) == expected


# A discriminated-union body in a client generated from a spec, as the CLI does

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 276", "version": "0.1.0"},
    "servers": [{"url": BASE_URL}],
    "paths": {
        "/notify": {
            "post": {
                "operationId": "notify",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Notification"}}},
                },
                "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": {}}}}},
            }
        }
    },
    "components": {
        "schemas": {
            # Shape from the issue
            "Notification": {
                "oneOf": [
                    {"$ref": "#/components/schemas/NotificationAddUser"},
                    {"$ref": "#/components/schemas/NotificationRemoveUser"},
                ],
                "discriminator": {"propertyName": "action"},
            },
            "NotificationAddUser": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add-user"], "default": "add-user"},
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
            "NotificationRemoveUser": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["remove-user"], "default": "remove-user"},
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
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
    spec_path = tmp_path / "issue_276.json"
    spec_path.write_text(json.dumps(SPEC))
    APIGenerator(
        spec=cicerone_parse.parse_spec_from_dict(normalize_openapi_31_spec(SPEC)),
        output_dir=str(tmp_path / CLIENT_NAME),
        asyncio=False,
        regen=True,
        url=None,
        file=str(spec_path),
    ).generate()
    with _import_generated(tmp_path):
        from issue_276_client import client, config, schemas  # type: ignore

        yield client, config, schemas


def test_generated_discriminator_is_literal_with_default(generated):
    _, _, schemas = generated
    assert schemas.NotificationAddUser.model_fields["action"].default == "add-user"
    assert typing.get_args(schemas.NotificationAddUser.model_fields["action"].annotation) == ("add-user",)


@pytest.mark.parametrize(
    "exclude_unset, expected",
    [
        pytest.param(None, {"action": "add-user", "message": "hi"}, id="default"),
        pytest.param(True, {"message": "hi"}, id="exclude_unset"),
    ],
)
@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_sends_discriminator(generated, exclude_unset, expected, httpx2_mock: respx.Router):
    client, config, schemas = generated
    if exclude_unset is not None:
        client.client.configure(config=config.Config(request_body_exclude_unset=exclude_unset))

    route = httpx2_mock.post("/notify").respond(json={})
    client.notify(data=schemas.NotificationAddUser(message="hi"))

    body = _body(route)
    assert body == expected
    if exclude_unset is None:
        # What the server does with it: the tag selects the right member.
        adapter = pydantic.TypeAdapter(schemas.Notification)
        assert isinstance(adapter.validate_python(body), schemas.NotificationAddUser)
