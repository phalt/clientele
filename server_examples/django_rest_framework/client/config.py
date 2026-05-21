"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.
"""

import httpx2
from pydantic import Field

from clientele import api as clientele_api


class Config(clientele_api.BaseConfig):
    """
    Configuration object for your API client.

    Values can be set via:
    1. Environment variables (see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage)
    2. Direct instantiation with keyword arguments
    3. .env file (if python-dotenv is installed)

    Example:
        # From environment variables
        export API_BASE_URL="https://api.example.com"
        export BEARER_TOKEN="my-secret-token"
        config = Config()

        # Direct instantiation
        config = Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token",
            timeout=10.0
        )
    """

    base_url: str = "http://localhost:8000"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float | None = 5.0
    follow_redirects: bool = False
    verify: bool | str = True
    http2: bool = False
    auth: httpx2.Auth | tuple[str, str] | None = None
    limits: httpx2.Limits | None = None
    proxies: httpx2.Proxy | None = None
    transport: httpx2.BaseTransport | httpx2.AsyncBaseTransport | None = None
    cookies: httpx2.Cookies | None = None
