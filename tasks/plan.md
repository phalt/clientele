# Implementation Plan: SSE runtime (`sse-runtime`)

Status: approved 20 October 2026. Next: Task 1.

Spec: [specs/SPEC-sse-runtime.md](../specs/SPEC-sse-runtime.md) (approved 20 October 2026). Tasks: [tasks/todo.md](todo.md).

## Overview

Replace the line-based backend stream interface with a byte-chunk contract that carries status and headers, move line splitting and SSE decoding into Clientele core, and expose typed SSE through `streaming_response=SSE(...)` returning `Stream[T]` / `AsyncStream[T]`. Everything ships as 2.4.0 across five PRs. No new runtime dependency.

## Architecture Decisions

- **Parser in core, vendored from httpx2.** Works on all five backends and the fake; httpx2's `client.sse` becomes a test oracle only.
- **Transitional shim, then hard break.** Task 2 adds `open_*_stream` with a default implementation that adapts the legacy `handle_*_stream`, so every task leaves the suite green. Task 6 deletes the shim and makes the new methods abstract. Users only ever see the final shape, because nothing ships until 2.4.0.
- **Status and content-type checks move to `clientele.api`.** Backends just report status, headers and chunks.
- **Read timeout plumbing is per request.** `BaseConfig.timeout` (5 s) stays the default; `SSE(read_timeout=...)` overrides per endpoint. Each backend maps it to its own read-timeout knob, and aiohttp streams switch from `ClientTimeout(total=...)` to `sock_read`.
- **`Stream[T]` subclasses `Iterator[T]`.** `type_utils` learns to treat `Stream` / `AsyncStream` annotations as streaming types; existing `Iterator[T]` annotations keep working.

## Dependency Graph

Build bottom-up: splitter, contract, backends, decoder, stream objects, SSE, then helpers and docs.

| Task | Depends on |
|---|---|
| 1. Line splitter | None |
| 2. Contract + httpx2 + client switch | 1 |
| 3. requests / niquests | 2 |
| 4. aiohttp | 2 |
| 5. Fake backend | 2 |
| 6. Remove shim | 3, 4, 5 |
| 7. Drop 3.10 | None |
| 8. Vendored decoder | None |
| 9. Fuzz + oracle | 7, 8 |
| 10. Stream objects | 6 |
| 11. SSE raw mode | 8, 10 |
| 12. Typed events | 11 |
| 13. `response_parser` | 11 |
| 14. mypy tests | 12 |
| 15. `ResponseFactory.sse` | 11 |
| 16. Round trip | 12, 15 |
| 17. Docs | 13, 14, 16 |

## Task List

Full task blocks (acceptance criteria, verification, files, size) are in [todo.md](todo.md).

### Phase 1: Stream contract (PR 1)
- [ ] Task 1: Core line splitter over byte chunks
- [ ] Task 2: Stream contract, httpx2 backend and client switch
- [ ] Task 3: requests and niquests backends on the new contract
- [ ] Task 4: aiohttp backend on the new contract, with a read timeout for streams
- [ ] Task 5: Fake backend `queue_stream`
- [ ] Task 6: Remove the shim; make `open_*_stream` abstract

### Checkpoint A: Contract
- [ ] Full suite, ruff, ty and import-linter green on every supported Python
- [ ] A JSONL stream from `pytest-httpserver` yields items incrementally on every backend
- [ ] Human review before PR 1 merges

### Phase 2: Python floor (PR 2, parallel with Phase 1)
- [ ] Task 7: Drop Python 3.10

### Phase 3: Decoder (PR 3)
- [ ] Task 8: Vendor httpx2's SSE decoder and port its tests
- [ ] Task 9: Byte-offset fuzz and httpx2 oracle tests

### Checkpoint B: Decoder
- [ ] Decoder suite, fuzz and oracle green
- [ ] Attribution present in the file header and `LICENSE`

### Phase 4: SSE API (PR 4)
- [ ] Task 10: `Stream` / `AsyncStream` returned from line mode
- [ ] Task 11: SSE raw mode (`str` and `ServerSentEvent` items), content-type check, read timeout
- [ ] Task 12: Typed SSE items, `SSEEvent`, sentinel and `ignore_unknown`
- [ ] Task 13: `response_parser` in SSE mode; `None` skips in both modes
- [ ] Task 14: mypy plugin tests for `Stream[T]` and `SSE`

### Checkpoint C: SSE API
- [ ] Same SSE scenario green on all five backends, sync and async where supported
- [ ] `ResourceWarning` only on leaked streams
- [ ] Human review before PR 4 merges

### Phase 5: Helpers and docs (PR 5)
- [ ] Task 15: `ResponseFactory.sse`
- [ ] Task 16: FastAPI `EventSourceResponse` round trip and incremental delivery test
- [ ] Task 17: Docs and 2.4.0 CHANGELOG

### Checkpoint D: Complete
- [ ] Every spec success criterion met
- [ ] `pip install clientele` installs the same packages as 2.3.1
- [ ] Ready to release 2.4.0

## Parallelisation

- **Safe in parallel:** Task 7 alongside Phase 1; Task 8 alongside Phase 1; Tasks 3, 4 and 5 once Task 2 lands; Tasks 12, 13 and 15 once Task 11 lands.
- **Sequential:** 1 then 2 (contract), 6 after 3, 4 and 5, 10 before any SSE work.
- **Contract first:** Task 2 fixes `StreamResponse` / `AsyncStreamResponse`; agree its shape at review before 3, 4 and 5 start.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| aiohttp streams die after 5 s total (`ClientTimeout(total=...)`) | High | Task 4 sets `sock_read` for streams and adds a test with a stream longer than the timeout |
| Per-request read timeout not settable on some backend | Med | Task 11 checks each backend; fall back to a per-stream client only if one cannot do it |
| Shim in Task 2 reports `status_code=200` for unmigrated backends | Low | Lives only between Tasks 2 and 6, never released; Task 6 deletes it |
| U+2028 split bug does not reproduce | Low | Task 1 writes the failing test first; if it passes on httpx2, keep the test as a regression guard and drop the claim from the CHANGELOG |
| `iter_content(chunk_size=None)` or `iter_any()` buffers | Med | Tasks 3 and 4 include an incremental-delivery test against `pytest-httpserver` |
| Suite runs with warnings as errors, so the fallback deprecation breaks tests | Low | Task 5 checks `filterwarnings` first and migrates internal tests to `queue_stream` |
| Vendored decoder drifts from upstream | Low | Oracle tests in Task 9 compare against httpx2 on every run |

## Open Questions

- None blocking. The remaining spec items (chunk semantics, per-backend timeouts, U+2028) are resolved inside Tasks 1, 3, 4 and 11.
