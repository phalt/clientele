"""
Integration test to demonstrate connection pooling with api client pattern.

These tests simulate how auto-generated clients work, where a single APIClient
instance (created at module level) is shared across multiple decorated API functions.
The singleton httpx clients enable connection pooling across all API calls.
"""

from __future__ import annotations

import httpx
import pytest
from pydantic import BaseModel
from respx import MockRouter

from clientele import api as clientele_api

BASE_URL = "https://api.example.com"


class User(BaseModel):
    id: int
    name: str


class Config(BaseModel):
    """Simulated config class like the generated clients have."""

    base_url: str = BASE_URL
    headers: dict[str, str] = {}

    def httpx_client_options(self) -> dict:
        return {
            "base_url": self.base_url,
            "headers": self.headers,
            "timeout": 5.0,
        }


@pytest.mark.respx(base_url=BASE_URL)
def test_generated_client_singleton_reuses_connections(respx_mock: MockRouter) -> None:
    """
    Test that simulates how a generated client would work with singleton httpx clients.
    The generated client creates one APIClient instance and all decorated functions use it,
    which should reuse the same httpx.Client for connection pooling.
    """
    # Mock multiple endpoints
    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))
    respx_mock.get("/users/2").mock(return_value=httpx.Response(200, json={"id": 2, "name": "Bob"}))
    respx_mock.post("/users").mock(return_value=httpx.Response(201, json={"id": 3, "name": "Charlie"}))

    # This simulates how auto-generated client code creates the client (singleton pattern)
    # The generated code has: client = clientele_api.APIClient(config=config.Config())
    client = clientele_api.APIClient(base_url=BASE_URL)

    # Store reference to verify singleton behavior
    original_sync_client = client.config.http_backend._sync_client  # type: ignore

    # Define decorated functions like the generator does
    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    @client.post("/users")
    def create_user(data: dict, result: User) -> User:
        return result

    # Make multiple requests
    user1 = get_user(1)
    user2 = get_user(2)
    new_user = create_user(data={"name": "Charlie"})

    # Verify all calls used the same httpx.Client instance (connection pooling)
    assert client.config.http_backend._sync_client is original_sync_client  # type: ignore
    assert user1.id == 1
    assert user2.id == 2
    assert new_user.id == 3

    # Verify that we made the expected number of requests
    assert len(respx_mock.calls) == 3


@pytest.mark.respx(base_url=BASE_URL)
def test_custom_httpx_client_with_generated_pattern(respx_mock: MockRouter) -> None:
    """
    Test that users can provide their own httpx.Client with custom settings
    when instantiating the generated client pattern.
    """
    respx_mock.get("/users/1").mock(return_value=httpx.Response(200, json={"id": 1, "name": "Ada"}))

    # User creates a custom httpx client with specific connection pool settings
    custom_client = httpx.Client(
        base_url=BASE_URL,
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )

    # Pass the custom client to the api APIClient
    client = clientele_api.APIClient(base_url=BASE_URL, httpx_client=custom_client)

    @client.get("/users/{user_id}")
    def get_user(user_id: int, result: User) -> User:
        return result

    user = get_user(1)

    # Verify the custom client is used
    assert client.config.http_backend._sync_client is custom_client  # type: ignore
    assert user.id == 1
