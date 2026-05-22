from __future__ import annotations

import typing

try:
    import requests as requests_lib
except ImportError as exc:
    raise ImportError(
        "The RequestsHTTPBackend requires the 'requests' library. Install it with: pip install requests"
    ) from exc

from clientele.api import exceptions as api_exceptions
from clientele.api.stream import hydrate_content
from clientele.http import backends, response


class RequestsHTTPBackend(backends.HTTPBackend):
    """Synchronous-only HTTP backend using the requests library.

    Async methods (send_async_request, handle_async_stream, build_async_client)
    raise NotImplementedError. Use HttpxHTTPBackend for async support.

    Args:
        base_url: Base URL prepended to all relative request paths.
        headers: Default headers applied to every request.
        timeout: Request timeout in seconds. None means no timeout.
        follow_redirects: Whether to follow HTTP redirects.
        verify: SSL certificate verification. True, False, or path to CA bundle.
    """

    _sync_client: requests_lib.Session | None = None

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
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify = verify

    @classmethod
    def from_config(cls, config: typing.Any) -> "RequestsHTTPBackend":
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

    def build_client(self) -> requests_lib.Session:
        if not self._sync_client:
            session = requests_lib.Session()
            session.headers.update(self.headers)
            # requests stubs type verify as bool but the library accepts str (CA bundle path) too
            session.verify = typing.cast(bool, self.verify)
            self._sync_client = session
        return self._sync_client

    def build_async_client(self) -> typing.Any:
        raise NotImplementedError("RequestsHTTPBackend does not support async. Use HttpxHTTPBackend instead.")

    @staticmethod
    def convert_to_response(native_response: typing.Any) -> response.Response:
        return response.Response(
            status_code=native_response.status_code,
            headers=dict(native_response.headers),
            content=native_response.content,
            text=native_response.text,
            request_method=native_response.request.method,
            request_url=native_response.request.url,
        )

    def send_sync_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        session = self.build_client()
        requests_response = session.request(
            method,
            self._full_url(url),
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        return self.convert_to_response(requests_response)

    async def send_async_request(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> response.Response:
        raise NotImplementedError("RequestsHTTPBackend does not support async. Use HttpxHTTPBackend instead.")

    def handle_sync_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Generator[typing.Any, None, None]:
        session = self.build_client()
        requests_response = session.request(
            method,
            self._full_url(url),
            stream=True,
            timeout=self.timeout,
            allow_redirects=self.follow_redirects,
            **kwargs,
        )
        try:
            if 400 <= requests_response.status_code < 600:
                generic_response = self.convert_to_response(requests_response)
                raise api_exceptions.HTTPStatusError(
                    response=generic_response,
                    reason=f"HTTP {requests_response.status_code}",
                )
            for line in requests_response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if response_parser is not None:
                    yield response_parser(line)
                else:
                    yield hydrate_content(line, inner_type)
        finally:
            requests_response.close()

    async def handle_async_stream(
        self,
        method: str,
        url: str,
        inner_type: typing.Any,
        response_parser: typing.Callable[[str], typing.Any] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncGenerator[typing.Any, None]:
        raise NotImplementedError("RequestsHTTPBackend does not support async. Use HttpxHTTPBackend instead.")
        yield  # type: ignore[misc]  # required to make this an async generator

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        pass
