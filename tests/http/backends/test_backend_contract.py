"""The HTTPBackend stream contract: open_sync_stream / open_async_stream are required."""

from __future__ import annotations

import typing

import pytest

from clientele.http import backends, response


class _AllButStreams(backends.HTTPBackend):
    """Implements every abstract member except the two stream methods."""

    def build_client(self) -> None:
        return None

    def build_async_client(self) -> None:
        return None

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        return native_response

    def send_sync_request(self, method: str, url: str, **kwargs: typing.Any) -> response.Response:
        raise NotImplementedError

    async def send_async_request(self, method: str, url: str, **kwargs: typing.Any) -> response.Response:
        raise NotImplementedError

    def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass


class _OnlySyncStream(_AllButStreams):
    def open_sync_stream(self, method: str, url: str, **kwargs: typing.Any) -> typing.Any:
        raise NotImplementedError


class _OnlyAsyncStream(_AllButStreams):
    def open_async_stream(self, method: str, url: str, **kwargs: typing.Any) -> typing.Any:
        raise NotImplementedError


class _BothStreams(_OnlySyncStream, _OnlyAsyncStream):
    pass


@pytest.mark.parametrize(
    ("backend_class", "missing"),
    [
        (_AllButStreams, "open_async_stream, open_sync_stream"),
        (_OnlySyncStream, "open_async_stream"),
        (_OnlyAsyncStream, "open_sync_stream"),
    ],
)
def test_backend_without_stream_methods_cannot_be_instantiated(backend_class: type, missing: str) -> None:
    with pytest.raises(TypeError, match="abstract") as exc_info:
        backend_class()
    for name in missing.split(", "):
        assert name in str(exc_info.value)


def test_backend_with_both_stream_methods_can_be_instantiated() -> None:
    assert isinstance(_BothStreams(), backends.HTTPBackend)


def test_legacy_line_methods_are_gone() -> None:
    assert not hasattr(backends.HTTPBackend, "handle_sync_stream")
    assert not hasattr(backends.HTTPBackend, "handle_async_stream")


def test_every_builtin_backend_implements_the_contract() -> None:
    from clientele.http import aiohttp_backend, fake_backend, httpx_backend, niquests_backend, requests_backend

    for backend in (
        httpx_backend.HttpxHTTPBackend(),
        fake_backend.FakeHTTPBackend(),
        requests_backend.RequestsHTTPBackend(),
        niquests_backend.NiquestsHTTPBackend(),
        aiohttp_backend.AiohttpHTTPBackend(),
    ):
        assert not getattr(type(backend), "__abstractmethods__", None), type(backend).__name__
