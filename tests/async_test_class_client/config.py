"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.
"""

import httpx


class Config:
    """
    Configuration object for the API client.
    Pass an instance of this class to the Client constructor to configure
    the client with custom settings.

    Example:
        config = Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token",
            timeout=10.0,
            follow_redirects=True
        )
        client = Client(config=config)
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost",
        additional_headers: dict | None = None,
        user_key: str = "user",
        pass_key: str = "password",
        bearer_token: str = "token",
        timeout: float = 5.0,
        follow_redirects: bool = False,
        verify_ssl: bool = True,
        http2: bool = False,
        max_redirects: int = 20,
        limits: httpx.Limits | None = None,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ):
        """
        Initialize the configuration object.

        Args:
            api_base_url: Base URL for the API (default: "http://localhost")
            additional_headers: Additional headers to include in all requests (default: {})
            user_key: Username for HTTP Basic authentication (default: "user")
            pass_key: Password for HTTP Basic authentication (default: "password")
            bearer_token: Token for HTTP Bearer authentication (default: "token")
            timeout: Request timeout in seconds (default: 5.0)
            follow_redirects: Whether to follow HTTP redirects (default: False)
            verify_ssl: Whether to verify SSL certificates (default: True)
            http2: Whether to enable HTTP/2 support (default: False)
            max_redirects: Maximum number of redirects to follow (default: 20)
            limits: Connection pool limits (default: None, uses httpx defaults)
            transport: Custom transport instance (default: None, uses httpx defaults)
        """
        self.api_base_url = api_base_url
        self.additional_headers = additional_headers or {}
        self.user_key = user_key
        self.pass_key = pass_key
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.http2 = http2
        self.max_redirects = max_redirects
        self.limits = limits
        self.transport = transport
        self.transport = transport
