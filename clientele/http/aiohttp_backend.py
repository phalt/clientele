from __future__ import annotations

import typing

try:
    import aiohttp as aiohttp_lib
except ImportError as exc:
    raise ImportError(
        "The AiohttpHTTPBackend requires the 'aiohttp' library. Install it with: pip install aiohttp"
    ) from exc

from clientele.api import exceptions as api_exceptions
from clientele.api.stream import hydrate_content
from clientele.http import backends, response


class AiohttpHTTPBackend(backends.HTTPBackend):
    """Asynchronous-only HTTP backend using the aiohttp library.

    Sync methods (build_client, send_sync_request, handle_sync_stream) raise
    NotImplementedError. Use HttpxHTTPBackend for sync support.

    Args:
        base_url: Base URL prepended to all relative request paths.
        headers: Default headers applied to every request.
        timeout: Request timeout in seconds. None means no timeout.
        follow_redirects: Whether to follow HTTP redirects.
        verify: SSL certificate verification. False to disable; str CA bundle paths
            are not supported (use an ssl.SSLContext via a custom connector instead).
    """

    _async_client: aiohttp_lib.ClientSession | None = None

    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float | None = 5.0,
        follow_redirects: bool = False,
        verify: bool | str = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.aiohttp_timeout = (
            aiohttp_lib.ClientTimeout(total=timeout) if timeout is not None else aiohttp_lib.ClientTimeout(total=None)
        )
        self.follow_redirects = follow_redirects
        # aiohttp uses ssl=False to disable; str CA paths are not supported here
        self._ssl: bool | None = None if verify else False

    @classmethod
    def from_config(cls, config: typing.Any) -> "AiohttpHTTPBackend":
        return cls(
            base_url=config.base_url,
            headers=config.headers,
            timeout=config.timeout,
            follow_redirects=config.follow_redirects,
            verify=config.verify,
        )

    def _full_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return self.base_url + url

    def build_client(self) -> typing.Any:
        raise NotImplementedError("AiohttpHTTPBackend does not support sync requests. Use HttpxHTTPBackend instead.")

    def build_async_client(self) -> aiohttp_lib.ClientSession:
        if not self._async_client or self._async_client.closed:
            self._async_client = aiohttp_lib.ClientSession(headers=self.headers)
        return self._async_client

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        # Body must be pre-read via await resp.read() before calling this
        content: bytes = native_response._body or b""
        return response.Response(
            status_code=native_response.status,
            headers=dict(native_response.headers),
            content=content,
            request_method=native_response.method.upper(),
            request_url=str(native_response.url),
        )

    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        raise NotImplementedError("AiohttpHTTPBackend does not support sync requests. Use HttpxHTTPBackend instead.")

    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        session = self.build_async_client()
        async with session.request(
            method,
            self._full_url(url),
            timeout=self.aiohttp_timeout,
            allow_redirects=self.follow_redirects,
            ssl=self._ssl,
            **kwargs,
        ) as resp:
            await resp.read()
            return self.convert_to_response(resp)

    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
        raise NotImplementedError("AiohttpHTTPBackend does not support sync requests. Use HttpxHTTPBackend instead.")
        yield  # type: ignore[misc]

    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        session = self.build_async_client()
        async with session.request(
            method,
            self._full_url(url),
            timeout=self.aiohttp_timeout,
            allow_redirects=self.follow_redirects,
            ssl=self._ssl,
            **kwargs,
        ) as resp:
            if 400 <= resp.status < 600:
                await resp.read()
                generic_response = self.convert_to_response(resp)
                raise api_exceptions.HTTPStatusError(
                    response=generic_response,
                    reason=f"HTTP {resp.status}",
                )
            while True:
                line = await resp.content.readline()
                if not line:
                    break
                decoded = line.decode("utf-8").rstrip("\r\n")
                if not decoded:
                    continue
                if response_parser is not None:
                    yield response_parser(decoded)
                else:
                    yield hydrate_content(decoded, inner_type)

    def close(self) -> None:
        pass

    async def aclose(self) -> None:
        if self._async_client and not self._async_client.closed:
            await self._async_client.close()
            self._async_client = None
