from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field


class Config(BaseModel):
    """
    Runtime configuration for the decorator-based ``Client``.

    Parameters mirror the options exposed by generated clients so users can
    keep a single mental model for connection settings.
    """

    model_config = {"arbitrary_types_allowed": True}

    base_url: str = "http://localhost"
    headers: dict[str, str] = Field(default_factory=dict)
    timeout: float | None = 5.0
    follow_redirects: bool = False
    auth: httpx.Auth | tuple[str, str] | None = None
    verify: bool | str = True
    http2: bool = False
    limits: httpx.Limits | None = None
    proxies: Any = None  # httpx._types.ProxyTypes
    transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None
    cookies: Any = None  # httpx._types.CookieTypes

    def httpx_client_options(self) -> dict[str, Any]:
        """Create a dictionary of options suitable for ``httpx.Client``."""

        options: dict[str, Any] = {
            "base_url": self.base_url,
            "headers": self.headers,
            "timeout": self.timeout,
            "follow_redirects": self.follow_redirects,
            "verify": self.verify,
            "http2": self.http2,
            "cookies": self.cookies,
        }
        if self.auth is not None:
            options["auth"] = self.auth
        if self.limits is not None:
            options["limits"] = self.limits
        if self.proxies is not None:
            options["proxies"] = self.proxies
        if self.transport is not None:
            options["transport"] = self.transport
        return options


def get_default_config() -> Config:
    """
    Create a default configuration instance.

    Returns a Config with sensible defaults suitable for most use cases.
    Users can override specific values by passing keyword arguments to Client
    or by providing their own Config instance.
    """
    return Config(
        base_url="http://localhost",
        headers={},
        timeout=5.0,
        follow_redirects=False,
        verify=True,
        http2=False,
    )
