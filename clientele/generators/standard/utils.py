import functools
import keyword
import re

from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele import settings
from clientele.generators import cicerone_compat

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

    # Track if we need to prepend underscore for digit-starting identifier
    prepend_underscore = result[0].isdigit()
    if prepend_underscore:
        result = f"_{result}"

    # Avoid Python reserved words
    if result.lower() in RESERVED_WORDS:
        result = result + "_"

    # Convert to snake_case unless already uppercase or no letters
    has_letters = any(c.isalpha() for c in result)
    if has_letters and not result.isupper():
        result = "".join(["_" + i.lower() if i.isupper() else i for i in result])
        # Only strip leading underscores if we didn't intentionally add one for digit-starting identifier
        if not prepend_underscore:
            result = result.lstrip("_")

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
    t_nullable = t.get("nullable", False)

    # Handle oneOf - creates a union type
    if one_of := t.get("oneOf"):
        union_types = [get_type(schema) for schema in one_of]
        result = union_for_py_ver(union_types)
        # Apply nullable wrapper if needed
        if t_nullable:
            return f"typing.Optional[{result}]"
        return result

    # Handle anyOf - creates a union type
    if any_of := t.get("anyOf"):
        union_types = [get_type(schema) for schema in any_of]
        result = union_for_py_ver(union_types)
        # Apply nullable wrapper if needed
        if t_nullable:
            return f"typing.Optional[{result}]"
        return result

    # Handle regular types
    base_type = None
    if t_type == DataType.STRING:
        base_type = "str"
    elif t_type == DataType.INTEGER:
        base_type = "int"
    elif t_type == DataType.NUMBER:
        # Check formatting for a decimal type
        if t_format == "decimal":
            base_type = "decimal.Decimal"
        else:
            base_type = "float"
    elif t_type == DataType.BOOLEAN:
        base_type = "bool"
    elif t_type == DataType.OBJECT:
        base_type = "dict[str, typing.Any]"
    elif t_type == DataType.ARRAY:
        inner_class = get_type(t.get("items"))
        base_type = f"list[{inner_class}]"
    elif ref := t.get("$ref"):
        # Handle component-based references
        if "#/components/schemas/" in ref:
            # Use forward reference (quoted string) for Pydantic model properties
            # This allows classes to reference other classes that may be defined later
            base_type = f'"{class_name_titled(ref.replace("#/components/schemas/", ""))}"'
        else:
            # Path-based references are not supported - use typing.Any
            # These are inline schemas in the OpenAPI spec
            base_type = "typing.Any"
    elif t_type is None:
        # In this case, make it an "Any"
        base_type = "typing.Any"
    else:
        # Note: enums have type {'type': '"EXAMPLE"'} so fall through here
        base_type = t_type

    # Apply nullable wrapper if the type is nullable
    if base_type and t_nullable:
        return f"typing.Optional[{base_type}]"

    return base_type if base_type else "typing.Any"


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


def get_param_from_ref(spec: cicerone_openapi_spec.OpenAPISpec, param: dict) -> dict:
    """Get parameter from reference and convert to dict using centralized compat layer."""
    ref = param.get("$ref", "")
    stripped_name = param_ref(ref)
    param_obj = spec.components.parameters.get(stripped_name)
    if param_obj is None:
        return {}
    return cicerone_compat.parameter_to_dict(param_obj)


def get_schema_from_ref(spec: cicerone_openapi_spec.OpenAPISpec, ref: str) -> dict:
    """Get schema from reference and convert to dict using centralized compat layer."""
    stripped_name = schema_ref(ref)
    schema_obj = spec.components.schemas.get(stripped_name)
    if schema_obj is None:
        return {}
    return cicerone_compat.schema_to_dict(schema_obj)


def union_for_py_ver(union_items: list) -> str:
    """
    Create a union type string based on Python version and content.
    Uses typing.Union if any items are forward references (quoted strings),
    otherwise uses modern | syntax for Python 3.10+
    """
    # Check if any items are forward references (quoted strings)
    has_forward_ref = any(isinstance(item, str) and item.startswith('"') for item in union_items)

    # Always use typing.Union for forward references or Python < 3.10
    minor = settings.PY_VERSION[1]
    if has_forward_ref or int(minor) < 10:
        return f"typing.Union[{', '.join(union_items)}]"
    else:
        return " | ".join(union_items)


def remove_forward_ref_quotes(type_string: str) -> str:
    """
    Remove quotes from forward references in a type string.

    Converts 'list["SomeType"]' to 'list[SomeType]'
    Converts 'dict[str, "SomeType"]' to 'dict[str, SomeType]'

    This is used for type aliases where forward references are not needed
    because all types are defined in the same module and model_rebuild() is called.
    """
    import re

    # Replace quoted strings within type annotations
    # Pattern: matches quoted strings that are type names (alphanumeric + underscore)
    return re.sub(r'"([A-Za-z_][A-Za-z0-9_]*)"', r"\1", type_string)
