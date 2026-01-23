"""Tests for HTTP backend support."""

import httpx
import pytest
from respx import MockRouter

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import httpx_backend as httpx_backend

BASE_URL = "https://api.example.com"


class TestHttpxHTTPBackend:
    """Test HttpxHTTPBackend functionality."""

    @pytest.mark.respx(base_url=BASE_URL)
    def test_custom_client_options(self, respx_mock: MockRouter):
        """Test passing custom options to httpx client."""
        # Mock the HTTP response
        respx_mock.get("/get").mock(return_value=httpx.Response(200, json={"headers": {"test": "value"}}))

        config = api_config.BaseConfig(
            base_url=BASE_URL,
        )
        client = api_client.APIClient(config=config)

        @client.get("/get")
        def test_get(result: dict) -> dict:
            return result

        result = test_get()

        # Verify we got a response
        assert "headers" in result

        client.close()

    def test_client_reuse(self):
        """Test that the same client is reused."""
        httpx_backend_instance = httpx_backend.HttpxHTTPBackend()

        # Build client twice - should get the same instance
        client1 = httpx_backend_instance.build_client()
        client2 = httpx_backend_instance.build_client()
        assert client1 is client2

        httpx_backend_instance.close()

    @pytest.mark.asyncio
    async def test_async_client_reuse(self):
        """Test that the same async client is reused."""
        httpx_backend_instance = httpx_backend.HttpxHTTPBackend()

        # Build async client twice - should get the same instance
        client1 = httpx_backend_instance.build_async_client()
        client2 = httpx_backend_instance.build_async_client()
        assert client1 is client2

        await httpx_backend_instance.aclose()

    @pytest.mark.asyncio
    @pytest.mark.respx(base_url=BASE_URL)
    async def test_async_real_request(self, respx_mock: MockRouter):
        """Test async requests with httpx backend."""
        # Mock the HTTP response
        respx_mock.get("/get").mock(return_value=httpx.Response(200, json={"headers": {"test": "value"}}))

        config = api_config.BaseConfig(
            base_url=BASE_URL,
        )
        client = api_client.APIClient(config=config)

        @client.get("/get")
        async def async_get(result: dict) -> dict:
            return result

        result = await async_get()

        assert "headers" in result

        await client.aclose()
