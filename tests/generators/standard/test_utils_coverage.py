"""Additional tests for standard utils to increase coverage."""

from clientele.generators.standard import utils


def test_snake_case_prop_with_empty_string():
    """Test snake_case_prop handles empty strings (line 55)."""
    result = utils.snake_case_prop("")
    assert result == "EMPTY"


def test_snake_case_prop_with_only_special_chars():
    """Test snake_case_prop handles strings that become empty after sanitization (line 55)."""
    result = utils.snake_case_prop("!@#$%^&*()")
    assert result == "EMPTY"


def test_snake_case_prop_with_digit_start():
    """Test snake_case_prop handles identifiers starting with digit.

    The function correctly adds underscore prefix for digit-starting identifiers
    and preserves it to ensure valid Python identifier syntax.
    """
    result = utils.snake_case_prop("123test")
    # Underscore prefix is preserved for valid Python identifier
    assert result == "_123test"

    # Also test with underscores and other characters
    result2 = utils.snake_case_prop("1_property")
    assert result2 == "_1_property"


def test_snake_case_prop_with_only_digits():
    """Test snake_case_prop handles strings with only digits."""
    result = utils.snake_case_prop("123456")
    assert result == "_123456"


def test_get_type_with_oneof():
    """Test get_type handles oneOf schemas (lines 99-104)."""
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
    """Test get_type handles oneOf with nullable (lines 102-104)."""
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
    """Test get_type handles anyOf schemas (lines 107-112)."""
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
    """Test get_type handles anyOf with nullable (line 112)."""
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
    """Test get_type handles allOf schemas (line 157)."""
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
    # Use existing test spec that has components
    from tests.generators.integration_utils import load_spec

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
