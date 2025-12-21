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
"""

import typing


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

    result = {}

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
