"""Tests for HTTP backend support."""

import pytest

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import Response, fake_backend
from clientele.testing import ResponseFactory


class TestFakeHTTPBackend:
    def test_clients_return_none(self):
        backend = fake_backend.FakeHTTPBackend()
        assert backend.build_client() is None
        assert backend.build_async_client() is None

    def test_convert_to_response_noop(self):
        backend = fake_backend.FakeHTTPBackend()
        sample_response = ResponseFactory.ok({"key": "value"})
        converted = backend.convert_to_response(sample_response)
        assert converted is sample_response

    def test_basic_request_capture(self):
        backend = fake_backend.FakeHTTPBackend(
            default_response=ResponseFactory.ok({"id": 1, "name": "Test"}),
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
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
        assert len(backend.requests) == 1
        assert backend.requests[0]["method"] == "GET"
        assert "/users/123" in backend.requests[0]["url"]

        client.close()

    def test_queued_responses(self):
        backend = fake_backend.FakeHTTPBackend()
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/resource")
        def get_resource(result: dict) -> dict:
            return result

        backend.queue_response(
            path="/resource",
            response_obj=ResponseFactory.ok({"first": "response"}),
        )
        backend.queue_response(
            path="/resource",
            response_obj=ResponseFactory.ok({"second": "response"}),
        )
        # Support bytes
        backend.queue_response(
            path="/resource",
            response_obj=ResponseFactory.ok({"bytes": "response"}),
        )

        result1 = get_resource()
        result2 = get_resource()
        result_bytes = get_resource()

        assert result1 == {"first": "response"}
        assert result2 == {"second": "response"}
        assert result_bytes == {"bytes": "response"}

        client.close()

    def test_default_headers_override(self):
        backend = fake_backend.FakeHTTPBackend(
            default_response=ResponseFactory.ok(
                data={},
                headers={"X-Default-Header": "DefaultValue", "content-type": "application/json"},
            ),
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/headers-test")
        def headers_test(result: dict, response: Response) -> Response:
            # Note: returns the response object instead!
            return response

        backend.queue_response(
            path="/headers-test",
            response_obj=ResponseFactory.ok(
                data={"status": "ok"},
                headers={"content-type": "application/json", "X-Default-Header": "DefaultValue"},
            ),
        )

        # Make request
        response = headers_test()

        # Verify response
        assert response.content == b'{"status": "ok"}'

        # Verify headers gets content-type and default header
        assert response.headers.keys() == {"content-type", "X-Default-Header"}
        client.close()

    def test_post_request_with_data(self):
        """Test POST request with data payload."""
        backend = fake_backend.FakeHTTPBackend(
            default_response=ResponseFactory.ok({"id": 42, "created": True}),
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
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
        assert len(backend.requests) == 1
        assert backend.requests[0]["method"] == "POST"
        assert backend.requests[0]["kwargs"]["json"] == {
            "name": "Alice",
            "email": "alice@example.com",
        }

        client.close()

    def test_reset(self):
        """Test resetting the fake backend."""
        backend = fake_backend.FakeHTTPBackend()
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/test")
        def test_endpoint(result: dict) -> dict:
            return result

        # Make some requests
        test_endpoint()
        test_endpoint()
        assert len(backend.requests) == 2

        # Reset
        backend.reset()
        assert len(backend.requests) == 0

        # Queue a response and reset
        backend.queue_response(
            path="/test",
            response_obj=ResponseFactory.ok({"test": "data"}),
        )
        backend.reset()
        assert len(backend._response_map) == 0

        client.close()

    @pytest.mark.asyncio
    async def test_async_requests(self):
        """Test async request capture."""
        backend = fake_backend.FakeHTTPBackend(
            default_response=ResponseFactory.ok({"async": True}),
        )
        config = api_config.BaseConfig(
            base_url="https://api.example.com",
            http_backend=backend,
        )
        client = api_client.APIClient(config=config)

        @client.get("/async-test")
        async def async_get(result: dict) -> dict:
            return result

        # Make async request
        result = await async_get()

        assert result == {"async": True}
        assert len(backend.requests) == 1
        assert backend.requests[0]["method"] == "GET"

        await client.aclose()
