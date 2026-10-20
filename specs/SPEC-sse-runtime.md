# Spec: SSE runtime (`sse-runtime`)

Status: draft, awaiting approval. Target release: 2.4.0. Decisions settled 20 October 2026.

See [capability-map.md](capability-map.md) for the related `cicerone-oas32` and `sse-generator` modules.

## Objective

Make the SSE support Clientele already advertises actually work, on every backend, without adding a runtime dependency.

Today it does not:

- Every backend drops blank lines (`if not line: continue`), and a blank line is the SSE event boundary. Multi-line `data:` is merged wrongly, and `event`, `id` and `retry` are lost.
- Streams never expose status or headers, so `Content-Type` cannot be checked.
- The SSE recipe in `docs/api-stream.md` fails Clientele's own decoration-time type check (`clientele/api/request_context.py`, the stringified type-name comparison). Its "return `None` to skip" promise is not implemented: `None` is yielded.
- httpx2's `iter_lines` splits on `str.splitlines` separators, including U+2028, which can cut a JSONL line inside a JSON string (inferred from `httpx2/_decoders.py`, not reproduced).

Who it is for: developers calling APIs without a good vendor SDK (internal services, FastAPI backends using `EventSourceResponse`, LLM gateways, MCP-style servers) who want typed events through the same decorators they already use.

Goals:

1. One backend stream contract that carries status, headers and raw bytes, implemented by all five backends.
2. A WHATWG-conformant SSE decoder in core, shared by every backend and by `FakeHTTPBackend`.
3. Typed SSE through the existing verb decorators: discriminated unions, sentinels, a closeable stream object, sync and async.
4. Line mode keeps its public behaviour, apart from the breaking changes listed under Delivery.

Non-goals: reconnection, WebSockets, generator support (separate spec), cicerone changes (separate spec).

## Tech Stack

- Python `>=3.11` after this release (3.10 dropped in its own PR). Internal code uses `typing.Generic[T]` and `typing.Self`; PEP 695 syntax waits for a 3.12 floor. Docs and examples show 3.14-style user code.
- Runtime dependencies unchanged: `httpx2`, `pydantic`, `pydantic-settings`, `stamina`.
- Backends: httpx2 (default, sync and async), requests (sync), aiohttp (async), niquests (sync and async), `FakeHTTPBackend`.
- Vendored code: httpx2's SSE decoder (`httpx2/_sse.py`, MIT, derived from httpx-sse) at a pinned upstream commit.
- Dev and test: uv, ruff, ty, import-linter, pytest, pytest-httpx2, aioresponses, responses, pytest-httpserver, FastAPI (already a dev dependency).

## Commands

```
Install:        uv sync
Format:         uv run ruff format . && uv run ruff check --fix .
Lint (CI):      uv run ruff format --check . && uv run ruff check .
Types:          uv run ty check
Import rules:   uv run lint-imports
Tests:          uv run pytest -vv --cov=clientele --cov-branch --cov-report=term-missing --cov-config=pyproject.toml
Focused tests:  uv run pytest tests/api/stream -vv
Docs:           uv run mkdocs serve
Lock httpx2:    uv lock --upgrade-package httpx2
```

## Project Structure

```
clientele/http/backends.py          → HTTPBackend ABC: open_sync_stream / open_async_stream, StreamResponse, AsyncStreamResponse
clientele/http/*_backend.py         → each backend's implementation of the contract
clientele/http/fake_backend.py      → FakeHTTPBackend.queue_stream
clientele/api/stream/__init__.py
clientele/api/stream/parser.py      → existing; line and SSE hydration
clientele/api/stream/lines.py       → core line splitter over byte chunks
clientele/api/stream/_sse_decoder.py → vendored httpx2 decoder, MIT header + upstream commit hash
clientele/api/stream/stream.py      → Stream / AsyncStream
clientele/api/exceptions.py         → StreamError tree
clientele/testing.py                → ResponseFactory.sse
clientele/mypy*                     → plugin update for Stream[T] and SSE
tests/api/stream/                   → decoder, fuzz, oracle, line splitter tests
tests/api/test_stream_*.py          → per-backend stream tests (rewritten)
tests/api/test_sse.py               → API-level SSE tests
docs/api-stream.md, api-http-backends.md, api-testing.md, api-exceptions.md
LICENSE                             → third-party section for the vendored decoder
```

### Backend contract

`HTTPBackend.handle_sync_stream` and `handle_async_stream` are removed. Two abstract methods replace them. Backends no longer raise on status; the API layer does.

```python
# clientele/http/backends.py
import abc
import typing
from collections.abc import AsyncIterator, Iterator, Mapping
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StreamResponse:
    status_code: int
    headers: Mapping[str, str]
    request_method: str
    request_url: str
    chunks: Iterator[bytes]


@dataclass(frozen=True, slots=True)
class AsyncStreamResponse:
    status_code: int
    headers: Mapping[str, str]
    request_method: str
    request_url: str
    chunks: AsyncIterator[bytes]


class HTTPBackend(abc.ABC):
    @abc.abstractmethod
    def open_sync_stream(
        self, method: str, url: str, **kwargs: typing.Any
    ) -> AbstractContextManager[StreamResponse]: ...

    @abc.abstractmethod
    def open_async_stream(
        self, method: str, url: str, **kwargs: typing.Any
    ) -> AbstractAsyncContextManager[AsyncStreamResponse]: ...
```

| Backend | Sync chunks | Async chunks |
|---|---|---|
| httpx2 | `client.stream(...)` + `iter_bytes()` | `client.stream(...)` + `aiter_bytes()` |
| requests | `stream=True` + `iter_content(chunk_size=None)` | Not supported (sync only today) |
| niquests | `stream=True` + `iter_content(chunk_size=None)` | Async equivalent |
| aiohttp | Not supported (async only today) | `resp.content.iter_any()` |
| Fake | Chunks from `queue_stream` | Same |

Data flow for one streamed call:

1. The decorator opens the backend stream when the function is called.
2. `clientele.api` checks the status (`HTTPStatusError` with a buffered body on 4xx/5xx) and, in SSE mode, the content type.
3. Chunks go to the line splitter (line mode) or the vendored SSE decoder (SSE mode).
4. Hydration turns each line or event into `T`, applying `response_parser`, the sentinel and `ignore_unknown`.
5. The result is wrapped in `Stream[T]` / `AsyncStream[T]`, which owns the backend context manager and closes it.

Line splitter: splits on `\n`, strips a trailing `\r`, decodes UTF-8 incrementally across chunk boundaries, and keeps dropping blank lines in line mode.

Import-linter: the `api-layers` and `runtime-base-dependencies` contracts hold unchanged, because nothing new is imported.

## Code Style

SSE is switched on by widening the existing keyword: `streaming_response: bool | SSE`. `True` still means line mode. No new decorator.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class SSE:
    sentinel: str | None = None                  # compared to raw data before validation; ends iteration
    ignore_unknown: bool = False                 # skip only union_tag_invalid failures
    max_event_size: int | None = 1024 * 1024     # bytes; EventTooLarge when exceeded
    read_timeout: float | None | Unset = UNSET   # UNSET inherits BaseConfig.timeout; None disables


@dataclass(frozen=True, slots=True)
class ServerSentEvent:
    event: str = "message"
    data: str = ""
    id: str = ""
    retry: int | None = None

    def json(self) -> object: ...
```

The item type comes from the `result` annotation, resolved once at decoration time into a `TypeAdapter`:

| `result` item type | What is validated | Typical API |
|---|---|---|
| Model, or union of models | `event.data` parsed as JSON | OpenAI, Anthropic (`type` inside the payload) |
| `str` | Raw `event.data` | Plain text streams |
| `ServerSentEvent` | Nothing; raw event | Custom handling |
| `SSEEvent` subclass, or union of them | The whole envelope; `data: Json[Model]` for JSON | OpenAPI 3.2 style, discriminated on `event:` |

Payload-discriminated stream (user code, 3.14):

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from clientele import api
from clientele.api import SSE, AsyncStream

client = api.APIClient(base_url="https://api.example.com")


class Delta(BaseModel):
    type: Literal["delta"]
    text: str


class Usage(BaseModel):
    type: Literal["usage"]
    output_tokens: int


type ChatChunk = Annotated[Delta | Usage, Field(discriminator="type")]


class ChatRequest(BaseModel):
    prompt: str


@client.post("/chat", streaming_response=SSE(sentinel="[DONE]", ignore_unknown=True))
async def chat(*, result: AsyncStream[ChatChunk], data: ChatRequest) -> AsyncStream[ChatChunk]:
    return result


async def main() -> None:
    stream = await chat(data=ChatRequest(prompt="hi"))  # request sent, status checked here
    async with stream:
        async for chunk in stream:
            match chunk:
                case Delta(text=text):
                    print(text, end="")
                case Usage(output_tokens=n):
                    print(f"\n{n} tokens")
```

Event-name-discriminated stream:

```python
from pydantic import Json

from clientele.api import SSEEvent, Stream


class Token(BaseModel):
    text: str


class TokenEvent(SSEEvent):
    event: Literal["token"]
    data: Json[Token]


class DoneEvent(SSEEvent):
    event: Literal["done"]


type BuildEvent = Annotated[TokenEvent | DoneEvent, Field(discriminator="event")]


@client.get("/builds/{build_id}/events", streaming_response=SSE())
def build_events(build_id: int, *, result: Stream[BuildEvent]) -> Stream[BuildEvent]:
    return result


with build_events(42) as events:
    print(events.response.status_code, events.response.headers.get("x-request-id"))
    for event in events:
        if isinstance(event, DoneEvent):
            break
    print(events.last_event_id)
```

Rules for both modes:

- Streamed functions always return `Stream[T]` (sync) or `AsyncStream[T]` (async). Each is an iterator and a context manager, with `.response` (status, headers, request URL), `.close()` / `.aclose()`, and `.last_event_id` in SSE mode. They subclass `Iterator` / `AsyncIterator`, so existing `result: Iterator[T]` annotations stay valid.
- The async calling convention is unchanged: `stream = await fn(...)`, then `async for`.
- In SSE mode `response_parser` receives a `ServerSentEvent`. In both modes, returning `None` skips the item.
- `response_map` with streaming is still rejected at decoration time.
- Public exports from `clientele.api`: `SSE`, `SSEEvent`, `ServerSentEvent`, `Stream`, `AsyncStream`.

### Errors

```
APIException                     # clientele/http/response.py (unchanged)
├── HTTPStatusError              # unchanged; now raised at call time for every stream
└── StreamError                  # new base, clientele/api/exceptions.py
    ├── UnexpectedContentType    # call time: SSE mode got a non text/event-stream response
    ├── StreamValidationError    # mid-stream: .event: ServerSentEvent, __cause__ = ValidationError
    └── EventTooLarge            # an event exceeded SSE.max_event_size
```

`APIException` needs a buffered `Response`, so one is built from the stream's status and headers: the first 4 KiB of body for `UnexpectedContentType`, empty for mid-stream errors.

| Check | When | Raises |
|---|---|---|
| Status 4xx/5xx | Call time, every stream mode | `HTTPStatusError`, body read fully |
| Content type (media type before `;`) | Call time, SSE mode only | `UnexpectedContentType`; no opt-out |
| Event size | While parsing | `EventTooLarge` |
| Validation | Per item | `StreamValidationError`, unless `ignore_unknown` and the failure is `union_tag_invalid` |

### Lifecycle

- The stream closes itself when exhausted, when the sentinel is hit, or when iteration raises.
- `with` / `async with`, `close()` and `aclose()` close it explicitly; closing twice is a no-op.
- `__del__` emits a `ResourceWarning` only if the stream was neither closed nor exhausted.
- Exiting the context manager mid-iteration closes the backend response.

### Timeouts

In httpx2, `BaseConfig.timeout` (default 5 s) acts as the read timeout between chunks. FastAPI sends a keep-alive comment every 15 s, so a quiet stream dies under the default. `SSE(read_timeout=...)` overrides it per endpoint, and the docs flag this prominently. The global default does not change.

## Testing Strategy

The decoder is pure, so most confidence comes from unit tests on it.

| Layer | What | Where |
|---|---|---|
| Decoder | Port httpx2's SSE tests (about 40 cases): multi-line data, CR/LF/CRLF, comments, NUL in `id`, bad `retry`, EOF flush, size cap | `tests/api/stream/test_sse_decoder.py` |
| Decoder fuzz | Split a canned body at every byte offset, including mid UTF-8 sequence; output matches the unsplit parse | Same file |
| Oracle | Same bodies through httpx2's `client.sse` with `MockTransport`; events must match (needs httpx2 >= 2.5 in the dev lock) | Same file |
| Line splitter | `\n` / `\r\n`, chunk boundaries, U+2028 inside a JSON string stays on one line | `tests/api/stream/test_lines.py` |
| Backends | Each backend's `open_*_stream` against its own mock (pytest-httpx2, aioresponses, responses) with chunked bodies, status and headers | `tests/api/test_stream_*.py` |
| API | Item type rules, sentinel, `ignore_unknown`, `response_parser` skip, every exception, closing, `ResourceWarning` | `tests/api/test_sse.py` |
| Round trip | FastAPI `EventSourceResponse` + `-> AsyncIterable[Item]` into a Clientele `AsyncStream` | `tests/integration/` |
| mypy plugin | `Stream[T]` return types and the `SSE` keyword in both modes | Plugin tests |

New public testing API:

```python
from clientele import testing


def test_build_events_stops_on_done() -> None:
    fake = testing.configure_client_for_testing(client)
    fake.queue_stream(
        "/builds/42/events",
        testing.ResponseFactory.sse(
            {"event": "token", "data": '{"text": "ok"}'},
            {"event": "done", "data": ""},
        ),
        headers={"content-type": "text/event-stream"},
    )
    with build_events(42) as events:
        assert [e.event for e in events] == ["token", "done"]
```

- `FakeHTTPBackend.queue_stream(path, chunks: Sequence[bytes | str], *, status_code: int = 200, headers: Mapping[str, str] | None = None)` feeds both modes.
- The old fallback (a stream built from a queued response's text) stays but emits a `DeprecationWarning`.
- httpx2's `ASGITransport` buffers the whole response, so incremental and infinite-stream tests use `pytest-httpserver`, not ASGI.
- Coverage: the new modules stay at the project's existing coverage level; the decoder and splitter aim for full branch coverage.

## Boundaries

- Always:
  - Keep httpx2 types out of the public API and out of exceptions.
  - Run the full backend matrix for any change to the stream path.
  - Keep `pip install clientele` dependencies unchanged.
- Ask first:
  - Changing `BaseConfig` defaults, including the 5 s timeout.
  - Any change to non-stream request paths.
  - Diverging from the vendored decoder's behaviour, other than bug fixes reported upstream.
- Never:
  - Import `httpx2.websockets` or `wsproto` from core (import-linter treats `httpx2` as one node and would not catch it).
  - Retry a stream from inside iteration.
  - Swallow validation errors other than `union_tag_invalid` under `ignore_unknown`.

Out of scope for this spec: reconnection and `Last-Event-ID` resend, `response_map` with streaming, callable sentinels, a content-type opt-out, WebSockets beyond the documented escape hatch, generator changes, cicerone changes.

## Success Criteria

- The ported decoder suite, the byte-offset fuzz test and the httpx2 oracle tests pass.
- The same SSE scenario passes on httpx2 (sync and async), requests (sync), aiohttp (async), niquests (sync and async) and the fake backend.
- A FastAPI `EventSourceResponse` endpoint round-trips typed events into a Clientele `AsyncStream`.
- A U+2028 character inside a JSON string in a JSONL stream yields one item, not two.
- An unclosed, unexhausted stream emits `ResourceWarning`; a closed or exhausted one does not.
- CI is green: ruff format and check, ty, import-linter, pytest on every supported Python.
- `pip install clientele` installs the same packages as 2.3.1.

## Delivery

Five PRs, released together as 2.4.0.

| PR | Contents | Depends on |
|---|---|---|
| 1. Stream contract | `open_*_stream` on all five backends, `StreamResponse`, core line splitter, call-time status errors, `queue_stream` | None |
| 2. Drop Python 3.10 | `requires-python = ">=3.11"`, CI matrix, `uv lock --upgrade-package httpx2` | None |
| 3. Vendored decoder | `_sse_decoder.py` with attribution, ported tests, fuzz, oracle | 1 (oracle needs 2) |
| 4. SSE API | `SSE`, `SSEEvent`, `ServerSentEvent`, `Stream`/`AsyncStream`, `response_parser` changes, exceptions, mypy plugin | 1, 3 |
| 5. Docs and helpers | `ResponseFactory.sse`, FastAPI round trip, docs rewrite, CHANGELOG | 4 |

Docs:

- `api-stream.md`: replace the SSE recipe with `SSE()`, document both annotation styles, add the timeout section.
- `api-http-backends.md`: the new contract, a migration guide for custom backend authors, and the WebSocket escape hatch (`http_backend.build_async_client().websocket(...)` after `uv add "httpx2[ws]>=2.6"`, with `http2=False`).
- `api-testing.md`: `queue_stream` and `ResponseFactory.sse`.
- `api-exceptions.md`: the `StreamError` tree.

Breaking changes for the 2.4.0 CHANGELOG:

- Custom backends: `handle_sync_stream` / `handle_async_stream` replaced by abstract `open_sync_stream` / `open_async_stream`.
- Sync line streams send the request at call time, so `HTTPStatusError` moves to the call.
- Streamed functions return `Stream[T]` / `AsyncStream[T]` instead of bare generators; code that only iterates is unaffected.
- `response_parser` returning `None` skips the item instead of yielding `None`.
- Python 3.10 is no longer supported.

## Decision Log

Settled 20 October 2026.

| Decision | Choice |
|---|---|
| Where SSE parsing lives | Core (Option A); httpx2 `client.sse` used only as a test oracle |
| 2.4.0 release | Held; one breaking change to the backend interface, not two |
| Old stream methods | Removed; new methods abstract |
| Status errors | Call time for every stream mode |
| Entry point | `streaming_response: bool \| SSE` |
| Return type | Always `Stream[T]` / `AsyncStream[T]` |
| Parser source | Vendored from httpx2 with attribution |
| Python 3.10 | Dropped in 2.4.0, own PR |
| Item types | Four rules; envelope validation only via `SSEEvent` subclasses |
| `ServerSentEvent` | Clientele's own type |
| Sentinel | Plain `str` |
| `ignore_unknown` | Skips `union_tag_invalid` only, default off |
| Mid-stream errors | `StreamValidationError` carrying the raw event, then close |
| Content type | Checked at call time, no opt-out |
| Timeouts | `SSE(read_timeout=...)`, inherits config by default |
| Line mode | Core splitter, blank lines still dropped |
| Testing | `queue_stream` + `ResponseFactory.sse`; old fallback deprecated |
| Exceptions | `StreamError` tree in `clientele/api/exceptions.py`, synthesised `Response` |
| Cleanup | Auto-close; `ResourceWarning` when leaked |
| Internal typing | `typing.Generic` until the 3.12 floor |
| Cicerone | Separate spec, no compat shim |
| WebSockets | Not built; escape hatch documented |

## Open Questions

- [ ] SSE `read_timeout` default: inherit the 5 s config timeout (current decision), or a stream-specific default such as 60 s?
- [ ] mypy plugin: not yet read closely; it may need no changes or more than one PR's worth. Check before PR 4.
- [ ] Per-request read timeout on every backend: httpx2 `Timeout`, requests/niquests `(connect, read)` tuple, aiohttp `ClientTimeout(sock_read=...)`. Confirm each can be set per stream.
- [ ] U+2028 split: write the failing test first in PR 1; report upstream to httpx2 if it reproduces.
- [ ] Chunk semantics: confirm `iter_content(chunk_size=None)` (requests, niquests) and `iter_any()` (aiohttp) yield data as it arrives.
- [ ] Demand: check Clientele's issue tracker for SSE or WebSocket requests to shape docs examples.
- [ ] Deprecation noise: check whether the test suite runs with warnings as errors before deprecating the `queue_response` stream fallback.
