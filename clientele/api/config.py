from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pydantic
import pydantic_settings

from clientele.cache import types as cache_types
from clientele.http import backends as http_backends


@runtime_checkable
class Logger(Protocol):
    """Protocol for logger implementations.

    Compatible with Python's standard logging.Logger interface.
    Users can pass any logging.getLogger() instance or custom logger
    that implements these methods.
    """

    def debug(self, msg: Any, *args: Any) -> None: ...
    def info(self, msg: Any, *args: Any) -> None: ...
    def warning(self, msg: Any, *args: Any) -> None: ...
    def error(self, msg: Any, *args: Any) -> None: ...


class BaseConfig(pydantic_settings.BaseSettings):
    """
    Runtime configuration for clientele clients.

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

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    base_url: str = "http://localhost"
    headers: dict[str, str] = pydantic.Field(default_factory=dict)
    timeout: float | None = 5.0
    follow_redirects: bool = False
    verify: bool | str = True
    http2: bool = False
    # Cache configuration
    cache_backend: cache_types.CacheBackend | None = None
    # HTTP backend configuration
    http_backend: http_backends.HTTPBackend | None = None
    # Logging configuration
    logger: Logger | None = None


def get_default_config(base_url: str) -> BaseConfig:
    """
    Create a default configuration instance.

    Returns a BaseConfig with sensible defaults suitable for most use cases.
    Users can override specific values by passing keyword arguments to Client
    or by providing their own Config instance.
    """
    return BaseConfig(
        base_url=base_url,
        headers={},
        timeout=5.0,
        follow_redirects=False,
        verify=True,
        http2=False,
        cache_backend=None,
        http_backend=None,
        logger=None,
    )
