# Capability Map: Typed streaming (SSE)

Three independently testable capabilities, specified and built separately. Module ids are stable; specs are named `SPEC-<module id>.md`.

| Module id | Responsibility | Repo | Depends on |
|---|---|---|---|
| `sse-runtime` | Byte-chunk backend stream contract, core line splitter, vendored SSE decoder, `SSE()` API, `Stream`/`AsyncStream`, testing helpers, docs | phalt/clientele | None |
| `cicerone-oas32` | Typed `itemSchema` on `MediaType`, `contentMediaType`/`contentSchema` on `Schema`, sequential media types; Clientele moves off the `cicerone==0.3.0` pin | phalt/cicerone | None |
| `sse-generator` | `text/event-stream` and JSONL detection, `itemSchema` to typed events, `x-speakeasy-sse-sentinel` / `x-fern-streaming` | phalt/clientele | `sse-runtime`, `cicerone-oas32` |

Build order: `sse-runtime`, `cicerone-oas32` (in parallel) then `sse-generator`.

Specs:

- [SPEC-sse-runtime.md](SPEC-sse-runtime.md): drafted 20 October 2026
- `SPEC-cicerone-oas32.md`: not written; lives in phalt/cicerone
- `SPEC-sse-generator.md`: not written

Out of scope for this initiative: WebSockets. The runtime spec documents an escape hatch through the httpx2 backend's own client.
