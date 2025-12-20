import functools
import re

import openapi_core

from clientele import settings


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
    # Replace characters in a single pass using translate
    trans_table = str.maketrans({">": "", "<": "", "-": "_", ".": "_", "/": "_", " ": "_"})
    input_str = input_str.translate(trans_table)

    # Remove any characters that aren't valid in Python identifiers
    # Keep only alphanumeric and underscore
    input_str = "".join(c for c in input_str if c.isalnum() or c == "_")

    # If the result is empty or starts with a digit, prefix with underscore
    if not input_str:
        input_str = "EMPTY"
    elif input_str[0].isdigit():
        input_str = f"_{input_str}"

    # python keywords need to be converted
    reserved_words = [
        "from",
        "import",
        "class",
        "def",
        "return",
        "if",
        "else",
        "elif",
        "for",
        "while",
        "try",
        "except",
        "finally",
        "with",
        "as",
        "pass",
        "break",
        "continue",
        "raise",
        "assert",
        "yield",
        "lambda",
        "global",
        "nonlocal",
        "del",
        "and",
        "or",
        "not",
        "in",
        "is",
        "None",
        "True",
        "False",
    ]
    if input_str.lower() in reserved_words:
        input_str = input_str + "_"

    # Retain all-uppercase strings or strings with only underscores/digits, otherwise convert to camel case
    # Check if the string has any letters and if they're all uppercase
    has_letters = any(c.isalpha() for c in input_str)
    if not has_letters or input_str.isupper():
        # Keep as-is (already uppercase or no letters)
        pass
    else:
        # Convert to snake_case
        input_str = "".join(["_" + i.lower() if i.isupper() else i for i in input_str]).lstrip("_")

    return input_str


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
        return f'"{class_name_titled(ref.replace("#/components/schemas/", ""))}"'
    if t_type is None:
        # In this case, make it an "Any"
        return "typing.Any"
    # Note: enums have type {'type': '"EXAMPLE"'} so fall through here
    return t_type


def create_query_args(query_args: list[str]) -> str:
    return "?" + "&".join([f"{p}=" + "{" + p + "}" for p in query_args])


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
