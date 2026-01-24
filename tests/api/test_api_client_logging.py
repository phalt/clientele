"""Tests for request logging functionality."""

from __future__ import annotations

import logging

import pytest
from pydantic import BaseModel

from clientele.api import APIClient, BaseConfig
from clientele.testing import ResponseFactory, configure_client_for_testing

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


def test_sync_request_logs_method_and_url(caplog: pytest.LogCaptureFixture) -> None:
    """Test that sync requests log method and URL at debug level."""
    logger = logging.getLogger("test_sync")
    config = BaseConfig(base_url=BASE_URL, logger=logger)
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(data={"id": 1, "name": "Alice"}),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG, logger="test_sync"):
        get_user(1)

    assert len(caplog.records) >= 2
    messages = [r.message for r in caplog.records]
    assert any("Request: GET" in m and "/users/1" in m for m in messages)
    assert any("Response: GET" in m and "200" in m for m in messages)

    client.close()


@pytest.mark.asyncio
async def test_async_request_logs_method_and_url(caplog: pytest.LogCaptureFixture) -> None:
    """Test that async requests log method and URL at debug level."""
    logger = logging.getLogger("test_async")
    config = BaseConfig(base_url=BASE_URL, logger=logger)
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(path="/users/2", response_obj=ResponseFactory.ok(data={"id": 2, "name": "Bob"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG, logger="test_async"):
        await get_user(2)

    assert len(caplog.records) >= 2
    messages = [r.message for r in caplog.records]
    assert any("Request: GET" in m for m in messages)
    assert any("Response: GET" in m for m in messages)

    await client.aclose()


def test_no_logging_when_logger_not_configured(caplog: pytest.LogCaptureFixture) -> None:
    """Test that requests work normally when no logger is configured."""
    config = BaseConfig(base_url=BASE_URL)  # No logger
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/3",
        response_obj=ResponseFactory.ok(data={"id": 3, "name": "Charlie"}),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG):
        user = get_user(3)

    assert user.id == 3
    assert user.name == "Charlie"

    # Verify no request/response logs from our code
    our_logs = [
        record for record in caplog.records if "HTTP Request:" in record.message or "HTTP Response:" in record.message
    ]
    assert len(our_logs) == 0, "No request/response logs should be captured when logger is not configured"

    client.close()


def test_post_request_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Test that POST requests are logged correctly."""
    logger = logging.getLogger("test_post")
    config = BaseConfig(base_url=BASE_URL, logger=logger)
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users",
        response_obj=ResponseFactory.created(data={"id": 10, "name": "New User"}),
    )

    @client.post("/users")
    def create_user(data: dict, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG, logger="test_post"):
        create_user(data={"name": "New User"})

    messages = [r.message for r in caplog.records]
    assert any("POST" in m and "/users" in m for m in messages)
    assert any("201" in m for m in messages)

    client.close()


def test_response_logs_include_timing(caplog: pytest.LogCaptureFixture) -> None:
    """Test that response logs include timing information."""
    logger = logging.getLogger("test_timing")
    config = BaseConfig(base_url=BASE_URL, logger=logger)
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(data={"id": 1, "name": "Alice"}),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG, logger="test_timing"):
        get_user(1)

    messages = [r.message for r in caplog.records]
    assert any("s)" in m and "Response:" in m for m in messages)

    client.close()


def test_response_logs_include_content(caplog: pytest.LogCaptureFixture) -> None:
    """Test that response logs include the response content."""
    logger = logging.getLogger("test_content")
    config = BaseConfig(base_url=BASE_URL, logger=logger)
    client = APIClient(config=config)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(data={"id": 1, "name": "Alice"}),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    with caplog.at_level(logging.DEBUG, logger="test_content"):
        get_user(1)

    messages = [r.message for r in caplog.records]
    assert any("Response Content:" in m and '{"id": 1, "name": "Alice"}' in m for m in messages)

    client.close()
