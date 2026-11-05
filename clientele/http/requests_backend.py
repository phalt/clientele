from __future__ import annotations

import contextlib
import typing

try:
    import requests as requests_lib
except ImportError as exc:
    raise ImportError(
        "The RequestsHTTPBackend requires the 'requests' library. Install it with: pip install requests"
    ) from exc

from clientele.http import backends, response


class RequestsHTTPBackend(backends.HTTPBackend):
    """Synchronous-only HTTP backend using the requests library.

    Async methods (send_async_request, open_async_stream, build_async_client)
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

    @contextlib.contextmanager
    def open_sync_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.Generator[backends.StreamResponse, None, None]:
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
            yield backends.StreamResponse(
                status_code=requests_response.status_code,
                headers=dict(requests_response.headers),
                request_method=requests_response.request.method or method,
                request_url=requests_response.request.url or self._full_url(url),
                chunks=_iter_available(requests_response),
            )
        finally:
            requests_response.close()

    def open_async_stream(
        self,
        method: str,
        url: str,
        **kwargs: typing.Any,
    ) -> typing.AsyncContextManager[backends.AsyncStreamResponse]:
        raise NotImplementedError("RequestsHTTPBackend does not support async. Use HttpxHTTPBackend instead.")

    def close(self) -> None:
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None

    async def aclose(self) -> None:
        pass


def _iter_available(requests_response: requests_lib.Response) -> typing.Generator[bytes, None, None]:
    """Yield body bytes as soon as they arrive.

    requests' iter_content cannot do this for every response: with chunk_size=None
    urllib3 reads a body without chunked transfer-encoding to EOF, and a fixed size
    blocks until that many bytes arrive. urllib3's read1 returns whatever is
    available, decoding content-encoding as it goes. urllib3 releases before 2.3
    lack read1 and fall back to iter_content, which is incremental only for chunked
    responses.
    """
    raw = requests_response.raw
    read1 = getattr(raw, "read1", None)
    if read1 is None:
        yield from requests_response.iter_content(chunk_size=None)
        return

    # Map urllib3 errors to the requests exceptions iter_content raises.
    from requests import exceptions as requests_exceptions
    from urllib3 import exceptions as urllib3_exceptions

    try:
        # No size: urllib3 returns whatever is buffered or one read's worth, and
        # urllib3-future (which replaces urllib3 when niquests is installed) only
        # returns early for an unbounded read; a size makes it wait for that many bytes.
        while chunk := read1(decode_content=True):
            yield chunk
    except urllib3_exceptions.ProtocolError as exc:
        raise requests_exceptions.ChunkedEncodingError(exc) from exc
    except urllib3_exceptions.DecodeError as exc:
        raise requests_exceptions.ContentDecodingError(exc) from exc
    except urllib3_exceptions.ReadTimeoutError as exc:
        raise requests_exceptions.ConnectionError(exc) from exc
    except urllib3_exceptions.SSLError as exc:
        raise requests_exceptions.SSLError(exc) from exc
