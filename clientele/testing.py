from __future__ import annotations

from clientele.api import client as api_client
from clientele.http import fake_backend


def configure_client_for_testing(
    client: api_client.APIClient,
) -> fake_backend.FakeHTTPBackend:
    """Function that provides a FakeHTTPBackend for testing.

    This function takes an APIClient instance and
    configures it to use a FakeHTTPBackend.

    The function returns the FakeHTTPBackend instance so you can queue responses
    in your test.

    Args:
        client: An APIClient instance to configure with the fake backend.
    Returns:
        A FakeHTTPBackend instance configured with the client.

    """

    # Create the fake backend
    backend = fake_backend.FakeHTTPBackend()

    # Configure the client to use the fake backend
    config = client.config
    config.http_backend = backend
    client.configure(config=config)

    # Return the backend
    return backend
