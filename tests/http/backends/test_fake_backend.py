"""Tests for HTTP backend support."""

import sys

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
        def get_user(result: dict, user_id: int) -> dict:
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
        response = headers_test()  # type: ignore

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
        def create_user(result: dict, data: dict) -> dict:
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


class TestFakeHTTPBackendStreams:
    """queue_stream and the open_*_stream contract on FakeHTTPBackend."""

    def test_queue_stream_sync_reports_status_headers_and_chunks(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_stream(
            "/events",
            [b"data: a\n", "\n", "data: é\n\n"],
            status_code=201,
            headers={"content-type": "text/event-stream"},
        )

        with backend.open_sync_stream("GET", "/events", params={"q": "1"}) as stream_response:
            assert stream_response.status_code == 201
            assert stream_response.headers == {"content-type": "text/event-stream"}
            assert stream_response.request_method == "GET"
            assert stream_response.request_url == "/events"
            assert list(stream_response.chunks) == [b"data: a\n", b"\n", "data: é\n\n".encode()]

        assert backend.requests == [
            {"method": "GET", "url": "/events", "kwargs": {"params": {"q": "1"}}, "streaming": True}
        ]

    @pytest.mark.asyncio
    async def test_queue_stream_async_reports_status_headers_and_chunks(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_stream("/events", ["one\n", "two\n"], headers={"x-id": "7"})

        async with backend.open_async_stream("POST", "/events", json={"k": 1}) as stream_response:
            assert stream_response.status_code == 200
            assert stream_response.headers == {"x-id": "7"}
            assert stream_response.request_method == "POST"
            assert [chunk async for chunk in stream_response.chunks] == [b"one\n", b"two\n"]

        assert backend.requests[0]["kwargs"] == {"json": {"k": 1}}
        assert backend.requests[0]["streaming"] is True

    def test_queued_streams_are_consumed_in_order_per_path(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_stream("/a", ["first\n"])
        backend.queue_stream("/a", ["second\n"])
        backend.queue_stream("/b", ["other\n"])

        for expected in ([b"first\n"], [b"second\n"], []):
            with backend.open_sync_stream("GET", "/a") as stream_response:
                assert list(stream_response.chunks) == expected
        with backend.open_sync_stream("GET", "/b") as stream_response:
            assert list(stream_response.chunks) == [b"other\n"]

    def test_unqueued_stream_is_empty_ok(self):
        backend = fake_backend.FakeHTTPBackend()
        with backend.open_sync_stream("GET", "/nothing") as stream_response:
            assert stream_response.status_code == 200
            assert list(stream_response.chunks) == []

    def test_queued_chunks_list_is_copied(self):
        backend = fake_backend.FakeHTTPBackend()
        chunks = ["a\n"]
        backend.queue_stream("/events", chunks)
        chunks.append("b\n")
        with backend.open_sync_stream("GET", "/events") as stream_response:
            assert list(stream_response.chunks) == [b"a\n"]

    def test_reset_clears_queued_streams(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_stream("/events", ["a\n"])
        backend.reset()
        with backend.open_sync_stream("GET", "/events") as stream_response:
            assert list(stream_response.chunks) == []

    def test_queue_response_fallback_still_streams_but_warns(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_response("/events", ResponseFactory.not_found(data=b"a\nb\n", headers={"x-id": "7"}))

        with pytest.warns(DeprecationWarning, match="queue_stream"):
            with backend.open_sync_stream("GET", "/events") as stream_response:
                assert stream_response.status_code == 404
                assert stream_response.headers["x-id"] == "7"
                assert b"".join(stream_response.chunks) == b"a\nb\n"

    @pytest.mark.asyncio
    async def test_queue_response_fallback_warns_for_async_streams(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_response("/events", ResponseFactory.ok(data="x\n"))

        with pytest.warns(DeprecationWarning, match="queue_stream"):
            async with backend.open_async_stream("GET", "/events") as stream_response:
                assert b"".join([chunk async for chunk in stream_response.chunks]) == b"x\n"

    def test_queue_stream_takes_priority_over_queued_response(self):
        backend = fake_backend.FakeHTTPBackend()
        backend.queue_response("/events", ResponseFactory.ok(data="from response\n"))
        backend.queue_stream("/events", ["from stream\n"])
        with backend.open_sync_stream("GET", "/events") as stream_response:
            assert list(stream_response.chunks) == [b"from stream\n"]


class TestFakeHTTPBackendStreamsThroughClient:
    """FakeHTTPBackend streams driven through APIClient, as user tests would."""

    def test_lines_split_across_queued_chunks(self):
        from typing import Iterator

        from clientele.testing import configure_client_for_testing

        client = api_client.APIClient(base_url="https://api.example.com")
        fake = configure_client_for_testing(client)
        fake.queue_stream("/events", ['{"n": ', "1}\r", "\n\n", '{"n": 2}'])

        @client.get("/events", streaming_response=True)
        def events(result: Iterator[dict]) -> Iterator[dict]:
            return result

        assert list(events()) == [{"n": 1}, {"n": 2}]

    def test_error_status_raises_when_called_with_body(self):
        from typing import Iterator

        from clientele.api.exceptions import HTTPStatusError
        from clientele.testing import configure_client_for_testing

        client = api_client.APIClient(base_url="https://api.example.com")
        fake = configure_client_for_testing(client)
        fake.queue_stream("/events", [b'{"detail": "no"}'], status_code=403, headers={"x-id": "7"})

        @client.get("/events", streaming_response=True)
        def events(result: Iterator[dict]) -> Iterator[dict]:
            return result

        with pytest.raises(HTTPStatusError) as exc_info:
            events()
        assert exc_info.value.response.status_code == 403
        assert exc_info.value.response.json() == {"detail": "no"}
        assert exc_info.value.response.headers == {"x-id": "7"}

    @pytest.mark.skipif(sys.version_info < (3, 12), reason="skip_file_prefixes needs Python 3.12")
    def test_queue_response_fallback_warning_points_at_caller(self):
        from typing import Iterator

        from clientele.testing import configure_client_for_testing

        client = api_client.APIClient(base_url="https://api.example.com")
        fake = configure_client_for_testing(client)
        fake.queue_response("/events", ResponseFactory.ok(data="x\n"))

        @client.get("/events", streaming_response=True)
        def events(result: Iterator[str]) -> Iterator[str]:
            return result

        with pytest.warns(DeprecationWarning, match="queue_stream") as record:
            assert list(events()) == ["x"]
        assert record[0].filename == __file__
