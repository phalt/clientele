"""Tests for HTTP backend support."""

import pytest

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import fake


class TestFakeHTTPBackend:
    def test_basic_request_capture(self):
        fake_backend = fake.FakeHTTPBackend(
            default_content={"id": 1, "name": "Test"},
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/users/{user_id}")
        def get_user(user_id: int, result: dict) -> dict:
            return result

        # Make a request
        result = get_user(user_id=123)

        # Verify response
        assert result == {"id": 1, "name": "Test"}

        # Verify request was captured
        assert len(fake_backend.requests) == 1
        assert fake_backend.requests[0]["method"] == "GET"
        assert "/users/123" in fake_backend.requests[0]["url"]

        client.close()

    def test_queued_responses(self):
        fake_backend = fake.FakeHTTPBackend()
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/resource")
        def get_resource(result: dict) -> dict:
            return result

        fake_backend.queue_response(
            status=200,
            content={"first": "response"},
        )
        fake_backend.queue_response(
            status=200,
            content={"second": "response"},
        )

        result1 = get_resource()
        result2 = get_resource()

        assert result1 == {"first": "response"}
        assert result2 == {"second": "response"}

        client.close()

    def test_post_request_with_data(self):
        """Test POST request with data payload."""
        fake_backend = fake.FakeHTTPBackend(
            default_content={"id": 42, "created": True},
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client = api_client.APIClient(config=config)

        @client.post("/users")
        def create_user(data: dict, result: dict) -> dict:
            return result

        # Make request with payload
        result = create_user(data={"name": "Alice", "email": "alice@example.com"})

        # Verify response
        assert result == {"id": 42, "created": True}

        # Verify payload was captured
        assert len(fake_backend.requests) == 1
        assert fake_backend.requests[0]["method"] == "POST"
        assert fake_backend.requests[0]["kwargs"]["json"] == {
            "name": "Alice",
            "email": "alice@example.com",
        }

        client.close()

    def test_reset(self):
        """Test resetting the fake backend."""
        fake_backend = fake.FakeHTTPBackend()
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/test")
        def test_endpoint(result: dict) -> dict:
            return result

        # Make some requests
        test_endpoint()
        test_endpoint()
        assert len(fake_backend.requests) == 2

        # Reset
        fake_backend.reset()
        assert len(fake_backend.requests) == 0

        # Queue a response and reset
        fake_backend.queue_response(status=200, content={"test": "data"})
        fake_backend.reset()
        assert len(fake_backend._response_queue) == 0

        client.close()

    @pytest.mark.asyncio
    async def test_async_requests(self):
        """Test async request capture."""
        fake_backend = fake.FakeHTTPBackend(
            default_content={"async": True},
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=fake_backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/async-test")
        async def async_get(result: dict) -> dict:
            return result

        # Make async request
        result = await async_get()

        assert result == {"async": True}
        assert len(fake_backend.requests) == 1
        assert fake_backend.requests[0]["method"] == "GET"

        await client.aclose()
