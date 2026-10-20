# Tasks: SSE runtime (`sse-runtime`)

Plan: [tasks/plan.md](plan.md). Spec: [specs/SPEC-sse-runtime.md](../specs/SPEC-sse-runtime.md).

Standard checks for every task (referred to below as **checks**):

```
uv run ruff format --check . && uv run ruff check . && uv run ty check && uv run lint-imports
```

---

## Phase 1: Stream contract (PR 1)

## Task 1: Core line splitter over byte chunks

**Description:** Add `clientele/api/stream/lines.py` with sync and async splitters that turn byte chunks into `str` lines: split on `\n`, strip a trailing `\r`, decode UTF-8 incrementally across chunk boundaries, drop blank lines, flush a final unterminated line. Pure functions, not wired in yet. Write the U+2028 test first to confirm the httpx2 `iter_lines` bug.

**Status:** Done (228d66f). httpx2 2.13.1 `iter_lines` reproduced the U+2028 split.

**Acceptance criteria:**
- [x] A JSON string containing U+2028 or U+2029 stays on one line
- [x] Output is identical however the input bytes are split, including mid UTF-8 sequence
- [x] `\r\n` and `\n` both terminate lines; a trailing line with no newline is yielded

**Verification:**
- [x] Tests pass: `uv run pytest tests/api/stream/test_lines.py -vv`
- [x] Checks pass (ruff locally; ty and import-linter in CI)
- [x] Manual check: note whether the U+2028 case fails against httpx2 `iter_lines` today, and record the result in the PR

**Dependencies:** None

**Files likely touched:**
- `clientele/api/stream/lines.py`
- `tests/api/stream/test_lines.py`

**Estimated scope:** S

## Task 2: Stream contract, httpx2 backend and client switch

**Description:** Add `StreamResponse` / `AsyncStreamResponse` and `open_sync_stream` / `open_async_stream` to `HTTPBackend`, with a temporary default implementation that adapts the legacy `handle_*_stream` (lines re-encoded as chunks, `status_code=200`, empty headers). Implement both methods properly on the httpx2 backend (`client.stream` + `iter_bytes` / `aiter_bytes`, no status raising). Switch `_execute_sync_stream` / `_execute_async_stream` in `client.py` to open the stream at call time, raise `HTTPStatusError` there on 4xx/5xx with a buffered body, and feed chunks through Task 1's splitter into the existing hydration.

**Status:** Done. Real-socket check: first item at 0.1 s of a 1.3 s body, sync and async; 25 early-closed streams left no requests in the httpx2 pool.

**Acceptance criteria:**
- [x] httpx2 sync and async line streams behave as before for 2xx responses
- [x] 4xx/5xx raise `HTTPStatusError` when the decorated function is called, not on first iteration, for sync and async
- [x] Other backends still pass their existing stream tests through the shim

**Verification:**
- [x] Tests pass: `uv run pytest tests/api/test_stream.py tests/api/test_stream_httpx.py tests/http/backends -vv`
- [x] Full suite passes: `uv run pytest -x`
- [x] Checks pass

**Dependencies:** 1

**Files likely touched:**
- `clientele/http/backends.py`
- `clientele/http/httpx_backend.py`
- `clientele/api/client.py`
- `clientele/api/stream/parser.py`
- `tests/api/test_stream_httpx.py`

**Estimated scope:** M

## Task 3: requests and niquests backends on the new contract

**Description:** Implement `open_sync_stream` on requests and both methods on niquests using `stream=True` + `iter_content`: urllib3 `read1` for requests, `chunk_size=-1` for niquests (its documented "as they come" value; the async variant is awaited to get the generator). Confirm chunks arrive incrementally rather than buffered.

**Status:** Done. requests reads with urllib3 `read1()` with no size (falls back to `iter_content` on urllib3 < 2.3); a size makes urllib3-future, which replaces urllib3 whenever niquests is installed, wait for that many bytes: `iter_content(chunk_size=None)` buffers a non-chunked body to EOF, which the pytest-httpserver test caught. Also fixes the requests backend yielding `bytes` lines for responses without a declared charset. Verified locally against requests 2.34, niquests 3.18.8 (source) and real pytest-httpserver/pytest-asyncio.

**Acceptance criteria:**
- [x] Both backends return status, headers and raw chunks without raising on status
- [x] A slow stream from `pytest-httpserver` yields its first item before the server finishes
- [x] Existing stream tests for both backends pass unchanged in behaviour

**Verification:**
- [x] Tests pass: `uv run pytest tests/http/backends/test_requests_backend.py tests/http/backends/test_niquests_backend.py -vv`
- [x] Checks pass

**Dependencies:** 2

**Files likely touched:**
- `clientele/http/requests_backend.py`
- `clientele/http/niquests_backend.py`
- `tests/http/backends/test_requests_backend.py`
- `tests/http/backends/test_niquests_backend.py`

**Estimated scope:** M

## Task 4: aiohttp backend on the new contract, with a read timeout for streams

**Description:** Implement `open_async_stream` on aiohttp using `resp.content.iter_any()`. Streams currently use `ClientTimeout(total=timeout)`, which kills any stream after 5 s even while data flows; use `ClientTimeout(total=None, sock_read=timeout)` for streams.

**Status:** Done. Before the fix, a stream still receiving data died at the total timeout with a raw `asyncio.CancelledError`. Verified locally against aiohttp 3.13.5 (source, pure-Python mode) over real sockets: a 1.5 s stream under a 1.0 s timeout completes, a quiet one raises `SocketTimeoutError`, early-closed streams release their connections.

**Acceptance criteria:**
- [x] A stream that runs longer than the configured timeout, sending data more often than the timeout, completes
- [x] A stream that goes quiet for longer than the timeout raises a timeout
- [x] Chunks arrive incrementally (`pytest-httpserver` or aiohttp test server)

**Verification:**
- [x] Tests pass: `uv run pytest tests/http/backends/test_aiohttp_backend.py -vv`
- [x] Checks pass

**Dependencies:** 2

**Files likely touched:**
- `clientele/http/aiohttp_backend.py`
- `tests/http/backends/test_aiohttp_backend.py`

**Estimated scope:** S

## Task 5: Fake backend `queue_stream`

**Description:** Add public `FakeHTTPBackend.queue_stream(path, chunks: Sequence[bytes | str], *, status_code: int = 200, headers: Mapping[str, str] | None = None)` and implement `open_*_stream` from it. Keep the fallback that builds a stream from a queued response's text, but emit `DeprecationWarning`. pytest has no `filterwarnings` config today, so this will not fail the suite, but move Clientele's own tests to `queue_stream` anyway.

**Status:** Done. Each queued chunk is delivered separately so tests control chunk boundaries. The fallback's warning points at the caller's line on Python 3.12+ (`skip_file_prefixes`). `tests/api/test_stream.py` moved to `queue_stream`; the suite passes with the deprecation promoted to an error.

**Acceptance criteria:**
- [x] `queue_stream` drives both sync and async streams, with status and headers visible to the API layer
- [x] The text fallback still works and warns once per use
- [x] No internal test relies on the deprecated fallback

**Verification:**
- [x] Tests pass: `uv run pytest tests/http/backends/test_fake_backend.py tests/test_testing.py -vv`
- [x] Checks pass

**Dependencies:** 2

**Files likely touched:**
- `clientele/http/fake_backend.py`
- `tests/http/backends/test_fake_backend.py`
- `tests/test_testing.py`

**Estimated scope:** S

## Task 6: Remove the shim; make `open_*_stream` abstract

**Description:** Delete `handle_sync_stream` / `handle_async_stream` from the ABC and every backend, remove the transitional default, and mark `open_sync_stream` / `open_async_stream` abstract. Backends that only support one mode raise `NotImplementedError` from the other, as they do today.

**Status:** Done. Also corrected the unreleased 2.4.0 CHANGELOG entry and the `HTTPBackend` interface in `docs/api-http-backends.md`, which described the removed methods; the full docs pass is still Task 17.

**Acceptance criteria:**
- [x] `grep -rn "handle_sync_stream\|handle_async_stream" clientele` returns nothing
- [x] A backend subclass missing either method cannot be instantiated
- [x] Full suite green

**Verification:**
- [x] Full suite passes: `uv run pytest`
- [x] Checks pass

**Dependencies:** 3, 4, 5

**Files likely touched:**
- `clientele/http/backends.py`
- `clientele/http/httpx_backend.py`, `requests_backend.py`, `niquests_backend.py`, `aiohttp_backend.py`, `fake_backend.py` (deletions only)

**Estimated scope:** S (many files, deletion only)

## Checkpoint A: Contract
- [ ] Full suite, ruff, ty and import-linter green on every supported Python
- [ ] A JSONL stream from `pytest-httpserver` yields items incrementally on every backend
- [ ] Human review before PR 1 merges

---

## Phase 2: Python floor (PR 2)

## Task 7: Drop Python 3.10

**Description:** Set `requires-python = ">=3.11"`, remove `"3.10"` from the CI matrix in `.github/workflows/ci.yml`, and run `uv lock --upgrade-package httpx2` so the dev lock gets an httpx2 with `client.sse`. (There are no classifiers or ruff `target-version` to update; ruff infers it from `requires-python`.)

**Acceptance criteria:**
- [ ] CI matrix starts at 3.11; `uv.lock` resolves httpx2 >= 2.5
- [ ] `uv sync --frozen` and the full suite pass on 3.11 and 3.14

**Verification:**
- [ ] Full suite passes: `uv run pytest`
- [ ] Checks pass
- [ ] Manual check: `uv run python -c "import httpx2; print(httpx2.__version__)"` shows >= 2.5

**Dependencies:** None (can run in parallel with Phase 1)

**Files likely touched:**
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/ci.yml`

**Estimated scope:** XS

---

## Phase 3: Decoder (PR 3)

## Task 8: Vendor httpx2's SSE decoder and port its tests

**Description:** Copy the decoder from `httpx2/_sse.py` at a pinned commit into `clientele/api/stream/_sse_decoder.py`, adapted to consume byte chunks and produce Clientele's `ServerSentEvent` (frozen, slots: `event`, `data`, `id`, `retry`, `json()`), defined in the new public module `clientele/api/stream/sse.py`. Add the MIT header with the upstream commit hash and a third-party section in `LICENSE`. Port the upstream SSE test cases.

**Acceptance criteria:**
- [ ] Ported cases pass: multi-line data, CR/LF/CRLF, comments, NUL in `id`, invalid `retry`, EOF flush
- [ ] Events over `max_event_size` raise a decoder error that Task 11 maps to `EventTooLarge`
- [ ] Attribution present in the file header and `LICENSE`

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/stream/test_sse_decoder.py -vv`
- [ ] Checks pass

**Dependencies:** None

**Files likely touched:**
- `clientele/api/stream/_sse_decoder.py`
- `clientele/api/stream/sse.py` (`ServerSentEvent`)
- `tests/api/stream/test_sse_decoder.py`
- `LICENSE`

**Estimated scope:** M

## Task 9: Byte-offset fuzz and httpx2 oracle tests

**Description:** Add a test that splits each canned SSE body at every byte offset (including mid UTF-8 sequence) and asserts identical events. Add an oracle test that feeds the same bodies to httpx2's `client.sse` through `MockTransport` and compares.

**Acceptance criteria:**
- [ ] Fuzz test covers every canned body at every offset
- [ ] Oracle agrees with the vendored decoder on every canned body

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/stream/test_sse_decoder.py -vv`
- [ ] Checks pass

**Dependencies:** 7, 8

**Files likely touched:**
- `tests/api/stream/test_sse_decoder.py`
- `tests/api/stream/sse_bodies.py` (shared fixtures)

**Estimated scope:** S

## Checkpoint B: Decoder
- [ ] Decoder suite, fuzz and oracle green
- [ ] Human review before PR 3 merges

---

## Phase 4: SSE API (PR 4)

## Task 10: `Stream` / `AsyncStream` returned from line mode

**Description:** Add `clientele/api/stream/stream.py` with `Stream[T]` and `AsyncStream[T]` (`typing.Generic`, subclassing `Iterator` / `AsyncIterator`): context managers, `.response` (status, headers, request URL), `close()` / `aclose()`, idempotent close, auto-close on exhaustion or error, and `ResourceWarning` from `__del__` when leaked. Line mode returns them. Teach `type_utils.is_streaming_type` / `get_streaming_inner_type` / `is_async_streaming_type` to accept `Stream` / `AsyncStream` annotations. Export both from `clientele.api`.

**Acceptance criteria:**
- [ ] `result: Iterator[T]` and `result: Stream[T]` both work; `isinstance(result, Iterator)` holds
- [ ] Breaking out of a loop inside `with` closes the backend response
- [ ] A leaked, unexhausted stream emits `ResourceWarning`; closed or exhausted ones do not

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/stream tests/api/test_stream.py tests/api/test_type_utils.py -vv`
- [ ] Checks pass

**Dependencies:** 6

**Files likely touched:**
- `clientele/api/stream/stream.py`
- `clientele/api/type_utils.py`
- `clientele/api/client.py`
- `clientele/api/__init__.py`
- `tests/api/stream/test_stream_objects.py`

**Estimated scope:** M

## Task 11: SSE raw mode, content-type check and read timeout

**Description:** Add the `SSE` config dataclass and widen `streaming_response` to `bool | SSE` on every verb decorator. In SSE mode, route chunks through the vendored decoder and support `str` and `ServerSentEvent` item types. Add `StreamError`, `UnexpectedContentType` and `EventTooLarge` in `clientele/api/exceptions.py`, with a synthesised `Response` (first 4 KiB for content-type errors). Check the media type at call time. Plumb `SSE(read_timeout=...)` through each backend's per-request timeout; `UNSET` inherits `BaseConfig.timeout`, `None` disables. Expose `.last_event_id`.

**Acceptance criteria:**
- [ ] `result: Stream[str]` yields `data`; `result: Stream[ServerSentEvent]` yields full events, on every backend that supports the mode
- [ ] A JSON error body with `200` raises `UnexpectedContentType` at call time, with `.response.status_code` set
- [ ] `read_timeout` overrides the config timeout per endpoint on every backend

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/test_sse.py -vv`
- [ ] Checks pass

**Dependencies:** 8, 10

**Files likely touched:**
- `clientele/api/stream/sse.py` (`SSE`)
- `clientele/api/client.py`
- `clientele/api/stream/parser.py`
- `clientele/api/exceptions.py`
- `clientele/api/request_context.py`
- `tests/api/test_sse.py`

**Estimated scope:** M. This is the largest task: if the read-timeout plumbing needs backend changes, split it out as 11b (backends + timeout tests) and keep 11a to the API layer.

## Task 12: Typed SSE items, `SSEEvent`, sentinel and `ignore_unknown`

**Description:** Build one `TypeAdapter` per endpoint at decoration time. Models and model unions validate `event.data` as JSON; `SSEEvent` subclasses (and unions) validate the whole envelope, with `data: Json[Model]`. Apply `sentinel` against raw `data` before validation. `ignore_unknown` skips only `union_tag_invalid` failures. Other failures raise `StreamValidationError` (`.event`, `__cause__`) and close the stream.

**Acceptance criteria:**
- [ ] Both examples from the spec's Code Style section run as written
- [ ] `[DONE]` ends iteration and closes the connection without a validation error
- [ ] An unknown event type is skipped under `ignore_unknown`; a malformed known type still raises

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/test_sse.py -vv`
- [ ] Checks pass

**Dependencies:** 11

**Files likely touched:**
- `clientele/api/stream/parser.py`
- `clientele/api/stream/sse.py` (`SSEEvent`)
- `clientele/api/exceptions.py`
- `clientele/api/__init__.py`
- `tests/api/test_sse.py`

**Estimated scope:** M

## Task 13: `response_parser` in SSE mode; `None` skips in both modes

**Description:** In SSE mode, `response_parser` receives a `ServerSentEvent`. In both modes, a `None` return skips the item. Update decoration-time validation in `request_context.py` so a parser returning `T | None` is accepted for `Stream[T]`, which also fixes the current docs recipe failure.

**Acceptance criteria:**
- [ ] A parser returning `None` for some lines or events never yields `None`
- [ ] A parser annotated `-> ChatMessage | None` is accepted for `result: AsyncStream[ChatMessage]`
- [ ] Existing `response_parser` tests for non-stream calls are unchanged

**Verification:**
- [ ] Tests pass: `uv run pytest tests/api/test_api_response_parser.py tests/api/test_request_context.py tests/api/test_sse.py -vv`
- [ ] Checks pass

**Dependencies:** 11

**Files likely touched:**
- `clientele/api/request_context.py`
- `clientele/api/stream/parser.py`
- `tests/api/test_api_response_parser.py`
- `tests/api/test_request_context.py`

**Estimated scope:** S

## Task 14: mypy plugin tests for `Stream[T]` and `SSE`

**Description:** The plugin only strips the injected `result` / `response` parameters, so `Stream[T]` return types should need no plugin code. Add plugin tests that prove it for line mode and SSE mode, sync and async; change the plugin only if a test fails.

**Acceptance criteria:**
- [ ] mypy infers `Stream[T]` / `AsyncStream[T]` (awaited) for decorated stream functions
- [ ] `streaming_response=SSE(...)` type-checks

**Verification:**
- [ ] Tests pass: `uv run pytest tests/mypy -vv`
- [ ] Checks pass

**Dependencies:** 12

**Files likely touched:**
- `tests/mypy/test_mypy_plugin.py`
- `clientele/mypy.py` (only if needed)

**Estimated scope:** XS

## Checkpoint C: SSE API
- [ ] Same SSE scenario green on all five backends, sync and async where supported
- [ ] `ResourceWarning` only on leaked streams
- [ ] Human review before PR 4 merges

---

## Phase 5: Helpers and docs (PR 5)

## Task 15: `ResponseFactory.sse`

**Description:** Add `ResponseFactory.sse(*events)` to `clientele/testing.py`, accepting dicts, `ServerSentEvent`s or `SSEEvent` models and producing a valid `text/event-stream` body for `queue_stream`.

**Acceptance criteria:**
- [ ] Output round-trips through the vendored decoder to the same events
- [ ] The spec's testing example passes as written

**Verification:**
- [ ] Tests pass: `uv run pytest tests/test_testing.py -vv`
- [ ] Checks pass

**Dependencies:** 11

**Files likely touched:**
- `clientele/testing.py`
- `tests/test_testing.py`

**Estimated scope:** XS

## Task 16: FastAPI round trip and incremental delivery

**Description:** Add an integration test with a FastAPI `EventSourceResponse` endpoint returning `AsyncIterable[Item]`, consumed by a Clientele `AsyncStream[Item]`. Run it over a real socket (`pytest-httpserver` or uvicorn), because httpx2's `ASGITransport` buffers whole responses. Include a keep-alive gap longer than 5 s with `SSE(read_timeout=...)` set above it.

**Acceptance criteria:**
- [ ] Typed events round-trip with `id` preserved as `last_event_id`
- [ ] The first event arrives before the server finishes
- [ ] The keep-alive gap does not time out when `read_timeout` covers it, and does with the default

**Verification:**
- [ ] Tests pass: `uv run pytest tests/integration -vv`
- [ ] Checks pass

**Dependencies:** 12, 15

**Files likely touched:**
- `tests/integration/test_fastapi_sse.py`
- `tests/integration/__init__.py`

**Estimated scope:** S

## Task 17: Docs and 2.4.0 CHANGELOG

**Description:** Rewrite `docs/api-stream.md` (replace the SSE recipe with `SSE()`, both annotation styles, timeouts). Update `docs/api-http-backends.md` (new contract, custom-backend migration guide, WebSocket escape hatch), `docs/api-testing.md` (`queue_stream`, `ResponseFactory.sse`) and `docs/api-exceptions.md` (`StreamError` tree). Add the 2.4.0 CHANGELOG entry listing every breaking change.

**Acceptance criteria:**
- [ ] Every code sample in the changed docs runs (or is covered by a test)
- [ ] CHANGELOG lists all five breaking changes from the spec, each linking to its docs section
- [ ] `uv run mkdocs build --strict` passes

**Verification:**
- [ ] Docs build: `uv run mkdocs build --strict`
- [ ] Manual check: read `api-stream.md` top to bottom as a new user

**Dependencies:** 13, 14, 16

**Files likely touched:**
- `docs/api-stream.md`
- `docs/api-http-backends.md`
- `docs/api-testing.md`
- `docs/api-exceptions.md`
- `CHANGELOG.md` and `docs/CHANGELOG.md` (must stay byte-identical; `PUBLISHING.md` checks with `cmp`)

**Estimated scope:** M

## Checkpoint D: Complete
- [ ] Every spec success criterion met
- [ ] `pip install clientele` installs the same packages as 2.3.1
- [ ] Ready to release 2.4.0
