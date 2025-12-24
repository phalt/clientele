"""Shared utilities for schema generation across different generators."""

import typing

from clientele.generators.standard import utils


def build_union_type_string(schema_options: list[typing.Dict[str, typing.Any]]) -> str:
    """
    Build a union type string from a list of schema options (for oneOf or anyOf).

    Args:
        schema_options: List of schema option dictionaries from oneOf or anyOf

    Returns:
        A union type string (e.g., "Cat | Dog" or "typing.Union[Cat, Dog]")
    """
    union_types = []
    for schema_option in schema_options:
        if ref := schema_option.get("$ref"):
            ref_name = utils.class_name_titled(utils.schema_ref(ref))
            # Use direct reference without quotes for type aliases
            union_types.append(ref_name)
        else:
            # Inline schema - convert to type and remove forward ref quotes
            type_str = utils.get_type(schema_option)
            type_str = utils.remove_forward_ref_quotes(type_str)
            union_types.append(type_str)

    return utils.union_for_py_ver(union_types)
