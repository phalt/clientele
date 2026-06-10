"""
Tests for per-call config overrides (issue #233).

Generated clients create one module-global APIClient, so every decorated
function is bound to a single configuration. Users integrating with
multi-tenant APIs (the same OpenAPI spec served by many hosts) could not
direct individual calls at different base URLs or credentials without
mutating global state, which is not thread-safe.

Decorated functions and the direct request methods now accept a reserved
`config` keyword argument, following the same pattern as the reserved
`query` and `headers` kwargs:

  - the call uses the override config's base_url, headers, logger, and
    HTTP backend instead of the client-wide config
  - the client-wide config is not touched, so concurrent calls with
    different overrides are safe
  - an override config without an http_backend gets one lazily, cached
    on the config itself so each tenant keeps its own connection pool
  - functions that declare their own `config` parameter keep it as a
    normal argument (the reserved kwarg is disabled, like `query`)
"""

import typing

import pydantic
import pytest

from clientele.api import APIClient, BaseConfig
from clientele.http.fake_backend import FakeHTTPBackend
from clientele.http.response import Response


class Pong(pydantic.BaseModel):
    ok: bool


def make_backend() -> FakeHTTPBackend:
    return FakeHTTPBackend(
        default_response=Response(
            status_code=200,
            content=b'{"ok": true}',
            headers={"content-type": "application/json"},
        )
    )


def make_config(tenant: str, backend: FakeHTTPBackend | None = None) -> BaseConfig:
    return BaseConfig(
        base_url=f"https://{tenant}.example.com",
        headers={"X-Tenant": tenant},
        http_backend=backend if backend is not None else make_backend(),
    )


@pytest.fixture
def client_setup():
    default_backend = make_backend()
    client = APIClient(config=make_config("default", default_backend))

    @client.get("/ping")
    def ping(result: Pong) -> Pong:
        return result

    return client, ping, default_backend


class TestDecoratedFunctionOverride:
    def test_default_config_used_without_override(self, client_setup):
        _, ping, default_backend = client_setup
        result = ping()
        assert result.ok is True
        assert len(default_backend.requests) == 1
        assert default_backend.requests[0]["kwargs"]["headers"]["X-Tenant"] == "default"

    def test_override_routes_to_its_own_backend_and_headers(self, client_setup):
        _, ping, default_backend = client_setup
        tenant_backend = make_backend()
        tenant_config = make_config("tenant-b", tenant_backend)

        result = ping(config=tenant_config)

        assert result.ok is True
        assert len(default_backend.requests) == 0
        assert len(tenant_backend.requests) == 1
        assert tenant_backend.requests[0]["kwargs"]["headers"]["X-Tenant"] == "tenant-b"

    def test_override_does_not_mutate_the_client_config(self, client_setup):
        client, ping, default_backend = client_setup
        tenant_config = make_config("tenant-b")

        ping(config=tenant_config)
        assert client.config.base_url == "https://default.example.com"

        # The next un-overridden call still uses the client-wide config
        ping()
        assert len(default_backend.requests) == 1
        assert default_backend.requests[0]["kwargs"]["headers"]["X-Tenant"] == "default"

    def test_two_tenants_interleaved(self, client_setup):
        _, ping, _ = client_setup
        backend_a = make_backend()
        backend_b = make_backend()
        config_a = make_config("tenant-a", backend_a)
        config_b = make_config("tenant-b", backend_b)

        ping(config=config_a)
        ping(config=config_b)
        ping(config=config_a)

        assert len(backend_a.requests) == 2
        assert len(backend_b.requests) == 1


class TestAsyncOverride:
    @pytest.mark.asyncio
    async def test_async_function_accepts_config_override(self):
        default_backend = make_backend()
        client = APIClient(config=make_config("default", default_backend))

        @client.get("/ping")
        async def ping(result: Pong) -> Pong:
            return result

        tenant_backend = make_backend()
        tenant_config = make_config("tenant-b", tenant_backend)

        result = await ping(config=tenant_config)  # type: ignore

        assert result.ok is True
        assert len(default_backend.requests) == 0
        assert len(tenant_backend.requests) == 1
        assert tenant_backend.requests[0]["kwargs"]["headers"]["X-Tenant"] == "tenant-b"


class TestDirectRequestOverride:
    def test_request_accepts_config_override(self, client_setup):
        client, _, default_backend = client_setup
        tenant_backend = make_backend()
        tenant_config = make_config("tenant-b", tenant_backend)

        result = client.request("GET", "/ping", response_map={200: Pong}, config=tenant_config)

        assert result.ok is True
        assert len(default_backend.requests) == 0
        assert len(tenant_backend.requests) == 1

    @pytest.mark.asyncio
    async def test_arequest_accepts_config_override(self, client_setup):
        client, _, default_backend = client_setup
        tenant_backend = make_backend()
        tenant_config = make_config("tenant-b", tenant_backend)

        result = await client.arequest("GET", "/ping", response_map={200: Pong}, config=tenant_config)

        assert result.ok is True
        assert len(default_backend.requests) == 0
        assert len(tenant_backend.requests) == 1


class TestStreamingOverride:
    def test_sync_stream_uses_override_backend_and_headers(self):
        class RecordingStreamBackend(FakeHTTPBackend):
            def __init__(self) -> None:
                super().__init__()
                self.stream_calls: list[dict] = []

            def handle_sync_stream(self, method, url, inner_type=None, response_parser=None, **kwargs):
                self.stream_calls.append({"method": method, "url": url, "kwargs": kwargs})
                return iter([])

        default_backend = RecordingStreamBackend()
        client = APIClient(config=make_config("default", default_backend))

        @client.get("/events", streaming_response=True)
        def stream_events(result: typing.Iterator[str]) -> typing.Iterator[str]:
            return result

        override_backend = RecordingStreamBackend()
        override_config = make_config("stream-tenant", override_backend)

        list(stream_events(config=override_config))  # type: ignore

        assert len(default_backend.stream_calls) == 0
        assert len(override_backend.stream_calls) == 1
        sent_headers = override_backend.stream_calls[0]["kwargs"]["headers"]
        assert sent_headers["X-Tenant"] == "stream-tenant"


class TestLazyBackendCreation:
    def test_override_without_backend_gets_one_lazily_and_caches_it(self, client_setup, monkeypatch):
        _, ping, _ = client_setup
        created: list[FakeHTTPBackend] = []

        def fake_from_config(config):
            backend = make_backend()
            created.append(backend)
            return backend

        from clientele.http import httpx_backend

        monkeypatch.setattr(httpx_backend.HttpxHTTPBackend, "from_config", staticmethod(fake_from_config))

        tenant_config = BaseConfig(base_url="https://tenant-b.example.com")
        assert tenant_config.http_backend is None

        ping(config=tenant_config)
        ping(config=tenant_config)

        # The backend was created once and cached on the override config,
        # so each tenant config keeps its own connection pool.
        assert len(created) == 1
        assert tenant_config.http_backend is created[0]
        assert len(created[0].requests) == 2


class TestReservedKwargCollision:
    def test_function_with_its_own_config_parameter_keeps_it(self, client_setup):
        client, _, default_backend = client_setup

        @client.get("/search")
        def search(result: Pong, config: str) -> Pong:
            return result

        result = search(config="just-a-query-param")

        # The declared parameter wins: it is treated as a normal argument
        # (here, a query parameter) and the client-wide config is used.
        assert result.ok is True
        assert len(default_backend.requests) == 1
        assert default_backend.requests[0]["kwargs"]["params"] == {"config": "just-a-query-param"}
