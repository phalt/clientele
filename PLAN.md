# Clientele: Low-Hanging Fruit Feature Plan

## Context

Clientele (v2.2.2) is a Python API-integration framework with two halves: a runtime decorator-based client (`clientele/api/`) and an OpenAPI→Python code generator (`clientele/generators/`). Recent releases shipped the high-demand runtime features (retries via stamina, logging, ResponseFactory testing helpers, discriminated unions, SSE streaming). The remaining gaps cluster in three areas: **generator robustness with real-world specs**, **generator coverage of common OpenAPI constructs**, and **runtime flexibility** (the one open issue, #233, is about multi-instance clients).

This plan identifies the features with the best value-to-effort ratio, validated against the actual code (file references checked), ordered by priority. Each item is independently shippable.

---

## Tier 1 — Do these first

### 1. Fix non-string enum generation (int/float/mixed enums) — **Small** (bug-fix grade)
- **Value:** Any spec with `enum: [1, 2, 3]` (status codes, versions — very common) **crashes generation** with an opaque `AttributeError`. Verified: `schemas.py:178` builds `{v: {"type": f'"{v}"'}}` from raw enum values and `generate_enum_properties` (`schemas.py:31-36`) calls `arg.upper()` on each — fails for any non-string member. Blocks adoption outright.
- **Implementation:** In `make_schema_class` (`clientele/generators/shared/generators/schemas.py:176-178`), branch on value types: all-string keeps current path; otherwise synthesize member names (`VALUE_1`, sanitized, deduped) and emit `repr(v)` values. Add an `IntEnum` base conditional in `schema_class.jinja2`. Add a fixture spec + test alongside `tests/test_complex_schemas.py`.
- **Risk:** member-name collisions after sanitization — dedupe with suffix.

### 2. Generate auth config from `components.securitySchemes` — **Small/Medium**
- **Value:** Nearly every real API has auth; today the generator ignores `securitySchemes` entirely (verified: `config_py.jinja2` is rendered with only `base_url` in context, `generators/api/generator.py:84-88`) and `docs/api-authentication.md` tells users to hand-edit `config.py`. This is the most visible "it just works" win available.
- **Implementation:** In `APIGenerator.generate_templates_files` (`generator.py:62`), read security schemes from the spec (via cicerone's components, falling back to the `__pydantic_extra__` pattern already used throughout `cicerone_compat.py`). Pass a normalized `auth_schemes` list to the template. Extend `config_py.jinja2` with conditionals: `http/bearer` → `bearer_token` field + `Authorization: Bearer` header injection; `apiKey` in header → field + header; `http/basic` → username/password fields. pydantic-settings gives env-var support for free. **Scope cut:** skip `apiKey`-in-query and `oauth2` flows (emit explanatory comment + MANIFEST note).
- **Risk:** cicerone may not model securitySchemes first-class — verify; the extras escape hatch covers it. `config.py` is never overwritten on regen (`generator.py:80-81`), so this only benefits fresh generations — acceptable and safe.

### 3. `clientele validate` CLI command + graceful spec error reporting — **Small/Medium**
- **Value:** Malformed specs and missing `$refs` currently crash mid-generation with `AttributeError` (helpers like `get_schema_from_ref` silently return `{}`). A pre-flight compatibility check directly reduces the project's most common class of bug report, and gives CI users a gate.
- **Implementation:** New `validate` command in `clientele/cli.py` reusing the already-factored `_load_openapi_spec`/`_prepare_spec` (`cli.py:23-94`). Walk paths via existing `cicerone_compat.path_item_to_operations_dict` and report: unresolvable `#/components/...` refs, path-based `$refs` (degrade to `typing.Any`), cookie params (currently silently dropped), multipart bodies (unsupported), missing `responses`, non-string enums (until item 1 lands). Rich table output, exit 0/1.
- **Risk:** minimal — pure read-path code over existing modules. Label findings as warnings vs errors.

### 4. Typed `additionalProperties` (`dict[str, Model]`) — **Small**
- **Value:** Map-like schemas (error maps, translations, metrics keyed by ID) are everywhere; currently degrade to `dict[str, Any]`, losing all validation. Root cause verified: `cicerone_compat.schema_to_dict` never copies `additionalProperties` out of the parsed model, so the type resolver never sees it.
- **Implementation:** (a) Copy `additionalProperties` through `schema_to_dict` and `normalize_openapi_31_schema` in `clientele/generators/cicerone_compat.py` (recurse for schema values, pass through booleans). (b) In `get_type` (`clientele/generators/shared/utils.py:~145`), when object has a schema-valued `additionalProperties`, return `dict[str, {inner}]`. (c) Objects with *only* `additionalProperties` should emit a `RootModel` via existing `schema_root_model.jinja2` (same pattern as array responses).
- **Risk:** forward-ref quoting inside `dict[str, "X"]` — existing quote/unquote helpers cover it.

---

## Tier 2 — High value, slightly more work

### 5. Per-call config override / multi-instance clients (open issue #233) — **Medium**
- **Value:** The only open issue, with real multi-tenant users blocked: generated `client.py` hardcodes one module-global `APIClient`, and `configure()` mutates global state (not thread-safe). Same spec + many hosts (the reporter's OCPI/EV-charging case) is impossible today.
- **Implementation:** Add a reserved `config` kwarg following the exact pattern of the existing reserved `query`/`headers` kwargs (`clientele/api/client.py:331-334`): pop in `_prepare_call`, carry on the prepared call, and in the four execute paths resolve `effective_config = override or self.config`. Lazily build the override's `http_backend` via existing `HttpxHTTPBackend.from_config` (mirrors `configure()`), so each tenant config caches its own connection pool. **No template change needed** — every generated function gains multi-tenant support for free. Document in `docs/`.
- **Risk:** param-name collision if a spec has a parameter literally named `config` — same pre-existing risk/guard as `query`/`headers`; document it.

### 6. Request/response hooks on `BaseConfig` — **Small/Medium**
- **Value:** One feature closes three gaps: interceptors/middleware, token-refresh auth flows, and de-facto rate limiting/tracing — all currently require forking an HTTP backend.
- **Implementation:** Add `request_hooks` / `response_hooks` lists (default empty) to `BaseConfig` (`clientele/api/config.py`). Invoke at the two choke points `_send_request` / `_send_request_async` (`api/client.py:~581-657`) and the two stream paths, passing a small mutable `RequestInfo` (method, url, headers, query, json) so hooks can mutate headers. ~60 lines + tests with `FakeHTTPBackend`.
- **Risk:** API lock-in — keep the hook signature minimal; sync hooks only at first.

### 7. Richer exception hierarchy — **Small**
- **Value:** Users want `except ClientError` vs `except ServerError` and a `status_code` attribute; today there are only two exception types (`api/exceptions.py`) and users dig into `.response.status_code`.
- **Implementation:** Add `ClientError(HTTPStatusError)` (4xx) and `ServerError(HTTPStatusError)` (5xx); pick subclass by range in `http/response.py:raise_for_status` (~lines 60-73). Add `status_code` property. Fully backwards-compatible. Update `docs/api-exceptions.md`.

---

## Tier 3 — Worth doing opportunistically

### 8. OpenAPI 3.1 type arrays → unions — **Small/Medium**
- **Value:** Correctness bug: `type: ["string", "integer"]` silently keeps only the first type (`cicerone_compat.py:51-52`), producing wrong runtime validation.
- **Implementation:** In `normalize_openapi_31_schema`, rewrite multi-type arrays to `anyOf` branches (+ `nullable` if `"null"` present); the downstream anyOf→union pipeline already works.

### 9. Cookie parameters: warn now, support later — **Small** (warning)
- **Value:** Cookie params are *silently dropped* (`base_clients.py:142-163` handles only query/path/header). Silent data loss is the worst failure mode.
- **Implementation:** Add an `elif in_ == "cookie":` branch logging a yellow console warning; surface the same in `validate` (item 3). Full cookie support (threading through 5 backends) is deferred — Medium, low demand.

### 10. Schema constraints → `pydantic.Field` validation — **Medium**
- **Value:** `minLength`/`pattern`/`minimum` etc. are stripped by `schema_to_dict` before generation, so generated models accept data the server will reject.
- **Implementation:** Copy constraint keys through `cicerone_compat`, then refactor `generate_class_properties` (`schemas.py:49-89`) so the four-way alias/default branching collapses into one `pydantic.Field(...)` builder that also takes `min_length`, `max_length`, `pattern`, `ge`, `le`, `multiple_of`. The refactor is the real work; the mapping is mechanical.
- **Risk:** behavior changes in the branchy alias/default code — add coverage first.

### 11. `--check` drift mode for CI — **Medium**
- **Value:** Teams committing generated clients want CI to fail when spec and code drift; no design ambiguity.
- **Implementation:** `--check` flag on `start_api` (`cli.py`): generate into a temp dir, run the same ruff formatting, diff against the output dir ignoring user-owned `config.py`/`pyproject.toml` (per `generator.py:80,108`), exit 1 with diff summary.
- **Risk:** ruff version skew causing false positives — document.

### 12. Usage examples in generated docstrings — **Small**
- **Value:** Cheap DX polish: copy-pasteable call example per generated function.
- **Implementation:** Pure template change in `api_get_method.jinja2` / `api_post_method.jinja2` using data already in context (func name, required args, data class). Sanitize summaries containing `"""` while there.

---

## Explicitly NOT low-hanging fruit (excluded, with rationale)

| Feature | Why excluded |
|---|---|
| **Multipart/file uploads** | Runtime hardwires `json=` payloads (`api/client.py:594, 633`); needs API design + changes to all 5 HTTP backends + generator. Real feature, multi-PR project (**Large**). |
| **Pagination helpers** | Auto-detecting cursor/page/offset conventions from arbitrary specs is unreliable; needs API design consensus. No honest small version exists. |
| **Webhooks (3.1)** | Generates *server-side* handlers — outside clientele's client-generation mission. At most list in MANIFEST. |
| **Path-based `$refs`** | Needs a general JSON-pointer resolver + naming scheme for anonymous schemas; low demand. The `typing.Any` fallback + a `validate` warning covers it. |
| **Built-in rate limiting** | Superseded by hooks (item 6) + existing stamina retries. |
| **Streaming for direct `.request()`** | Decorator path covers streaming; low demand. |

## Suggested sequencing

1. **Release A (generator robustness):** items 1, 3, 4 — two are bug-fix grade, plus the `validate` command that catches everything else.
2. **Release B (headline features):** items 2 (auth generation) and 5 (#233 multi-instance) — the two most visible wins.
3. **Release C (runtime ergonomics):** items 6 + 7 together.
4. Items 8–12 opportunistically / as good-first-issues (9 and 12 are ideal community contributions).

## Verification

- Each generator item: add a fixture to `example_openapi_specs/`, regenerate test clients under `tests/api_clients/`, assert generated code imports cleanly and round-trips via `FakeHTTPBackend` (existing pattern in the 63-file test suite).
- Item 1: spec with `enum: [1, 2, 3]` generates an importable `IntEnum`.
- Item 2: spec with bearer/apiKey/basic schemes → generated `config.py` exposes the fields and injects headers (assert via FakeHTTPBackend captured request).
- Item 5: two configs with different `base_url`s → concurrent calls hit the right host (FakeHTTPBackend records URLs).
- CLI items: run `clientele validate -f <broken spec>` and `--check` against a stale dir, assert exit codes.
- Full suite: `uv run pytest`.
