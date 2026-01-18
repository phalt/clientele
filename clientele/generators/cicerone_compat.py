"""
Compatibility layer for converting cicerone Pydantic models to dict structures.

LEGACY MODULE: This module exists as a temporary compatibility layer during the
migration from openapi-core to cicerone. The goal is to eventually remove this
module entirely and work directly with cicerone's Pydantic models throughout
the codebase, eliminating the need for these conversions.

This module provides conversion utilities to transform cicerone's typed OpenAPI models
(Operation, Parameter, RequestBody, Response, Schema) into dict structures that are
compatible with existing code generation templates.

These conversions handle:
- Pydantic extra fields (e.g., $ref, deprecated, enum)
- Nested object conversion
- Mixed types (both Pydantic models and raw dicts)
- OpenAPI 3.1 compatibility (e.g., array-based type definitions)
"""

import typing


def normalize_openapi_31_schema(schema_dict: dict) -> dict:
    """
    Normalize OpenAPI 3.1 schema to OpenAPI 3.0 compatible format.

    OpenAPI 3.1 allows type to be an array (e.g., ['integer', 'null'] for nullable),
    while OpenAPI 3.0 uses 'nullable: true'. This function converts the 3.1 format
    to 3.0 format for compatibility with cicerone.

    Args:
        schema_dict: Schema dictionary that may contain OpenAPI 3.1 features

    Returns:
        Normalized schema dictionary compatible with OpenAPI 3.0
    """
    if not isinstance(schema_dict, dict):
        return schema_dict

    # Create a copy to avoid modifying the original
    normalized = schema_dict.copy()

    # Handle type as array (OpenAPI 3.1 nullable types)
    if "type" in normalized and isinstance(normalized["type"], list):
        types = normalized["type"]
        # Filter out 'null' and get the actual type
        non_null_types = [t for t in types if t != "null"]
        has_null = "null" in types

        if non_null_types:
            # Use the first non-null type
            normalized["type"] = non_null_types[0]
            # Mark as nullable if null was in the array OR if already marked nullable
            if has_null or normalized.get("nullable", False):
                normalized["nullable"] = True
        else:
            # Only null type - treat as nullable string
            normalized["type"] = "string"
            normalized["nullable"] = True
    # Preserve existing nullable: true even if type is not an array
    elif "nullable" in normalized and normalized["nullable"]:
        # Ensure it stays nullable through normalization
        normalized["nullable"] = True

    # Recursively normalize nested schemas
    if "properties" in normalized and isinstance(normalized["properties"], dict):
        normalized["properties"] = {k: normalize_openapi_31_schema(v) for k, v in normalized["properties"].items()}

    if "items" in normalized:
        normalized["items"] = normalize_openapi_31_schema(normalized["items"])

    if "allOf" in normalized and isinstance(normalized["allOf"], list):
        normalized["allOf"] = [normalize_openapi_31_schema(s) for s in normalized["allOf"]]

    if "oneOf" in normalized and isinstance(normalized["oneOf"], list):
        normalized["oneOf"] = [normalize_openapi_31_schema(s) for s in normalized["oneOf"]]

    if "anyOf" in normalized and isinstance(normalized["anyOf"], list):
        normalized["anyOf"] = [normalize_openapi_31_schema(s) for s in normalized["anyOf"]]

    return normalized


def normalize_openapi_31_spec(spec_dict: dict) -> dict:
    """
    Normalize an entire OpenAPI 3.1 spec to OpenAPI 3.0 compatible format.

    This recursively processes all schemas in the components section and throughout
    the spec to handle OpenAPI 3.1 specific features.

    Args:
        spec_dict: Full OpenAPI spec dictionary

    Returns:
        Normalized spec dictionary compatible with OpenAPI 3.0/cicerone
    """
    if not isinstance(spec_dict, dict):
        return spec_dict

    normalized = spec_dict.copy()

    # Normalize schemas in components
    if "components" in normalized and isinstance(normalized["components"], dict):
        if "schemas" in normalized["components"] and isinstance(normalized["components"]["schemas"], dict):
            normalized["components"]["schemas"] = {
                k: normalize_openapi_31_schema(v) for k, v in normalized["components"]["schemas"].items()
            }

    # Normalize schemas in paths
    if "paths" in normalized and isinstance(normalized["paths"], dict):
        for path, path_item in normalized["paths"].items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict) or method.startswith("$"):
                    continue

                # Normalize request body schemas
                if "requestBody" in operation and isinstance(operation["requestBody"], dict):
                    if "content" in operation["requestBody"]:
                        for content_type, content in operation["requestBody"]["content"].items():
                            if "schema" in content:
                                operation["requestBody"]["content"][content_type]["schema"] = (
                                    normalize_openapi_31_schema(content["schema"])
                                )

                # Normalize response schemas
                if "responses" in operation and isinstance(operation["responses"], dict):
                    for status, response in operation["responses"].items():
                        if not isinstance(response, dict):
                            continue
                        if "content" in response:
                            for content_type, content in response["content"].items():
                                if "schema" in content:
                                    operation["responses"][status]["content"][content_type]["schema"] = (
                                        normalize_openapi_31_schema(content["schema"])
                                    )

                # Normalize parameter schemas
                if "parameters" in operation and isinstance(operation["parameters"], list):
                    for param in operation["parameters"]:
                        if isinstance(param, dict) and "schema" in param:
                            param["schema"] = normalize_openapi_31_schema(param["schema"])

    return normalized


def schema_to_dict(schema) -> dict:
    """
    Convert a cicerone Schema object to a dict representation.

    Handles both cicerone Schema objects and raw dicts (for backwards compatibility).
    Converts nested schemas recursively.

    Args:
        schema: A cicerone Schema object or dict

    Returns:
        Dict representation of the schema
    """
    # If it's already a dict, return it as-is
    if isinstance(schema, dict):
        return schema

    result = {}

    # Handle $ref - it's in the extra fields
    if hasattr(schema, "__pydantic_extra__") and schema.__pydantic_extra__ and "$ref" in schema.__pydantic_extra__:
        result["$ref"] = schema.__pydantic_extra__["$ref"]
        return result  # When $ref is present, return early as other fields are not relevant

    # Handle allOf
    if hasattr(schema, "all_of") and schema.all_of:
        result["allOf"] = [schema_to_dict(s) for s in schema.all_of]

    # Handle oneOf
    if hasattr(schema, "one_of") and schema.one_of:
        result["oneOf"] = [schema_to_dict(s) for s in schema.one_of]

    # Handle anyOf
    if hasattr(schema, "any_of") and schema.any_of:
        result["anyOf"] = [schema_to_dict(s) for s in schema.any_of]

    # Handle discriminator (for oneOf schemas) - it's in the extra fields
    if hasattr(schema, "__pydantic_extra__") and schema.__pydantic_extra__:
        if discriminator := schema.__pydantic_extra__.get("discriminator"):
            result["discriminator"] = discriminator

    # Handle enum - it's in the extra fields
    if hasattr(schema, "__pydantic_extra__") and schema.__pydantic_extra__ and "enum" in schema.__pydantic_extra__:
        result["enum"] = schema.__pydantic_extra__["enum"]

    # Handle properties
    if hasattr(schema, "properties") and schema.properties:
        result["properties"] = {k: schema_to_dict(v) for k, v in schema.properties.items()}

    # Handle required
    if hasattr(schema, "required") and schema.required:
        result["required"] = schema.required

    # Handle type
    if hasattr(schema, "type") and schema.type:
        result["type"] = schema.type

    # Handle format
    if hasattr(schema, "format") and schema.format:
        result["format"] = schema.format

    # Handle nullable
    if hasattr(schema, "nullable") and schema.nullable:
        result["nullable"] = schema.nullable

    # Handle items (for arrays)
    if hasattr(schema, "items") and schema.items:
        result["items"] = schema_to_dict(schema.items)

    # Handle title
    if hasattr(schema, "title") and schema.title:
        result["title"] = schema.title

    return result


def parameter_to_dict(param) -> dict:
    """
    Convert a cicerone Parameter object to a dict representation.

    Args:
        param: A cicerone Parameter object or dict

    Returns:
        Dict representation of the parameter
    """
    # If it's already a dict (likely a reference), return it as-is
    if isinstance(param, dict):
        return param

    # Handle $ref
    if hasattr(param, "ref") and param.ref:
        return {"$ref": param.ref}

    result = {
        "name": param.name,
        "in": param.in_,
        "required": param.required if hasattr(param, "required") else False,
    }

    if hasattr(param, "schema_") and param.schema_:
        result["schema"] = schema_to_dict(param.schema_)

    return result


def request_body_to_dict(request_body) -> dict:
    """
    Convert a cicerone RequestBody object to a dict representation.

    Args:
        request_body: A cicerone RequestBody object or dict

    Returns:
        Dict representation of the request body
    """
    # If it's already a dict, return it as-is
    if isinstance(request_body, dict):
        return request_body

    result: dict[str, typing.Any] = {}

    if hasattr(request_body, "content") and request_body.content:
        result["content"] = {}
        for media_type, media_type_obj in request_body.content.items():
            result["content"][media_type] = {}
            if hasattr(media_type_obj, "schema_") and media_type_obj.schema_:
                result["content"][media_type]["schema"] = schema_to_dict(media_type_obj.schema_)

    return result


def response_to_dict(response) -> dict:
    """
    Convert a cicerone Response object to a dict representation.

    Args:
        response: A cicerone Response object or dict

    Returns:
        Dict representation of the response
    """
    # If it's already a dict, return it as-is
    if isinstance(response, dict):
        return response

    result = {}

    if hasattr(response, "description") and response.description:
        result["description"] = response.description

    if hasattr(response, "content") and response.content:
        result["content"] = {}
        for media_type, media_type_obj in response.content.items():
            result["content"][media_type] = {}
            if hasattr(media_type_obj, "schema_") and media_type_obj.schema_:
                result["content"][media_type]["schema"] = schema_to_dict(media_type_obj.schema_)

    return result


def operation_to_dict(operation) -> dict:
    """
    Convert a cicerone Operation object to a dict representation.

    Args:
        operation: A cicerone Operation object or dict

    Returns:
        Dict representation of the operation
    """
    # If it's already a dict, return it as-is
    if isinstance(operation, dict):
        return operation

    result = {}

    if hasattr(operation, "operation_id") and operation.operation_id:
        result["operationId"] = operation.operation_id

    if hasattr(operation, "summary") and operation.summary:
        result["summary"] = operation.summary

    if hasattr(operation, "description") and operation.description:
        result["description"] = operation.description

    # deprecated is in the extra fields
    deprecated = get_pydantic_extra(operation, "deprecated")
    if deprecated is not None:
        result["deprecated"] = deprecated

    if hasattr(operation, "parameters") and operation.parameters:
        result["parameters"] = [parameter_to_dict(p) for p in operation.parameters]

    # request_body might be in extra fields
    request_body = getattr(operation, "request_body", None) or get_pydantic_extra(operation, "requestBody")
    if request_body:
        result["requestBody"] = request_body_to_dict(request_body)

    if hasattr(operation, "responses") and operation.responses:
        result["responses"] = {status: response_to_dict(resp) for status, resp in operation.responses.items()}

    return result


def get_pydantic_extra(obj: typing.Any, key: str) -> typing.Any:
    """
    Safely retrieve a value from an object's __pydantic_extra__ mapping.

    Returns the value associated with `key` if __pydantic_extra__ exists,
    is truthy, and contains `key`; otherwise returns None.

    Args:
        obj: The object to check for pydantic extra fields
        key: The key to look up in the extra fields

    Returns:
        The value if found, None otherwise
    """
    extra = getattr(obj, "__pydantic_extra__", None)
    if not extra or key not in extra:
        return None
    return extra[key]


def path_item_to_operations_dict(path_item) -> dict:
    """
    Convert a cicerone PathItem object to a dict of operations.

    This extracts all operations (get, post, put, etc.) from the path item
    and converts them to dicts, including any path-level parameters.

    Args:
        path_item: A cicerone PathItem object

    Returns:
        Dict mapping HTTP methods to operation dicts, with optional "parameters" key
    """
    operations_dict = {}

    # Convert each operation in the path item
    for method, operation in path_item.operations.items():
        operations_dict[method] = operation_to_dict(operation)

    # Add path-level parameters if they exist
    if hasattr(path_item, "parameters") and path_item.parameters:
        operations_dict["parameters"] = [parameter_to_dict(p) for p in path_item.parameters]
    else:
        # Check in pydantic extra fields
        parameters = get_pydantic_extra(path_item, "parameters")
        if parameters:
            operations_dict["parameters"] = parameters

    return operations_dict
