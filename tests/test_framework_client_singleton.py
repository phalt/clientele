"""Tests for singleton httpx client instances in the framework Client."""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.framework import Client

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


@pytest.mark.respx(base_url=BASE_URL)
def test_client_reuses_same_httpx_client_instance(respx_mock: MockRouter) -> None:
    """Test that the Client reuses the same httpx.Client instance across multiple requests."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))
    respx_mock.get("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Bob"}))

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    # Store reference to the internal client
    sync_client = client._sync_client

    # Make multiple requests
    user1 = get_user(1)
    user2 = get_user(2)

    # Verify the same client instance is reused
    assert client._sync_client is sync_client
    assert user1.id == 1
    assert user2.id == 2


@pytest.mark.respx(base_url=BASE_URL)
@pytest.mark.asyncio
async def test_async_client_reuses_same_httpx_client_instance(respx_mock: MockRouter) -> None:
    """Test that the Client reuses the same httpx.AsyncClient instance across multiple requests."""
    client = Client(base_url=BASE_URL)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))
    respx_mock.get("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Bob"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    # Store reference to the internal async client
    async_client = client._async_client

    # Make multiple requests
    user1 = await get_user(1)
    user2 = await get_user(2)

    # Verify the same client instance is reused
    assert client._async_client is async_client
    assert user1.id == 1
    assert user2.id == 2


@pytest.mark.respx(base_url=BASE_URL)
def test_can_provide_custom_httpx_client(respx_mock: MockRouter) -> None:
    """Test that a custom httpx.Client can be provided to the Client."""
    custom_httpx_client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    client = Client(base_url=BASE_URL, httpx_client=custom_httpx_client)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)

    # Verify the custom client is used
    assert client._sync_client is custom_httpx_client
    assert user.id == 1


@pytest.mark.respx(base_url=BASE_URL)
@pytest.mark.asyncio
async def test_can_provide_custom_httpx_async_client(respx_mock: MockRouter) -> None:
    """Test that a custom httpx.AsyncClient can be provided to the Client."""
    custom_httpx_async_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    client = Client(base_url=BASE_URL, httpx_async_client=custom_httpx_async_client)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    user = await get_user(1)

    # Verify the custom async client is used
    assert client._async_client is custom_httpx_async_client
    assert user.id == 1


def test_close_method_closes_owned_sync_client() -> None:
    """Test that close() closes the sync client if owned by the Client."""
    client = Client(base_url=BASE_URL)

    # Client should own the sync client
    assert client._owns_sync_client is True

    # Close should work without errors
    client.close()

    # After closing, the client should be closed
    assert client._sync_client.is_closed


@pytest.mark.asyncio
async def test_aclose_method_closes_owned_async_client() -> None:
    """Test that aclose() closes the async client if owned by the Client."""
    client = Client(base_url=BASE_URL)

    # Client should own the async client
    assert client._owns_async_client is True

    # Close should work without errors
    await client.aclose()

    # After closing, the async client should be closed
    assert client._async_client.is_closed


def test_close_does_not_close_custom_sync_client() -> None:
    """Test that close() does not close a custom httpx.Client provided by the user."""
    custom_httpx_client = httpx.Client(base_url=BASE_URL)
    client = Client(base_url=BASE_URL, httpx_client=custom_httpx_client)

    # Client should not own the sync client
    assert client._owns_sync_client is False

    # Close should not close the custom client
    client.close()
    assert not custom_httpx_client.is_closed

    # Clean up the custom client
    custom_httpx_client.close()


@pytest.mark.asyncio
async def test_aclose_does_not_close_custom_async_client() -> None:
    """Test that aclose() does not close a custom httpx.AsyncClient provided by the user."""
    custom_httpx_async_client = httpx.AsyncClient(base_url=BASE_URL)
    client = Client(base_url=BASE_URL, httpx_async_client=custom_httpx_async_client)

    # Client should not own the async client
    assert client._owns_async_client is False

    # Close should not close the custom async client
    await client.aclose()
    assert not custom_httpx_async_client.is_closed

    # Clean up the custom async client
    await custom_httpx_async_client.aclose()
