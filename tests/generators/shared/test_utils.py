import pytest

from clientele.generators.shared import utils
from tests.generators.integration_utils import load_spec


@pytest.mark.parametrize(
    "input,expected_output",
    [
        ("Lowercase", "lowercase"),
        ("bad-string", "bad_string"),
        (">badstring", "badstring"),
        ("FooBarBazz", "foo_bar_bazz"),
        ("RETAIN_ALL_UPPER", "RETAIN_ALL_UPPER"),
        ("RETAINALLUPPER", "RETAINALLUPPER"),
        ("some.property.name", "some_property_name"),
        # Reserved words get an underscore suffix
        ("from", "from_"),
        # Empty (or empty after sanitization) inputs get a placeholder
        ("", "EMPTY"),
        ("!@#$%^&*()", "EMPTY"),
        # Digit-starting identifiers get an underscore prefix to stay valid Python
        ("123test", "_123test"),
        ("1_property", "_1_property"),
        ("123456", "_123456"),
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
        ({"type": "array"}, "list[typing.Any]"),
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


def test_class_name_titled_removes_special_chars():
    """Test class_name_titled removes various special characters."""
    result = utils.class_name_titled("test-name_with.special>chars")
    assert "-" not in result
    assert "_" not in result
    assert "." not in result
    assert ">" not in result


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


def test_get_type_with_oneof():
    """Test get_type handles oneOf schemas."""
    type_spec = {
        "oneOf": [
            {"type": "string"},
            {"type": "integer"},
        ]
    }
    result = utils.get_type(type_spec)
    # Should create a union type
    assert "str" in result
    assert "int" in result
    assert "|" in result or "Union" in result


def test_get_type_with_oneof_and_nullable():
    """Test get_type handles oneOf with nullable."""
    type_spec = {
        "oneOf": [
            {"type": "string"},
            {"type": "integer"},
        ],
        "nullable": True,
    }
    result = utils.get_type(type_spec)
    # Should wrap union in Optional
    assert "Optional" in result or "None" in result


def test_get_type_with_anyof():
    """Test get_type handles anyOf schemas."""
    type_spec = {
        "anyOf": [
            {"type": "string"},
            {"type": "boolean"},
        ]
    }
    result = utils.get_type(type_spec)
    # Should create a union type
    assert "str" in result
    assert "bool" in result
    assert "|" in result or "Union" in result


def test_get_type_with_anyof_and_nullable():
    """Test get_type handles anyOf with nullable."""
    type_spec = {
        "anyOf": [
            {"type": "string"},
            {"type": "integer"},
        ],
        "nullable": True,
    }
    result = utils.get_type(type_spec)
    # Should wrap union in Optional
    assert "Optional" in result or "None" in result


def test_get_type_with_allof():
    """Test get_type handles allOf schemas."""
    type_spec = {
        "allOf": [
            {"type": "string"},
        ]
    }
    result = utils.get_type(type_spec)
    # allOf should be handled, returning a type
    assert result is not None


def test_get_schema_from_ref_basic():
    """Test get_schema_from_ref retrieves schema from components/schemas."""
    spec = load_spec("best.json")

    # This spec should have some schemas we can reference
    if spec.components and spec.components.schemas:
        # Get first available schema key
        schema_keys = list(spec.components.schemas.keys())
        if schema_keys:
            first_key = schema_keys[0]
            ref = f"#/components/schemas/{first_key}"
            result = utils.get_schema_from_ref(spec=spec, ref=ref)

            # Should return a dict
            assert result is not None
            assert isinstance(result, dict)


def test_get_schema_from_ref_missing():
    """Test get_schema_from_ref with non-existent schema."""
    spec = load_spec("simple.json")

    result = utils.get_schema_from_ref(spec, "#/components/schemas/NonExistentSchema")

    assert result == {}


def test_get_param_from_ref_missing():
    """Test get_param_from_ref with non-existent parameter."""
    spec = load_spec("simple.json")

    param = {"$ref": "#/components/parameters/NonExistentParam"}
    result = utils.get_param_from_ref(spec, param)

    assert result == {}


def test_resolve_forward_refs_for_client():
    """Test that forward references are replaced with schemas module references."""
    assert utils.resolve_forward_refs_for_client('"ActionStatus"') == "schemas.ActionStatus"
    assert (
        utils.resolve_forward_refs_for_client('typing.Union["ActionStatus", None]')
        == "typing.Union[schemas.ActionStatus, None]"
    )
    assert utils.resolve_forward_refs_for_client('list["MyModel"]') == "list[schemas.MyModel]"
    assert utils.resolve_forward_refs_for_client("str") == "str"
    assert utils.resolve_forward_refs_for_client("int") == "int"


def test_strip_none_from_type():
    """Test stripping None/Optional wrapping from type strings."""
    assert utils.strip_none_from_type("typing.Optional[str]") == "str"
    assert utils.strip_none_from_type("typing.Union[schemas.ActionStatus, None]") == "schemas.ActionStatus"
    assert utils.strip_none_from_type("schemas.ActionStatus | None") == "schemas.ActionStatus"
    assert utils.strip_none_from_type("str") == "str"
    assert utils.strip_none_from_type("typing.Optional[list[str]]") == "list[str]"
    assert utils.strip_none_from_type("typing.Union[dict[str, int], None]") == "dict[str, int]"


def test_get_client_project_directory_path():
    """Test converting output directory to dot-notation path."""
    # Test basic conversion
    result = utils.get_client_project_directory_path("path/to/client")
    assert result == "path.to"

    # Test single level
    result = utils.get_client_project_directory_path("client")
    assert result == ""

    # Test with multiple levels
    result = utils.get_client_project_directory_path("a/b/c/d")
    assert result == "a.b.c"


def test_get_client_project_directory_path_edge_cases():
    """Test edge cases for path conversion."""
    # Empty string
    result = utils.get_client_project_directory_path("")
    assert result == ""

    # Path with trailing slash
    result = utils.get_client_project_directory_path("path/to/client/")
    assert result == "path.to.client"
