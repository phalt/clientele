# schema-order: generated `schemas.py` fails to import when an alias or array model precedes what it references

Issue: none yet. Open one, rename this file to `<issue-number>.md` and update the `TODO.md` link before starting.

Found while fixing #276 (see the PR for #276, "Other information").

## Summary

`SchemasGenerator.generate_schema_classes` (`clientele/generators/shared/schemas.py`, ~line 253) writes components in spec order. Some generated definitions are evaluated at import time and reference other components by name:

- `oneOf` / `anyOf` components become module-level type aliases (`_create_union_type_alias`), e.g. `Notification = typing.Annotated[NotificationAddUser | NotificationRemoveUser, pydantic.Field(discriminator="action")]`.
- `type: array` components become `class L(ListResponse[Item])` (`schema_root_model.jinja2`). The base-class subscript is evaluated eagerly.

If either comes before a component it references, importing `schemas.py` raises `NameError: name '...' is not defined`. FastAPI emits components in alphabetical order, so a union named after its members (`Notification` before `NotificationAddUser`, the shape in #276) breaks out of the box.

Plain classes are not affected. `schemas_py.jinja2` starts with `from __future__ import annotations`, and the `model_rebuild()` loop at the end resolves field annotations. `allOf` is not affected because it inlines the referenced properties.

## Reproduction (checked on `main` after #276)

Generated with `APIGenerator` + `normalize_openapi_31_spec`, then imported:

| Components in spec order | Result |
|---|---|
| `U` (`oneOf` + discriminator on `UA`/`UB`), `UA`, `UB` | `NameError: name 'UA' is not defined` |
| `U` (`anyOf` of `UA`/`UB`), `UA`, `UB` | `NameError: name 'UA' is not defined` |
| `L` (`type: array`, `items: $ref UA`), `UA` | `NameError: name 'UA' is not defined` |
| `V` (`anyOf` of `U` and `string`), `U` (`anyOf` of `UA`/`UB`), `UA`, `UB` | `NameError: name 'U' is not defined` |
| `Box` (object with property `$ref U`), `UA`, `UB`, `U` | OK |
| `C` (`allOf` of `UA`), `UA` | OK |

## Proposed fix

Order components before generating them; don't change what each one generates.

- Eager dependencies: for a `oneOf` / `anyOf` / `type: array` component, every component it references by `$ref`, including refs nested in inline members or `items` (e.g. `anyOf: [{type: array, items: {$ref: X}}]`). Object, enum and `allOf` components have none.
- Stable topological sort: keep spec order, except that a component moves after its eager dependencies. Specs that already import keep their current order, so generated test clients shouldn't change.
- A cycle among eager definitions (e.g. `U = A | V`, `V = U | str`) can't be expressed as module-level aliases anyway. Fall back to spec order for those and log a warning; don't crash the generator.
- Keep it in `SchemasGenerator`. Don't move to string-quoted aliases or `typing.TypeAliasType`. That changes the generated types and how pydantic resolves discriminators.

Interacts with #282 (`--base-class`): a user-supplied base class is imported, not generated, so it adds no dependency.

## Tests

In `tests/generators/api/test_issue_<n>.py`, generating through `normalize_openapi_31_spec` the way the CLI does (as `tests/generators/api/test_issue_278.py` does):

- Each failing row in the table above imports, and the alias / `RootModel` validates data (e.g. a discriminated union picks the right member).
- The issue #276 shape in FastAPI's alphabetical order (`Notification`, `NotificationAddUser`, `NotificationRemoveUser`) imports and validates.
- Components that were already in a valid order keep their order in the generated file.
- A cycle among aliases generates without crashing (whether it imports is out of scope).
- Then remove the "listed after its members" workaround comment and ordering in `tests/api/test_issue_276.py`'s spec.
