"""Tests for singleton httpx client instances in the APIClient."""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele.api import APIClient

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


@pytest.mark.respx(base_url=BASE_URL)
def test_can_provide_custom_httpx_client(respx_mock: MockRouter) -> None:
    """Test that a custom httpx.Client can be provided to the APIClient."""
    custom_httpx_client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    client = APIClient(base_url=BASE_URL, httpx_client=custom_httpx_client)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)

    # Verify the custom client is used
    assert client.config.http_backend._sync_client is custom_httpx_client  # type: ignore
    assert user.id == 1


@pytest.mark.respx(base_url=BASE_URL)
@pytest.mark.asyncio
async def test_can_provide_custom_httpx_async_client(respx_mock: MockRouter) -> None:
    """Test that a custom httpx.AsyncClient can be provided to the APIClient."""
    custom_httpx_async_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    client = APIClient(base_url=BASE_URL, httpx_async_client=custom_httpx_async_client)

    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))

    @client.get("/users/{user_id}")
    async def get_user(user_id: int, result: User) -> User:
        return result

    user = await get_user(1)

    # Verify the custom async client is used
    assert client.config.http_backend._async_client is custom_httpx_async_client  # type: ignore
    assert user.id == 1


def test_close_method_closes_owned_sync_client() -> None:
    """Test that close() closes the sync client."""
    client = APIClient(base_url=BASE_URL)

    # Close should work without errors
    client.close()

    # After closing, the client should be closed
    assert client.config.http_backend._sync_client.is_closed  # type: ignore


@pytest.mark.asyncio
async def test_aclose_method_closes_owned_async_client() -> None:
    """Test that aclose() closes the async client."""
    client = APIClient(base_url=BASE_URL)

    # Close should work without errors
    await client.aclose()

    # After closing, the async client should be closed
    assert client.config.http_backend._async_client.is_closed  # type: ignore
