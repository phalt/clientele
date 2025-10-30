"""
This file will never be updated on subsequent clientele runs.
Use it as a space to store configuration and constants.
"""


class Config:
    """
    Configuration object for the API client.
    Pass an instance of this class to the Client constructor to configure
    the client with custom settings.

    Example:
        config = Config(
            api_base_url="https://api.example.com",
            bearer_token="my-token"
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
    ):
        """
        Initialize the configuration object.

        Args:
            api_base_url: Base URL for the API (default: "http://localhost")
            additional_headers: Additional headers to include in all requests (default: {})
            user_key: Username for HTTP Basic authentication (default: "user")
            pass_key: Password for HTTP Basic authentication (default: "password")
            bearer_token: Token for HTTP Bearer authentication (default: "token")
        """
        self.api_base_url = api_base_url
        self.additional_headers = additional_headers or {}
        self.user_key = user_key
        self.pass_key = pass_key
        self.bearer_token = bearer_token
