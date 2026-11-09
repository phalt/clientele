# Issues TODO

Open GitHub issues to fix, ordered from lowest-hanging fruit to largest. Each has a spec in this directory (`<issue-number>.md`).

Convention for every fix (one PR per issue, linked with `Fixes #<n>`):

1. Write a failing test that proves the issue (`tests/.../test_issue_<n>.py`).
2. Make the fix.
3. Add a changelog entry under the unreleased version in `CHANGELOG.md`.
4. Run `make test`, `make format`, `make ty`, `make lint-imports` and `make generate-test-clients`.
5. Open a PR that links the issue.

## Phase 1: quick bug fixes

- [x] [#268](268.md): fields are required when a schema has no `required` list
- [x] [#279](279.md): use the bundled ruff instead of the one on `PATH`
- [x] [#277](277.md): duplicate enum members from punctuation-only differences

## Phase 2: generator type correctness

- [x] [#278](278.md): inline multi-value enums become `Literal` (fixes discriminated unions)
- [x] [#280](280.md): `uuid` / `date-time` / `date` string formats map to Python types

## Phase 3: serialization semantics

- [x] [#276](276.md): include defaulted fields in request bodies again; make `exclude_unset` opt-in (after #268)

## Phase 4: response handling

- [ ] [#265](265.md): keep 204/no-content in `response_map` and dereference response `$ref`s

## Phase 5: generator ordering

- [ ] [schema-order](schema-order.md): `schemas.py` fails to import when a `oneOf`/`anyOf` alias or array model comes before a component it references (no GitHub issue yet; found in #276)

## Phase 6: config (breaking)

- [ ] [#281](281.md): per-client `env_prefix` for generated `Config`

## Phase 7: new generator option

- [ ] [#282](282.md): `--base-class` option for generated models

## Dropped

- #233 (factory / per-tenant clients): out of scope for now.

## Release note

#276, #278, #280, #281 and #265 change behaviour or generated types. Together with the unreleased 2.4.0 changes, consider shipping as 3.0.0.
