import pytest

from clientele.generators.standard import utils


@pytest.mark.parametrize(
    "input,expected_output",
    [
        ("Lowercase", "lowercase"),
        ("bad-string", "bad_string"),
        (">badstring", "badstring"),
        ("FooBarBazz", "foo_bar_bazz"),
        ("RETAIN_ALL_UPPER", "RETAIN_ALL_UPPER"),
        ("RETAINALLUPPER", "RETAINALLUPPER"),
    ],
)
def test_snake_case_prop(input, expected_output):
    assert utils.snake_case_prop(input_str=input) == expected_output


@pytest.mark.parametrize(
    "type_spec,expected_output",
    [
        ({"type": "string"}, "str"),
        ({"type": "boolean"}, "bool"),
        ({"type": "integer"}, "int"),
        ({"type": "number"}, "float"),
        ({"type": "number", "format": "decimal"}, "decimal.Decimal"),
        ({"type": "object"}, "dict[str, typing.Any]"),
        ({"type": "array", "items": {"type": "string"}}, "list[str]"),
        ({"type": "array", "items": {"type": "integer"}}, "list[int]"),
        ({"type": "array", "items": {"type": "number"}}, "list[float]"),
        ({}, "typing.Any"),
    ],
)
def test_get_type(type_spec, expected_output):
    assert utils.get_type(type_spec) == expected_output
