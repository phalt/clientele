from __future__ import annotations

import typing

try:
    import niquests as niquests_lib
except ImportError as exc:
    raise ImportError(
        "The NiquestsHTTPBackend requires the 'niquests' library. Install it with: pip install niquests"
    ) from exc

from clientele.api import exceptions as api_exceptions
from clientele.api.stream import hydrate_content
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

    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
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
            if resp.status_code is not None and 400 <= resp.status_code < 600:
                generic_response = self.convert_to_response(resp)
                raise api_exceptions.HTTPStatusError(
                    response=generic_response,
                    reason=f"HTTP {resp.status_code}",
                )
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if response_parser is not None:
                    yield response_parser(line)
                else:
                    yield hydrate_content(line, inner_type)
        finally:
            resp.close()

    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        session = self.build_async_client()
        # stream=True returns AsyncResponse with async content/text/close
        resp = await session.request(
            method,
            self._full_url(url),
            stream=True,
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        try:
            if resp.status_code is not None and 400 <= resp.status_code < 600:
                content = await resp.content or b""
                text = await resp.text or ""
                headers: dict[str, str] = {
                    k: v if isinstance(v, str) else v.decode("latin-1") for k, v in resp.headers.items()
                }
                request_method = (resp.request.method or "GET") if resp.request is not None else "GET"
                request_url = (resp.request.url or "") if resp.request is not None else ""
                generic_response = response.Response(
                    status_code=resp.status_code,
                    headers=headers,
                    content=content,
                    text=text,
                    request_method=request_method,
                    request_url=request_url,
                )
                raise api_exceptions.HTTPStatusError(
                    response=generic_response,
                    reason=f"HTTP {resp.status_code}",
                )
            # AsyncResponse.iter_lines is annotated as a coroutine returning AsyncGenerator,
            # but niquests implements it as an async generator function (runtime discrepancy).
            # Assigning to Any lets us iterate correctly at runtime without misrepresenting types.
            resp_any: typing.Any = resp
            async for line in resp_any.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if response_parser is not None:
                    yield response_parser(line)
                else:
                    yield hydrate_content(line, inner_type)
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
