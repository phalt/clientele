"""Tests for the niquests HTTP backend."""

import pytest

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import niquests_backend

BASE_URL = "https://api.example.com"


class TestNiquestsHTTPBackendSync:
    def test_build_client_returns_session(self):
        import niquests

        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        session = backend.build_client()
        assert isinstance(session, niquests.Session)
        backend.close()

    def test_build_client_reuse(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_client()
        s2 = backend.build_client()
        assert s1 is s2
        backend.close()

    def test_close_clears_client(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        backend.build_client()
        assert backend._sync_client is not None
        backend.close()
        assert backend._sync_client is None

    def test_close_is_idempotent(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        backend.close()
        backend.close()

    def test_from_config(self):
        config = api_config.BaseConfig(
            base_url=BASE_URL,
            headers={"X-API-Key": "secret"},
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        )
        backend = niquests_backend.NiquestsHTTPBackend.from_config(config)
        assert backend.base_url == BASE_URL
        assert backend.headers == {"X-API-Key": "secret"}
        assert backend.timeout == 30.0
        assert backend.follow_redirects is True
        assert backend.verify is False

    def test_full_url_strips_double_slash(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"

    def test_full_url_absolute_unchanged(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        assert backend._full_url("https://other.example.com/path") == "https://other.example.com/path"

    def test_send_sync_request(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("GET", "/users/1")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}
        assert result.request_method == "GET"
        assert result.request_url == f"{httpserver.url_for('').rstrip('/')}/users/1"

    def test_send_sync_request_post_with_json(self, httpserver):
        httpserver.expect_request("/items", method="POST").respond_with_json({"id": 99}, status=201)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("POST", "/items", json={"name": "foo"})
        backend.close()

        assert result.status_code == 201

    def test_send_sync_request_passes_default_headers(self, httpserver):
        httpserver.expect_request(
            "/me",
            headers={"Authorization": "Bearer token"},
        ).respond_with_json({}, status=200)

        backend = niquests_backend.NiquestsHTTPBackend(
            base_url=httpserver.url_for(""),
            headers={"Authorization": "Bearer token"},
        )
        backend.send_sync_request("GET", "/me")
        backend.close()

    def test_handle_sync_stream_yields_lines(self, httpserver):
        httpserver.expect_request("/stream").respond_with_data(
            "line one\nline two\nline three\n",
            content_type="text/plain; charset=utf-8",
        )

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        results = list(backend.handle_sync_stream("GET", "/stream", str, response_parser=lambda x: x))
        backend.close()

        assert results == ["line one", "line two", "line three"]

    def test_handle_sync_stream_error_raises(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        with pytest.raises(api_exceptions.HTTPStatusError):
            list(backend.handle_sync_stream("GET", "/missing", str))
        backend.close()

    def test_full_clientele_integration(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        config = api_config.BaseConfig(base_url=base_url, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        def get_user(result: dict, user_id: int) -> dict:
            return result

        result = get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        client.close()

    def test_convert_to_response_from_real_response(self, httpserver):
        httpserver.expect_request("/ping").respond_with_json({"ok": True})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = backend.send_sync_request("GET", "/ping")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"ok": True}
        assert result.request_method == "GET"


class TestNiquestsHTTPBackendAsync:
    def test_build_async_client_returns_async_session(self):
        import niquests

        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        session = backend.build_async_client()
        assert isinstance(session, niquests.AsyncSession)

    def test_build_async_client_reuse(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_async_client()
        s2 = backend.build_async_client()
        assert s1 is s2

    @pytest.mark.asyncio
    async def test_aclose_clears_client(self, httpserver):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        backend.build_async_client()
        assert backend._async_client is not None
        await backend.aclose()
        assert backend._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_is_idempotent(self):
        backend = niquests_backend.NiquestsHTTPBackend(base_url=BASE_URL)
        await backend.aclose()
        await backend.aclose()

    @pytest.mark.asyncio
    async def test_send_async_request(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = await backend.send_async_request("GET", "/users/1")
        await backend.aclose()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_send_async_request_post(self, httpserver):
        httpserver.expect_request("/items", method="POST").respond_with_json({"id": 99}, status=201)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        result = await backend.send_async_request("POST", "/items", json={"name": "foo"})
        await backend.aclose()

        assert result.status_code == 201

    @pytest.mark.asyncio
    async def test_handle_async_stream_yields_lines(self, httpserver):
        httpserver.expect_request("/stream").respond_with_data(
            "line one\nline two\nline three\n",
            content_type="text/plain; charset=utf-8",
        )

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        results = []
        async for item in backend.handle_async_stream("GET", "/stream", str, response_parser=lambda x: x):
            results.append(item)
        await backend.aclose()

        assert results == ["line one", "line two", "line three"]

    @pytest.mark.asyncio
    async def test_full_clientele_integration(self, httpserver):
        httpserver.expect_request("/users/1").respond_with_json({"id": 1, "name": "Alice"})

        base_url = httpserver.url_for("").rstrip("/")
        backend = niquests_backend.NiquestsHTTPBackend(base_url=base_url)
        config = api_config.BaseConfig(base_url=base_url, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        async def get_user(result: dict, user_id: int) -> dict:
            return result

        result = await get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        await client.aclose()

    @pytest.mark.asyncio
    async def test_handle_async_stream_error_raises(self, httpserver):
        httpserver.expect_request("/missing").respond_with_json({"error": "not found"}, status=404)

        backend = niquests_backend.NiquestsHTTPBackend(base_url=httpserver.url_for(""))
        with pytest.raises(api_exceptions.HTTPStatusError):
            async for _ in backend.handle_async_stream("GET", "/missing", str):
                pass
        await backend.aclose()
