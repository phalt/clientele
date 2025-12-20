import functools
import keyword
import re

import openapi_core

from clientele import settings

# Pre-computed set of Python reserved words for efficient lookup
RESERVED_WORDS = frozenset(list(keyword.kwlist) + list(keyword.softkwlist))


class DataType:
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ONE_OF = "oneOf"
    ANY_OF = "anyOf"


@functools.lru_cache(maxsize=256)
def class_name_titled(input_str: str) -> str:
    """
    Make the input string suitable for a class name
    """
    # Capitalize the first letter always
    input_str = input_str[:1].title() + input_str[1:]
    # Remove any bad characters with an empty space in a single pass
    trans_table = str.maketrans(".-_></{}", "        ")
    input_str = input_str.translate(trans_table)
    if " " in input_str:
        # Capitalize all the spaces
        input_str = input_str.title()
    # Remove all the spaces!
    return input_str.replace(" ", "")


@functools.lru_cache(maxsize=256)
def snake_case_prop(input_str: str) -> str:
    """
    Clean a property to not have invalid characters.
    Returns a "snake_case" version of the input string
    """
    # Sanitize: replace special chars and keep only valid Python identifier characters
    trans_table = str.maketrans({">": "", "<": "", "-": "_", ".": "_", "/": "_", " ": "_"})
    result = input_str.translate(trans_table)
    result = "".join(c for c in result if c.isalnum() or c == "_")

    # Handle empty or digit-starting identifiers
    if not result:
        return "EMPTY"
    if result[0].isdigit():
        result = f"_{result}"

    # Avoid Python reserved words
    if result.lower() in RESERVED_WORDS:
        result = result + "_"

    # Convert to snake_case unless already uppercase or no letters
    has_letters = any(c.isalpha() for c in result)
    if has_letters and not result.isupper():
        result = "".join(["_" + i.lower() if i.isupper() else i for i in result]).lstrip("_")

    return result


def _split_upper(s):
    res = re.findall(".[^A-Z]*", s)
    if len(res) > 1:
        return "_".join(res)
    return res[0]


def _snake_case(s):
    # Replace characters in a single pass
    trans_table = str.maketrans("/-.<>{} ", "________")
    s = s.translate(trans_table)
    s = _split_upper(s)
    return s[1:].lower() if s and s[0] == "_" else s.lower()


def get_func_name(operation: dict, path: str) -> str:
    if operation.get("operationId"):
        return _snake_case(operation["operationId"].split("__")[0])
    return _snake_case(path)


def get_type(t):
    t_type = t.get("type")
    t_format = t.get("format")

    if t_type == DataType.STRING:
        return "str"
    if t_type == DataType.INTEGER:
        return "int"
    if t_type == DataType.NUMBER:
        # Check formatting for a decimal type
        if t_format == "decimal":
            return "decimal.Decimal"
        return "float"
    if t_type == DataType.BOOLEAN:
        return "bool"
    if t_type == DataType.OBJECT:
        return "dict[str, typing.Any]"
    if t_type == DataType.ARRAY:
        inner_class = get_type(t.get("items"))
        return f"list[{inner_class}]"
    if ref := t.get("$ref"):
        # Handle component-based references
        if "#/components/schemas/" in ref:
            return f'"{class_name_titled(ref.replace("#/components/schemas/", ""))}"'
        else:
            # Path-based references are not supported - use typing.Any
            # These are inline schemas in the OpenAPI spec
            return "typing.Any"
    if t_type is None:
        # In this case, make it an "Any"
        return "typing.Any"
    # Note: enums have type {'type': '"EXAMPLE"'} so fall through here
    return t_type


def create_query_args(query_args: list[str]) -> str:
    return "?" + "&".join([f"{p}=" + "{" + p + "}" for p in query_args])


def create_query_args_with_mapping(sanitized_names: list[str], param_name_map: dict[str, str]) -> str:
    """
    Create query string using original API parameter names in the URL,
    but sanitized Python variable names in the f-string interpolation.

    Args:
        sanitized_names: List of sanitized Python parameter names
        param_name_map: Mapping from sanitized names to original API names

    Returns:
        Query string like "?originalName={sanitized_name}&other={other_var}"
    """
    parts = []
    for sanitized in sanitized_names:
        original = param_name_map.get(sanitized, sanitized)
        parts.append(f"{original}=" + "{" + sanitized + "}")
    return "?" + "&".join(parts)


def replace_path_parameters(url: str, param_name_map: dict[str, str]) -> str:
    """
    Replace path parameters in a URL with their sanitized Python variable names.

    For example: "/factions/{factionSymbol}" becomes "/factions/{faction_symbol}"
    when param_name_map = {"faction_symbol": "factionSymbol"}

    Args:
        url: The URL path with parameters in {braces}
        param_name_map: Mapping from sanitized names to original API names

    Returns:
        URL with path parameters replaced with sanitized names
    """
    # Create reverse mapping: original -> sanitized
    reverse_map = {original: sanitized for sanitized, original in param_name_map.items()}

    def replace_param(match):
        param_name = match.group(1)
        # If we have a sanitized version, use it; otherwise keep original
        return "{" + reverse_map.get(param_name, param_name) + "}"

    # Find all {paramName} in URL and replace with {sanitized_name}
    return re.sub(r"\{([^}]+)\}", replace_param, url)


@functools.lru_cache(maxsize=128)
def schema_ref(ref: str) -> str:
    return ref.replace("#/components/schemas/", "")


@functools.lru_cache(maxsize=128)
def param_ref(ref: str) -> str:
    return ref.replace("#/components/parameters/", "")


def get_param_from_ref(spec: openapi_core.Spec, param: dict) -> dict:
    ref = param.get("$ref", "")
    stripped_name = param_ref(ref)
    return spec["components"]["parameters"][stripped_name]


def get_schema_from_ref(spec: openapi_core.Spec, ref: str) -> dict:
    stripped_name = schema_ref(ref)
    return spec["components"]["schemas"][stripped_name]


def union_for_py_ver(union_items: list) -> str:
    minor = settings.PY_VERSION[1]
    if int(minor) >= 10:
        return " | ".join(union_items)
    else:
        return f"typing.Union[{', '.join(union_items)}]"
