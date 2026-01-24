"""Tests for testing utilities: ResponseFactory and NetworkErrorFactory simulation."""

import pytest

from clientele.api import client as api_client
from clientele.api import config as api_config
from clientele.http import fake_backend
from clientele.testing import NetworkErrorFactory, ResponseFactory


def test_ok_with_data():
    response = ResponseFactory.ok({"success": True})

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_ok_without_data():
    response = ResponseFactory.ok()

    assert response.status_code == 200
    assert response.content == b""


def test_created():
    response = ResponseFactory.created({"id": 42})

    assert response.status_code == 201
    assert response.json() == {"id": 42}


def test_created_without_data():
    response = ResponseFactory.created()

    assert response.status_code == 201
    assert response.content == b""


def test_accepted():
    response = ResponseFactory.accepted({"job_id": "abc123"})

    assert response.status_code == 202
    assert response.json() == {"job_id": "abc123"}


def test_no_content():
    response = ResponseFactory.no_content()

    assert response.status_code == 204
    assert response.content == b""


def test_bad_request():
    response = ResponseFactory.bad_request({"error": "Invalid input"})

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid input"}


def test_unauthorized():
    response = ResponseFactory.unauthorized({"error": "Not authorized"})

    assert response.status_code == 401
    assert response.json() == {"error": "Not authorized"}


def test_forbidden():
    response = ResponseFactory.forbidden({"error": "Access denied"})

    assert response.status_code == 403
    assert response.json() == {"error": "Access denied"}


def test_not_found():
    response = ResponseFactory.not_found({"error": "Resource not found"})

    assert response.status_code == 404
    assert response.json() == {"error": "Resource not found"}


def test_unprocessable_entity():
    response = ResponseFactory.unprocessable_entity({"errors": {"email": ["Invalid"]}})

    assert response.status_code == 422
    assert response.json() == {"errors": {"email": ["Invalid"]}}


def test_internal_server_error():
    response = ResponseFactory.internal_server_error({"error": "Something went wrong"})

    assert response.status_code == 500
    assert response.json() == {"error": "Something went wrong"}


def test_service_unavailable():
    response = ResponseFactory.service_unavailable({"error": "Service down"})

    assert response.status_code == 503
    assert response.json() == {"error": "Service down"}


def test_response_with_custom_headers():
    response = ResponseFactory.ok(
        {"data": "test"},
        headers={"X-Custom-Header": "custom-value"},
    )

    assert response.status_code == 200
    assert response.headers["X-Custom-Header"] == "custom-value"


def test_queue_timeout():
    """Test queuing and raising a timeout error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkErrorFactory.timeout())

    with pytest.raises(TimeoutError, match="Request timed out"):
        get_users()

    # Verify the error was captured in requests
    assert len(backend.requests) == 1
    assert "error" in backend.requests[0]

    client.close()


def test_queue_connection_refused():
    """Test queuing and raising a connection refused error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkErrorFactory.connection_refused())

    with pytest.raises(ConnectionRefusedError):
        get_users()

    client.close()


def test_queue_connection_reset():
    """Test queuing and raising a connection reset error."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkErrorFactory.connection_reset())

    with pytest.raises(ConnectionResetError, match="Connection reset by peer"):
        get_users()

    client.close()


def test_queue_dns_failure():
    """Test queuing and raising a DNS resolution failure."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkErrorFactory.dns_failure("api.example.com"))

    with pytest.raises(OSError, match="Failed to resolve hostname"):
        get_users()

    client.close()


def test_error_takes_priority_over_response():
    """Test that queued errors take priority over queued responses."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/resource")
    def get_resource(result: dict) -> dict:
        return result

    backend.queue_error("/resource", NetworkErrorFactory.timeout())
    backend.queue_response("/resource", ResponseFactory.ok({"data": "value"}))

    # Error should be raised first
    with pytest.raises(TimeoutError):
        get_resource()

    # Now the response should be returned
    result = get_resource()
    assert result == {"data": "value"}

    client.close()


def test_error_consumed_fifo():
    """Test that errors are consumed in FIFO order."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/resource")
    def get_resource(result: dict) -> dict:
        return result

    backend.queue_error("/resource", NetworkErrorFactory.timeout())
    backend.queue_error("/resource", NetworkErrorFactory.connection_refused())
    backend.queue_response("/resource", ResponseFactory.ok({"success": True}))

    with pytest.raises(TimeoutError):
        get_resource()

    with pytest.raises(ConnectionRefusedError):
        get_resource()

    result = get_resource()
    assert result == {"success": True}

    client.close()


@pytest.mark.asyncio
async def test_async_error():
    """Test that errors work with async requests."""
    backend = fake_backend.FakeHTTPBackend()
    config = api_config.BaseConfig(
        base_url="https://api.example.com",
        http_backend=backend,
    )
    client = api_client.APIClient(config=config)

    @client.get("/users")
    async def get_users(result: list) -> list:
        return result

    backend.queue_error("/users", NetworkErrorFactory.timeout())

    with pytest.raises(TimeoutError):
        await get_users()

    await client.aclose()


def test_reset_clears_errors():
    """Test that reset() clears queued errors."""
    backend = fake_backend.FakeHTTPBackend()

    backend.queue_error("/resource", NetworkErrorFactory.timeout())
    assert len(backend._error_map["/resource"]) == 1

    backend.reset()

    assert len(backend._error_map) == 0
