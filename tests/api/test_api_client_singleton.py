"""Tests for HTTP backend management in the APIClient."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from clientele.api import APIClient, BaseConfig
from clientele.http.fake_backend import FakeHTTPBackend
from clientele.testing import ResponseFactory, configure_client_for_testing

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


def test_can_provide_custom_http_backend() -> None:
    """Test that a custom HTTP backend can be provided to the APIClient."""
    custom_backend = FakeHTTPBackend(default_response=ResponseFactory.not_found())
    custom_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(data={"id": 1, "name": "Ada"}),
    )
    config = BaseConfig(base_url=BASE_URL, http_backend=custom_backend)
    client = APIClient(config=config)

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)

    # Verify the custom backend is used
    assert client.config.http_backend is custom_backend
    assert user.id == 1

    client.close()


@pytest.mark.asyncio
async def test_can_provide_custom_http_backend_async() -> None:
    """Test that a custom HTTP backend can be provided to the APIClient for async operations."""
    custom_backend = FakeHTTPBackend(default_response=ResponseFactory.not_found())
    custom_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )
    config = BaseConfig(base_url=BASE_URL, http_backend=custom_backend)
    client = APIClient(config=config)

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    user = await get_user(1)

    # Verify the custom backend is used
    assert client.config.http_backend is custom_backend
    assert user.id == 1

    await client.aclose()


def test_close_method_works() -> None:
    """Test that close() works without errors."""
    client = APIClient(base_url=BASE_URL)
    fake_backend = configure_client_for_testing(client)

    # Close should work without errors
    client.close()

    # Backend should still be accessible
    assert client.config.http_backend is fake_backend


@pytest.mark.asyncio
async def test_aclose_method_works() -> None:
    """Test that aclose() works without errors."""
    client = APIClient(base_url=BASE_URL)
    fake_backend = configure_client_for_testing(client)

    # Close should work without errors
    await client.aclose()

    # Backend should still be accessible
    assert client.config.http_backend is fake_backend


def test_can_reconfigure_with_base_url() -> None:
    """Test that base_url can be reconfigured."""
    client = APIClient(base_url="whatever")
    client.configure(base_url=BASE_URL)

    fake_backend = configure_client_for_testing(client)
    fake_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)
    assert user.id == 1

    client.close()


def test_can_reconfigure_with_custom_http_backend() -> None:
    """Test that a custom HTTP backend can be configured."""
    custom_backend = FakeHTTPBackend(default_response=ResponseFactory.not_found())
    custom_backend.queue_response(
        path="/users/1",
        response_obj=ResponseFactory.ok(
            data={"id": 1, "name": "Ada"},
        ),
    )
    client = APIClient(base_url=BASE_URL)
    config = BaseConfig(base_url=BASE_URL, http_backend=custom_backend)
    client.configure(config=config)

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)

    # Verify the custom backend is used
    assert client.config.http_backend is custom_backend
    assert user.id == 1

    client.close()
