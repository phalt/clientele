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


@pytest.mark.parametrize(
    "input_str,expected_output",
    [
        ("hello", "Hello"),
        ("hello-world", "HelloWorld"),
        ("hello_world", "HelloWorld"),
        ("hello.world", "HelloWorld"),
        ("hello>world<test", "HelloWorldTest"),
        ("hello/world", "HelloWorld"),
        ("already-Titled", "AlreadyTitled"),
    ],
)
def test_class_name_titled(input_str, expected_output):
    """Test converting strings to title case class names."""
    assert utils.class_name_titled(input_str) == expected_output


def test_snake_case_prop_reserved_words():
    """Test that reserved words get an underscore suffix."""
    assert utils.snake_case_prop("from") == "from_"


def test_get_type_with_array_of_objects():
    """Test type conversion for arrays of objects."""
    type_spec = {"type": "array", "items": {"type": "object"}}
    result = utils.get_type(type_spec)
    assert "list" in result and "dict" in result


def test_get_type_with_nested_arrays():
    """Test type conversion for nested arrays."""
    type_spec = {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
    result = utils.get_type(type_spec)
    # Should handle nested structure
    assert "list" in result


def test_get_type_with_enum():
    """Test type conversion with enum values."""
    type_spec = {"type": "string", "enum": ["ONE", "TWO", "THREE"]}
    result = utils.get_type(type_spec)
    # Should still return a string type
    assert result == "str"


def test_snake_case_prop_with_dots():
    """Test snake_case_prop converts dots to underscores."""
    assert utils.snake_case_prop("some.property.name") == "some_property_name"


def test_class_name_titled_removes_special_chars():
    """Test class_name_titled removes various special characters."""
    result = utils.class_name_titled("test-name_with.special>chars")
    assert "-" not in result
    assert "_" not in result
    assert "." not in result
    assert ">" not in result


def test_split_upper_single_char():
    """Test _split_upper with single character."""
    from clientele.generators.standard.utils import _split_upper

    result = _split_upper("A")
    assert result == "A"


def test_split_upper_multiple_uppercase():
    """Test _split_upper with multiple uppercase letters."""
    from clientele.generators.standard.utils import _split_upper

    result = _split_upper("HelloWorld")
    assert "_" in result or result == "HelloWorld"
