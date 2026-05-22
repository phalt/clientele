"""Tests for the requests HTTP backend."""

import json

import pytest
import responses as responses_lib

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import requests_backend

BASE_URL = "https://api.example.com"


class TestRequestsHTTPBackend:
    def test_build_client_applies_headers_and_verify(self):
        backend = requests_backend.RequestsHTTPBackend(
            base_url=BASE_URL,
            headers={"Authorization": "Bearer token"},
            verify=False,
        )
        session = backend.build_client()
        assert "Authorization" in session.headers
        assert session.verify is False
        backend.close()

    def test_client_reuse(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        s1 = backend.build_client()
        s2 = backend.build_client()
        assert s1 is s2
        backend.close()

    def test_close_clears_client(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        backend.build_client()
        assert backend._sync_client is not None
        backend.close()
        assert backend._sync_client is None

    def test_close_is_idempotent(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        backend.close()
        backend.close()

    @pytest.mark.asyncio
    async def test_aclose_is_noop(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        await backend.aclose()

    def test_build_async_client_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            backend.build_async_client()

    @pytest.mark.asyncio
    async def test_send_async_request_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            await backend.send_async_request("GET", "/get")

    @pytest.mark.asyncio
    async def test_handle_async_stream_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(NotImplementedError):
            async for _ in backend.handle_async_stream("GET", "/stream", str):
                pass

    def test_from_config(self):
        config = api_config.BaseConfig(
            base_url=BASE_URL,
            headers={"X-API-Key": "secret"},
            timeout=30.0,
            follow_redirects=True,
            verify=False,
        )
        backend = requests_backend.RequestsHTTPBackend.from_config(config)
        assert backend.base_url == BASE_URL
        assert backend.headers == {"X-API-Key": "secret"}
        assert backend.timeout == 30.0
        assert backend.follow_redirects is True
        assert backend.verify is False

    def test_full_url_strips_double_slash(self):
        backend = requests_backend.RequestsHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"

    def test_full_url_absolute_unchanged(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        assert backend._full_url("https://other.example.com/path") == "https://other.example.com/path"

    @responses_lib.activate
    def test_send_sync_request(self):
        responses_lib.get(f"{BASE_URL}/users/1", json={"id": 1, "name": "Alice"}, status=200)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        result = backend.send_sync_request("GET", "/users/1")
        backend.close()

        assert result.status_code == 200
        assert result.json() == {"id": 1, "name": "Alice"}
        assert result.request_method == "GET"
        assert result.request_url == f"{BASE_URL}/users/1"

    @responses_lib.activate
    def test_send_sync_request_post_with_json(self):
        responses_lib.post(f"{BASE_URL}/items", json={"id": 99}, status=201)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        result = backend.send_sync_request("POST", "/items", json={"name": "foo"})
        backend.close()

        assert result.status_code == 201
        body = responses_lib.calls[0].request.body
        assert body is not None
        assert json.loads(body) == {"name": "foo"}

    @responses_lib.activate
    def test_send_sync_request_passes_default_headers(self):
        responses_lib.get(f"{BASE_URL}/me", json={}, status=200)

        backend = requests_backend.RequestsHTTPBackend(
            base_url=BASE_URL,
            headers={"Authorization": "Bearer token"},
        )
        backend.send_sync_request("GET", "/me")
        backend.close()

        sent = responses_lib.calls[0].request
        assert sent.headers is not None
        assert "Bearer token" in sent.headers.get("Authorization", "")

    @responses_lib.activate
    def test_handle_sync_stream_yields_lines(self):
        responses_lib.get(
            f"{BASE_URL}/stream",
            body=b"line one\nline two\nline three\n",
            status=200,
            stream=True,
        )

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        results = list(backend.handle_sync_stream("GET", "/stream", str, response_parser=lambda x: x))
        backend.close()

        assert results == ["line one", "line two", "line three"]

    @responses_lib.activate
    def test_handle_sync_stream_error_raises(self):
        responses_lib.get(f"{BASE_URL}/missing", json={"error": "not found"}, status=404)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        with pytest.raises(api_exceptions.HTTPStatusError):
            list(backend.handle_sync_stream("GET", "/missing", str))
        backend.close()

    @responses_lib.activate
    def test_full_clientele_integration(self):
        responses_lib.get(f"{BASE_URL}/users/1", json={"id": 1, "name": "Alice"}, status=200)

        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        config = api_config.BaseConfig(base_url=BASE_URL, http_backend=backend)
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        def get_user(result: dict, user_id: int) -> dict:
            return result

        result = get_user(1)
        assert result == {"id": 1, "name": "Alice"}
        client.close()

    def test_convert_to_response(self):
        import requests

        req = requests.PreparedRequest()
        req.method = "GET"
        req.url = "https://api.example.com/get"

        native = requests.Response()
        native.status_code = 201
        native._content = b"hello"
        native.encoding = "utf-8"
        native.request = req

        result = requests_backend.RequestsHTTPBackend.convert_to_response(native)
        assert result.status_code == 201
        assert result.content == b"hello"
        assert result.text == "hello"
        assert result.request_method == "GET"
        assert result.request_url == "https://api.example.com/get"
