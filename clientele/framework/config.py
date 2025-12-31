from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class Config:
    """
    Runtime configuration for the decorator-based ``Client``.

    Parameters mirror the options exposed by generated clients so users can
    keep a single mental model for connection settings.
    """

    base_url: str = "http://localhost"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float | None = 5.0
    follow_redirects: bool = False
    auth: httpx.Auth | tuple[str, str] | None = None
    verify: bool | str = True
    http2: bool = False
    limits: httpx.Limits | None = None
    proxies: httpx._types.ProxiesTypes | None = None
    transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None
    cookies: httpx._types.CookieTypes | None = None

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
