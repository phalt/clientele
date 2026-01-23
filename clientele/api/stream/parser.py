from __future__ import annotations

import json
import typing

from clientele.api import type_utils


def hydrate_content(content: str, inner_type: typing.Any) -> typing.Any:
    """
    Convert string content to the appropriate type.

    Logic:
    - If inner_type is str: return as-is
    - If inner_type is dict: parse JSON to dict
    - If inner_type is Pydantic model: parse JSON and validate
    - Otherwise: attempt JSON parsing, fallback to string
    """
    # Case 1: Just return string
    if inner_type is str:
        return content

    # Case 2: Return as dict
    if inner_type is dict:
        return json.loads(content)

    # Case 3: Pydantic model - parse and validate
    if type_utils.is_pydantic_model(inner_type):
        data = json.loads(content)
        return inner_type.model_validate(data)

    # Case 4: TypedDict
    if type_utils.is_typeddict(inner_type):
        data = json.loads(content)
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for TypedDict {inner_type.__name__}, got {type(data).__name__}")
        return data

    # Default: Try JSON, fallback to string
    try:
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return content
