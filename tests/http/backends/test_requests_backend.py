"""Tests for the requests HTTP backend."""

from unittest.mock import MagicMock, patch

import pytest

from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.http import requests_backend

BASE_URL = "https://api.example.com"


def _make_mock_response(
    *,
    status_code: int = 200,
    content: bytes = b'{"ok": true}',
    text: str = '{"ok": true}',
    headers: dict | None = None,
    method: str = "GET",
    url: str = "https://api.example.com/get",
) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.content = content
    mock.text = text
    mock.headers = headers or {"content-type": "application/json"}
    mock.request.method = method
    mock.request.url = url
    return mock


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
        await backend.aclose()  # should not raise

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

    def test_convert_to_response(self):
        native = _make_mock_response(status_code=201, content=b"hello", text="hello")
        result = requests_backend.RequestsHTTPBackend.convert_to_response(native)
        assert result.status_code == 201
        assert result.content == b"hello"
        assert result.text == "hello"
        assert result.request_method == "GET"
        assert result.request_url == "https://api.example.com/get"

    def test_send_sync_request_relative_url(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response()

        with patch.object(backend.build_client(), "request", return_value=mock_response) as mock_request:
            result = backend.send_sync_request("GET", "/get")

        mock_request.assert_called_once_with(
            "GET",
            f"{BASE_URL}/get",
            timeout=5.0,
            allow_redirects=False,
        )
        assert result.status_code == 200

    def test_send_sync_request_absolute_url_unchanged(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(url="https://other.example.com/path")

        with patch.object(backend.build_client(), "request", return_value=mock_response) as mock_request:
            backend.send_sync_request("GET", "https://other.example.com/path")

        call_url = mock_request.call_args[0][1]
        assert call_url == "https://other.example.com/path"

    def test_send_sync_request_passes_kwargs(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response()

        with patch.object(backend.build_client(), "request", return_value=mock_response) as mock_request:
            backend.send_sync_request("POST", "/items", json={"name": "foo"}, params={"q": "1"})

        mock_request.assert_called_once_with(
            "POST",
            f"{BASE_URL}/items",
            timeout=5.0,
            allow_redirects=False,
            json={"name": "foo"},
            params={"q": "1"},
        )

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

    def test_handle_sync_stream_yields_lines(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(status_code=200)
        mock_response.iter_lines.return_value = iter(["line one", "", "line two"])

        with patch.object(backend.build_client(), "request", return_value=mock_response):
            results = list(backend.handle_sync_stream("GET", "/stream", str, response_parser=lambda x: x))

        assert results == ["line one", "line two"]
        mock_response.close.assert_called_once()

    def test_handle_sync_stream_error_raises(self):
        backend = requests_backend.RequestsHTTPBackend(base_url=BASE_URL)
        mock_response = _make_mock_response(status_code=404)
        mock_response.content = b"not found"
        mock_response.text = "not found"

        with patch.object(backend.build_client(), "request", return_value=mock_response):
            with pytest.raises(api_exceptions.HTTPStatusError):
                list(backend.handle_sync_stream("GET", "/missing", str))

        mock_response.close.assert_called_once()

    def test_full_url_strips_double_slash(self):
        backend = requests_backend.RequestsHTTPBackend(base_url="https://api.example.com/")
        assert backend._full_url("/users") == "https://api.example.com/users"
