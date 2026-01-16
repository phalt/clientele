"""Tests for HTTP backend support."""

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import fake, httpx


class TestBackendIntegration:
    """Test integration between backends and API client."""

    def test_switching_backends(self):
        """Test switching between different backends."""
        # Start with fake backend
        fake_backend = fake.FakeHTTPBackend(
            default_content={"backend": "fake"},
        )
        config_fake = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client_fake = api_client.APIClient(config=config_fake)

        @client_fake.get("/test")
        def test_fake(result: dict) -> dict:
            return result

        result = test_fake()
        assert result == {"backend": "fake"}
        assert len(fake_backend.requests) == 1

        client_fake.close()

        # Switch to httpx backend
        httpx_backend = httpx.HttpxHTTPBackend(client_options={"base_url": "https://httpbin.org"})
        config_httpx = api_config.BaseConfig(
            base_url="https://httpbin.org",
            http_backend=httpx_backend,
        )
        client_httpx = api_client.APIClient(config=config_httpx)

        @client_httpx.get("/get")
        def test_httpx(result: dict) -> dict:
            return result

        result = test_httpx()
        assert "headers" in result  # Real response from httpbin

        client_httpx.close()

    def test_no_backend_uses_default_httpx(self):
        """Test that not providing a backend uses httpx by default."""
        config = api_config.BaseConfig(base_url="https://httpbin.org")
        client = api_client.APIClient(config=config)

        @client.get("/get")
        def test_get(result: dict) -> dict:
            return result

        # Should work with default httpx
        result = test_get()
        assert "headers" in result

        client.close()
