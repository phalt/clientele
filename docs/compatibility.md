# 💱 Compatibility

## OpenAPI Version Support

Clientele is designed for **OpenAPI 3.0.x** schemas and supports most standard-compliant implementations.

### Fully Supported

- **OpenAPI 3.0.0, 3.0.1, 3.0.2, 3.0.3** - Full support for all standard features

### Partial Support

- **OpenAPI 3.1.x** - Many OpenAPI 3.1 schemas work, but some advanced 3.1-specific features may not be fully supported yet. Test your schema with `clientele validate` to check compatibility.

### Not Supported

- **OpenAPI 2.0 (Swagger)** - The 2.0 format is deprecated and significantly different from 3.0+. Clientele does not support it. If you have a Swagger 2.0 schema, consider upgrading it to OpenAPI 3.0+ first.

## Framework Compatibility

Clientele works with any tool that generates standard OpenAPI 3.0+ schemas. We actively test and verify compatibility with these Python frameworks:

### Python Web Frameworks

#### ✅ FastAPI

**Status**: 100% compatibility guaranteed

[FastAPI](https://fastapi.tiangolo.com/) is Clientele's primary target framework. FastAPI's automatic OpenAPI schema generation works perfectly with Clientele.

- **Schema location**: Usually `/openapi.json`
- **operationId**: Auto-generated or customizable via `operation_id` parameter
- **Async support**: Full support for both sync and async clients
- **Authentication**: Bearer tokens, Basic auth, OAuth2 flows

**Learn more**: [Using Clientele with FastAPI](framework-fastapi.md)

#### ✅ Django REST Framework + drf-spectacular

**Status**: Full compatibility

[Django REST Framework](https://www.django-rest-framework.org/) with [drf-spectacular](https://github.com/tfranzel/drf-spectacular) generates high-quality OpenAPI 3.0 schemas.

- **Schema location**: Configurable, typically `/api/schema/`
- **operationId**: Customizable via `@extend_schema(operation_id=...)`
- **Serializers**: Convert seamlessly to Pydantic models
- **ViewSets**: All CRUD operations supported

We've tested Clientele with numerous DRF APIs - see [this GitHub issue](https://github.com/phalt/clientele/issues/23) for specific schemas we've validated.

**Learn more**: [Using Clientele with Django REST Framework](framework-drf.md)

#### ✅ Django Ninja

**Status**: Native support

[Django Ninja](https://django-ninja.dev/) uses Pydantic for schemas, which aligns perfectly with Clientele's output.

- **Schema location**: Usually `/api/openapi.json`
- **operationId**: Customizable via `operation_id` parameter
- **Schemas**: Already uses Pydantic, no conversion needed
- **Async support**: Supports both sync and async views

**Learn more**: [Using Clientele with Django Ninja](framework-django-ninja.md)

### Other Tested APIs

We've successfully generated clients from:

- **[Microsoft Azure APIs](https://learn.microsoft.com/en-us/azure/api-management/import-api-from-oas)** - Battle-tested and works well
- **[Twilio's API](https://www.twilio.com/docs/openapi)** - Tested with real-world complexity
- Various public APIs with standard OpenAPI 3.0.x schemas

## Schema Feature Support

### Fully Supported Features

✅ **Request/Response schemas** - All HTTP methods (GET, POST, PUT, PATCH, DELETE)  
✅ **Path parameters** - URL path variables  
✅ **Query parameters** - URL query strings, optional and required  
✅ **Request bodies** - JSON request payloads  
✅ **Multiple response types** - Different responses per status code  
✅ **Pydantic-compatible types** - Strings, integers, floats, booleans, dates, enums  
✅ **Arrays and lists** - Including nested arrays  
✅ **Nested objects** - Complex object hierarchies  
✅ **References (`$ref`)** - Schema reuse throughout the spec  
✅ **`oneOf`** - Discriminated unions with type aliases  
✅ **`anyOf`** - Flexible union types  
✅ **`allOf`** - Schema composition and inheritance  
✅ **`nullable`** - Optional/nullable fields  
✅ **Enums** - Enumerated string values  
✅ **HTTP Bearer authentication** - Token-based auth  
✅ **HTTP Basic authentication** - Username/password auth

### Partially Supported or Limited

⚠️ **File uploads** - May require manual customization  
⚠️ **OpenAPI 3.1 specific features** - Some edge cases may not work  
⚠️ **OAuth2 flows** - Schema is parsed, but token acquisition must be handled manually in `config.py`  
⚠️ **Complex polymorphism** - Some exotic `oneOf`/`anyOf` combinations may need adjustment  
⚠️ **Webhooks and Callbacks** - Schema elements may be ignored

### Not Supported

❌ **File downloads** - Response file handling not generated  
❌ **Server-Sent Events (SSE)** - Streaming responses not supported  
❌ **WebSockets** - Not applicable to HTTP clients  
❌ **Cookie authentication** - Must be handled manually  

## Known Schema Issues

### Poor OpenAPI Implementations

Despite a well-defined [specification](https://www.openapis.org/), we've discovered many tools generate non-standard OpenAPI schemas.

**What this means for you:**

- If `clientele validate` reports errors, the schema may not be spec-compliant
- Some schema generators have bugs or take liberties with the spec
- We can't guarantee 100% compatibility with every OpenAPI schema

**Recommendation:**

- Always run `clientele validate` on your schema first
- Report issues with specific schemas to help us improve
- For FastAPI, DRF, and Django Ninja, compatibility is excellent

### OpenAPI 3.1 Caveats

OpenAPI 3.1 aligned with JSON Schema 2020-12, introducing changes:

- `nullable` was replaced with `type: [...]` arrays
- Some keywords changed semantics
- Schema validation is stricter

**Current state:**
- Many OpenAPI 3.1 schemas work fine
- Some 3.1-specific features may not be fully supported
- We primarily target OpenAPI 3.0.x for guaranteed compatibility

## Validation

Use `clientele validate` to check if your schema will work:

```sh
clientele validate -u http://localhost:8000/openapi.json
```

or

```sh
clientele validate -f path/to/openapi.json
```

Clientele uses [openapi-core](https://openapi-core.readthedocs.io/en/latest/) to validate schemas against the OpenAPI specification.

!!! note

    Some OpenAPI schema generators do not fully conform to the [specification](https://spec.openapis.org/oas/v3.1.0). Validation helps catch these issues early.

## When Things Don't Work

If you encounter a schema that doesn't work with Clientele:

1. **Run validation**: `clientele validate -f your-schema.json` to see specific errors
2. **Check the version**: Ensure it's OpenAPI 3.0.x (not 2.0 or unusual 3.1 features)
3. **Try generation anyway**: Sometimes validation is overly strict
4. **Report issues**: Open a GitHub issue with your schema (or a minimal example)
5. **Manual fixes**: For minor issues, you can edit the generated code

## Best Practices for Compatibility

### For API Developers

If you're developing an API that others will consume with Clientele:

1. **Use FastAPI, DRF + drf-spectacular, or Django Ninja** for best results
2. **Provide custom `operationId` values** for readable function names
3. **Document your schemas** with descriptions and examples
4. **Test your OpenAPI schema** with `clientele validate`
5. **Avoid exotic schema features** unless necessary
6. **Stick to OpenAPI 3.0.x** for maximum compatibility

### For Client Developers

If you're consuming an API with Clientele:

1. **Validate first**: Run `clientele validate` before generating
2. **Start with framework guides**: If using FastAPI/DRF/Ninja, follow the specific guide
3. **Review generated code**: Ensure it matches your expectations
4. **Test thoroughly**: The generated client should be tested like any dependency
5. **Report issues**: Help us improve by reporting problematic schemas

## Summary

| Feature | Support Level | Notes |
|---------|---------------|-------|
| **OpenAPI 3.0.x** | ✅ Full | Primary target, fully supported |
| **OpenAPI 3.1.x** | ⚠️ Partial | Most features work, some edge cases may not |
| **OpenAPI 2.0** | ❌ None | Not supported, use 3.0+ instead |
| **FastAPI** | ✅ Full | 100% compatibility |
| **DRF + drf-spectacular** | ✅ Full | Extensively tested |
| **Django Ninja** | ✅ Full | Native Pydantic alignment |
| **Complex schemas** | ✅ Most | `oneOf`, `anyOf`, `allOf`, `nullable` supported |
| **File operations** | ⚠️ Limited | May need manual customization |
| **Authentication** | ✅ Basic/Bearer | OAuth2 flows need manual token handling |
