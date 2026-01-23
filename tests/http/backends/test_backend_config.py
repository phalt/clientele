"""Tests for HTTP backend support."""

import httpx
import pytest
from respx import MockRouter

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import Response, fake_backend, httpx_backend

BASE_URL = "https://api.example.com"


class TestBackendIntegration:
    """Test integration between backends and API client."""

    @pytest.mark.respx(base_url=BASE_URL)
    def test_switching_backends(self, respx_mock: MockRouter):
        """Test switching between different backends."""
        # Start with fake backend
        fk_backend = fake_backend.FakeHTTPBackend(
            default_response=Response(
                status_code=200,
                content=b'{"backend": "fake"}',
                headers={"content-type": "application/json"},
            ),
        )
        config_fake = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fk_backend,
        )
        client_fake = api_client.APIClient(config=config_fake)

        @client_fake.get("/test")
        def test_fake(result: dict) -> dict:
            return result

        result = test_fake()
        assert result == {"backend": "fake"}
        assert len(fk_backend.requests) == 1

        client_fake.close()

        # Switch to httpx backend
        hx_backend = httpx_backend.HttpxHTTPBackend(client_options={"base_url": BASE_URL})
        config_httpx = api_config.BaseConfig(
            base_url=BASE_URL,
            http_backend=hx_backend,
        )
        client_httpx = api_client.APIClient(config=config_httpx)

        @client_httpx.get("/get")
        def test_httpx(result: dict) -> dict:
            return result

        respx_mock.get("/get").mock(return_value=httpx.Response(200, json={"headers": {"test": "value"}}))

        result = test_httpx()
        assert "headers" in result

        client_httpx.close()

    @pytest.mark.respx(base_url=BASE_URL)
    def test_no_backend_uses_default_httpx(self, respx_mock: MockRouter):
        """Test that not providing a backend uses httpx by default."""
        config = api_config.BaseConfig(base_url=BASE_URL)
        client = api_client.APIClient(config=config)

        respx_mock.get("/get").mock(return_value=httpx.Response(200, json={"headers": {"test": "value"}}))

        @client.get("/get")
        def test_get(result: dict) -> dict:
            return result

        # Should work with default httpx
        result = test_get()
        assert "headers" in result

        client.close()
