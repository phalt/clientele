from __future__ import annotations

import contextlib
import inspect
import typing

try:
    import niquests as niquests_lib
except ImportError as exc:
    raise ImportError(
        "The NiquestsHTTPBackend requires the 'niquests' library. Install it with: pip install niquests"
    ) from exc

from clientele.http import backends, response


class NiquestsHTTPBackend(backends.HTTPBackend):
    """HTTP backend using the niquests library, supporting both sync and async.

    This backend supports both synchronous and asynchronous requests in a single instance.

    Args:
        base_url: Base URL prepended to all relative request paths.
        headers: Default headers applied to every request.
        timeout: Request timeout in seconds. None means no timeout.
        follow_redirects: Whether to follow HTTP redirects.
        verify: SSL certificate verification. True to enable, False to disable.
    """

    _sync_client: niquests_lib.Session | None = None
    _async_client: niquests_lib.AsyncSession | None = None

    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        timeout: float | None = 5.0,
        follow_redirects: bool = False,
        verify: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify = verify

    @classmethod
    def from_config(cls, config: typing.Any) -> NiquestsHTTPBackend:
        return cls(
            base_url=config.base_url,
            headers=config.headers,
            timeout=config.timeout,
            follow_redirects=config.follow_redirects,
            verify=bool(config.verify),
        )

    def _full_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return self.base_url + url

    def build_client(self) -> niquests_lib.Session:
        if not self._sync_client:
            session = niquests_lib.Session(headers=self.headers, timeout=self.timeout)
            session.verify = self.verify
            self._sync_client = session
        return self._sync_client

    def build_async_client(self) -> niquests_lib.AsyncSession:
        if not self._async_client:
            session = niquests_lib.AsyncSession(headers=self.headers, timeout=self.timeout)
            session.verify = self.verify
            self._async_client = session
        return self._async_client

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        # Accepts both sync Response and non-streaming async Response (same type)
        return response.Response(
            status_code=native_response.status_code,
            headers=dict(native_response.headers),
            content=native_response.content or b"",
            text=native_response.text or "",
            request_method=native_response.request.method,
            request_url=native_response.request.url or "",
        )

    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        session = self.build_client()
        resp = session.request(
            method,
            self._full_url(url),
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        return self.convert_to_response(resp)

    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        session = self.build_async_client()
        # Non-streaming async returns a regular Response (sync content/text)
        resp = await session.request(
            method,
            self._full_url(url),
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        return self.convert_to_response(resp)

    @contextlib.contextmanager
    def open_sync_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.Generator[backends.StreamResponse, None, None]:
        session = self.build_client()
        resp = session.request(
            method,
            self._full_url(url),
            stream=True,
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        try:
            request_method, request_url = _request_line(resp, method, self._full_url(url))
            yield backends.StreamResponse(
                status_code=resp.status_code or 0,
                headers=_str_headers(resp.headers),
                request_method=request_method,
                request_url=request_url,
                # niquests documents chunk_size=-1 as "receive chunks as they come".
                chunks=typing.cast(typing.Iterator[bytes], resp.iter_content(chunk_size=-1)),
            )
        finally:
            resp.close()

    @contextlib.asynccontextmanager
    async def open_async_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[backends.AsyncStreamResponse, None]:
        session = self.build_async_client()
        # stream=True returns an AsyncResponse with async content, iteration and close.
        resp = await session.request(
            method,
            self._full_url(url),
            stream=True,
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        try:
            # AsyncResponse.iter_content is a coroutine that returns an async generator in
            # current niquests; older releases implemented it as an async generator function.
            resp_any: typing.Any = resp
            chunks = resp_any.iter_content(chunk_size=-1)
            if inspect.isawaitable(chunks):
                chunks = await chunks
            request_method, request_url = _request_line(resp, method, self._full_url(url))
            yield backends.AsyncStreamResponse(
                status_code=resp.status_code or 0,
                headers=_str_headers(resp.headers),
                request_method=request_method,
                request_url=request_url,
                chunks=chunks,
            )
        finally:
            await resp.close()

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None


def _str_headers(headers: typing.Any) -> dict[str, str]:
    """Return headers as str values; niquests may expose raw bytes values."""
    return {name: value if isinstance(value, str) else value.decode("latin-1") for name, value in headers.items()}


def _request_line(resp: typing.Any, method: str, url: str) -> tuple[str, str]:
    """Return the sent request's method and URL, falling back to what was requested."""
    request = resp.request
    if request is None:
        return method, url
    return request.method or method, request.url or url
