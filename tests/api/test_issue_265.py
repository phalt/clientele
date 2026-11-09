"""
Regression tests for GitHub issue #265 (runtime side).

`response_map` must accept `None` for a no-content status code such as 204, so
`response_map={204: None, 403: Err}` returns `None` on 204 and `Err` on 403 instead of
raising `APIException: Unexpected status code 204`. Codes missing from the map still raise.
"""

import typing

import pydantic
import pytest
import respx

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions

BASE_URL = "https://api.example.com"


class Err(pydantic.BaseModel):
    errors: list[str]


class ErrDict(typing.TypedDict):
    detail: str


RESPONSE_MAP: dict[int, typing.Any] = {204: None, 403: Err}


def _client() -> api_client.APIClient:
    return api_client.APIClient(config=api_config.BaseConfig(base_url=BASE_URL))


# Decorator, sync


@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorator_returns_none_on_204_and_model_on_403(httpx2_mock: respx.Router):
    app = _client()

    @app.delete("/uploads/{id}", response_map={204: None, 403: Err})
    def delete_upload(result: Err | None, id: str) -> Err | None:
        return result

    httpx2_mock.delete("/uploads/a").respond(204)
    assert delete_upload(id="a") is None

    httpx2_mock.delete("/uploads/b").respond(403, json={"errors": ["nope"]})
    assert delete_upload(id="b") == Err(errors=["nope"])


@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorator_with_optional_annotation_and_typeddict(httpx2_mock: respx.Router):
    app = _client()

    @app.delete("/uploads/{id}", response_map={204: None, 422: ErrDict})
    def delete_upload(result: typing.Optional[ErrDict], id: str) -> typing.Optional[ErrDict]:
        return result

    httpx2_mock.delete("/uploads/a").respond(204)
    assert delete_upload(id="a") is None

    httpx2_mock.delete("/uploads/b").respond(422, json={"detail": "bad"})
    assert delete_upload(id="b") == {"detail": "bad"}


@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorator_unknown_status_still_raises(httpx2_mock: respx.Router):
    app = _client()

    @app.delete("/uploads/{id}", response_map={204: None, 403: Err})
    def delete_upload(result: Err | None, id: str) -> Err | None:
        return result

    httpx2_mock.delete("/uploads/a").respond(500, json={"errors": []})
    with pytest.raises(api_exceptions.APIException) as excinfo:
        delete_upload(id="a")
    assert excinfo.value.reason.startswith("Unexpected status code 500")


@pytest.mark.httpx2(base_url=BASE_URL)
def test_decorator_only_204_without_response_map_still_works(httpx2_mock: respx.Router):
    app = _client()

    @app.post("/ping")
    def ping(result: None) -> None:
        return result

    httpx2_mock.post("/ping").respond(204)
    assert ping() is None


def test_none_in_response_map_requires_none_in_result_annotation():
    app = _client()

    with pytest.raises(ValueError, match="'None' for status code 204"):

        @app.delete("/uploads/{id}", response_map={204: None, 403: Err})
        def delete_upload(result: Err, id: str) -> Err:
            return result


# Decorator, async


@pytest.mark.asyncio
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_async_decorator_returns_none_on_204_and_model_on_403(httpx2_mock: respx.Router):
    app = _client()

    @app.delete("/uploads/{id}", response_map={204: None, 403: Err})
    async def delete_upload(result: Err | None, id: str) -> Err | None:
        return result

    httpx2_mock.delete("/uploads/a").respond(204)
    assert await delete_upload(id="a") is None

    httpx2_mock.delete("/uploads/b").respond(403, json={"errors": ["nope"]})
    assert await delete_upload(id="b") == Err(errors=["nope"])


@pytest.mark.asyncio
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_async_decorator_unknown_status_still_raises(httpx2_mock: respx.Router):
    app = _client()

    @app.delete("/uploads/{id}", response_map={204: None, 403: Err})
    async def delete_upload(result: Err | None, id: str) -> Err | None:
        return result

    httpx2_mock.delete("/uploads/a").respond(404)
    with pytest.raises(api_exceptions.APIException) as excinfo:
        await delete_upload(id="a")
    assert excinfo.value.reason.startswith("Unexpected status code 404")


# request / arequest


@pytest.mark.httpx2(base_url=BASE_URL)
def test_request_returns_none_on_204_and_model_on_403(httpx2_mock: respx.Router):
    app = _client()

    httpx2_mock.delete("/uploads/a").respond(204)
    assert app.request("DELETE", "/uploads/{id}", response_map={204: None, 403: Err}, id="a") is None

    httpx2_mock.delete("/uploads/b").respond(403, json={"errors": ["nope"]})
    assert app.request("DELETE", "/uploads/{id}", response_map=RESPONSE_MAP, id="b") == Err(errors=["nope"])

    httpx2_mock.delete("/uploads/c").respond(500)
    with pytest.raises(api_exceptions.APIException) as excinfo:
        app.request("DELETE", "/uploads/{id}", response_map=RESPONSE_MAP, id="c")
    assert excinfo.value.reason.startswith("Unexpected status code 500")


@pytest.mark.asyncio
@pytest.mark.httpx2(base_url=BASE_URL)
async def test_arequest_returns_none_on_204_and_model_on_403(httpx2_mock: respx.Router):
    app = _client()

    httpx2_mock.delete("/uploads/a").respond(204)
    assert await app.arequest("DELETE", "/uploads/{id}", response_map={204: None, 403: Err}, id="a") is None

    httpx2_mock.delete("/uploads/b").respond(403, json={"errors": ["nope"]})
    assert await app.arequest("DELETE", "/uploads/{id}", response_map=RESPONSE_MAP, id="b") == Err(errors=["nope"])

    httpx2_mock.delete("/uploads/c").respond(500)
    with pytest.raises(api_exceptions.APIException) as excinfo:
        await app.arequest("DELETE", "/uploads/{id}", response_map=RESPONSE_MAP, id="c")
    assert excinfo.value.reason.startswith("Unexpected status code 500")
