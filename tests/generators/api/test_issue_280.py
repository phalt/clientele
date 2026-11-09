"""
Regression tests for GitHub issue #280.

`utils.get_type` only used `format` for numbers (`decimal`), so strings with
`format: uuid`, `date-time` or `date` (what FastAPI/pydantic emit for `uuid.UUID`,
`datetime.datetime` and `datetime.date`) were generated as `str`. Callers lost
pydantic's validation and had to parse the values themselves.
"""

import datetime
import json
import sys
import uuid
from contextlib import contextmanager

import pydantic
import pytest
import respx
from cicerone import parse as cicerone_parse

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.generators.api.generator import APIGenerator
from clientele.generators.cicerone_compat import normalize_openapi_31_spec
from clientele.generators.shared import utils

CLIENT_NAME = "issue_280_client"
BASE_URL = "https://api.example.com"

SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Issue 280", "version": "0.1.0"},
    "servers": [{"url": BASE_URL}],
    "paths": {
        "/events/{event_id}": {
            "get": {
                "operationId": "get_event",
                "parameters": [
                    {
                        "name": "event_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                    },
                    {"name": "on", "in": "query", "required": True, "schema": {"type": "string", "format": "date"}},
                    {
                        "name": "after",
                        "in": "query",
                        "required": False,
                        "schema": {"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]},
                    },
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Event"}}},
                    }
                },
            }
        }
    },
    "components": {
        "schemas": {
            # Repro from the issue
            "Event": {
                "type": "object",
                "required": ["id", "at", "on"],
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "at": {"type": "string", "format": "date-time"},
                    "on": {"type": "string", "format": "date"},
                },
            },
            "Formats": {
                "type": "object",
                "required": ["start", "length", "nullable_30", "nullable_31", "any_of_null", "unknown", "link"],
                "properties": {
                    "start": {"type": "string", "format": "time"},
                    "length": {"type": "string", "format": "duration"},
                    "nullable_30": {"type": "string", "format": "uuid", "nullable": True},
                    "nullable_31": {"type": ["string", "null"], "format": "date-time"},
                    "any_of_null": {"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]},
                    "unknown": {"type": "string", "format": "made-up"},
                    "link": {"type": "string", "format": "uri"},
                    "ids": {"type": "array", "items": {"type": "string", "format": "uuid"}},
                },
            },
        }
    },
}

EVENT_ID = "00000000-0000-0000-0000-000000000001"
EVENT_JSON = {"id": EVENT_ID, "at": "2026-01-02T03:04:05Z", "on": "2026-01-02"}


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
    spec_path = tmp_path / "issue_280.json"
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
def schemas_source(generated):
    return (generated / CLIENT_NAME / "schemas.py").read_text()


@pytest.fixture
def client_source(generated):
    return (generated / CLIENT_NAME / "client.py").read_text()


@pytest.fixture
def schemas(generated):
    with _import_generated(generated):
        from issue_280_client import schemas  # type: ignore

        yield schemas


@pytest.fixture
def client(generated):
    with _import_generated(generated):
        from issue_280_client import client  # type: ignore

        yield client


def test_string_formats_validate_to_python_types(schemas):
    event = schemas.Event.model_validate(EVENT_JSON)

    assert event.id == uuid.UUID(EVENT_ID)
    assert event.at == datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
    assert event.on == datetime.date(2026, 1, 2)


def test_string_formats_reject_malformed_values(schemas):
    with pytest.raises(pydantic.ValidationError):
        schemas.Event.model_validate({**EVENT_JSON, "id": "not-a-uuid"})
    with pytest.raises(pydantic.ValidationError):
        schemas.Event.model_validate({**EVENT_JSON, "on": "yesterday"})


def test_generated_schema_annotations(schemas_source):
    assert "id: uuid.UUID\n" in schemas_source
    assert "at: datetime.datetime\n" in schemas_source
    assert "on: datetime.date\n" in schemas_source
    assert "start: datetime.time\n" in schemas_source
    assert "length: datetime.timedelta\n" in schemas_source
    assert "nullable_30: typing.Optional[uuid.UUID] = None\n" in schemas_source
    assert "nullable_31: typing.Optional[datetime.datetime] = None\n" in schemas_source
    assert "any_of_null: datetime.date | None\n" in schemas_source
    assert "unknown: str\n" in schemas_source
    assert "link: str\n" in schemas_source
    assert "ids: typing.Optional[list[uuid.UUID]] = None\n" in schemas_source


def test_nullable_and_other_formats_validate(schemas):
    formats = schemas.Formats.model_validate(
        {
            "start": "03:04:05",
            "length": "P1DT2H",
            "nullable_30": None,
            "nullable_31": "2026-01-02T03:04:05+01:00",
            "any_of_null": "2026-01-02",
            "unknown": "anything",
            "link": "https://example.com",
        }
    )
    assert formats.start == datetime.time(3, 4, 5)
    assert formats.length == datetime.timedelta(days=1, hours=2)
    assert formats.nullable_30 is None
    assert isinstance(formats.nullable_31, datetime.datetime)
    assert formats.any_of_null == datetime.date(2026, 1, 2)
    assert formats.unknown == "anything"
    assert formats.link == "https://example.com"


def test_client_signature_uses_python_types(client_source):
    assert "event_id: uuid.UUID" in client_source
    assert "on: datetime.date" in client_source
    assert "after: typing.Optional[datetime.datetime] = None" in client_source


@pytest.mark.httpx2(base_url=BASE_URL)
def test_generated_client_serialises_formatted_parameters(client, httpx2_mock: respx.Router):
    route = httpx2_mock.get(f"/events/{EVENT_ID}").respond(json=EVENT_JSON)
    event = client.get_event(
        event_id=uuid.UUID(EVENT_ID),
        on=datetime.date(2026, 1, 2),
        after=datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc),
    )

    request = route.calls.last.request
    assert request.url.path == f"/events/{EVENT_ID}"
    assert request.url.params["on"] == "2026-01-02"
    # ISO 8601 with a `T`, not `str(datetime)`'s space separator
    assert request.url.params["after"] == "2026-01-02T03:04:05Z"
    assert event.on == datetime.date(2026, 1, 2)


@pytest.mark.httpx2(base_url=BASE_URL)
def test_api_client_serialises_path_and_query_values(httpx2_mock: respx.Router):
    app = api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL))

    @app.get("/at/{at}")
    def get_at(result: dict, at: datetime.datetime, length: datetime.timedelta, ids: list[uuid.UUID]) -> dict:
        return result

    at = datetime.datetime(2026, 1, 2, 3, 4, 5)
    route = httpx2_mock.get("/at/2026-01-02T03:04:05").respond(json={})
    get_at(at=at, length=datetime.timedelta(days=1), ids=[uuid.UUID(EVENT_ID)])

    params = route.calls.last.request.url.params
    assert params["length"] == "P1D"
    assert params.get_list("ids") == [EVENT_ID]


@pytest.mark.parametrize(
    "schema, expected",
    [
        ({"type": "string", "format": "uuid"}, "uuid.UUID"),
        ({"type": "string", "format": "date-time"}, "datetime.datetime"),
        ({"type": "string", "format": "date"}, "datetime.date"),
        ({"type": "string", "format": "time"}, "datetime.time"),
        ({"type": "string", "format": "duration"}, "datetime.timedelta"),
        ({"type": "string", "format": "uuid", "nullable": True}, "typing.Optional[uuid.UUID]"),
        ({"type": "array", "items": {"type": "string", "format": "date"}}, "list[datetime.date]"),
        # Unknown and unmapped formats stay `str`
        ({"type": "string", "format": "uri"}, "str"),
        ({"type": "string", "format": "email"}, "str"),
        ({"type": "string", "format": "made-up"}, "str"),
        ({"type": "string"}, "str"),
        # An enum is a Literal of its values regardless of `format`
        ({"type": "string", "format": "date", "enum": ["2026-01-02"]}, "typing.Literal['2026-01-02']"),
    ],
)
def test_get_type_string_formats(schema, expected):
    assert utils.get_type(schema) == expected


@pytest.mark.parametrize(
    "schema, expected",
    [
        ({"type": ["string", "null"], "format": "uuid"}, "typing.Optional[uuid.UUID]"),
        ({"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]}, "datetime.datetime | None"),
    ],
)
def test_get_type_string_formats_openapi_31_nullable(schema, expected):
    """OpenAPI 3.1 nullable forms, normalised the way the CLI does."""
    spec = normalize_openapi_31_spec({"openapi": "3.1.0", "components": {"schemas": {"S": schema}}})
    assert utils.get_type(spec["components"]["schemas"]["S"]) == expected
