"""Tests for the cicerone_compat module."""

from unittest.mock import Mock

from clientele.generators import cicerone_compat
from clientele.generators.cicerone_compat import normalize_openapi_31_schema, normalize_openapi_31_spec


def test_schema_to_dict_with_dict_input():
    """Test schema_to_dict returns dict as-is (line 37)."""
    input_dict = {"type": "string", "format": "email"}
    result = cicerone_compat.schema_to_dict(input_dict)
    assert result == input_dict
    assert result is input_dict  # Should be the same object


def test_parameter_to_dict_with_ref():
    """Test parameter_to_dict handles $ref (line 105)."""
    mock_param = Mock()
    mock_param.ref = "#/components/parameters/TestParam"

    result = cicerone_compat.parameter_to_dict(mock_param)

    assert result == {"$ref": "#/components/parameters/TestParam"}


def test_parameter_to_dict_with_dict_input():
    """Test parameter_to_dict returns dict as-is (line 100)."""
    input_dict = {"$ref": "#/components/parameters/TestParam"}
    result = cicerone_compat.parameter_to_dict(input_dict)
    assert result == input_dict
    assert result is input_dict


def test_request_body_to_dict_with_content():
    """Test request_body_to_dict handles content properly (lines 133-142)."""
    # Create mock objects for the request body
    mock_schema = Mock()
    mock_schema.__pydantic_extra__ = {}
    mock_schema.type = "object"
    mock_schema.all_of = None
    mock_schema.one_of = None
    mock_schema.any_of = None
    mock_schema.properties = None
    mock_schema.required = None
    mock_schema.format = None
    mock_schema.items = None
    mock_schema.title = None

    mock_media_type = Mock()
    mock_media_type.schema_ = mock_schema

    mock_request_body = Mock()
    mock_request_body.content = {"application/json": mock_media_type}

    result = cicerone_compat.request_body_to_dict(mock_request_body)

    assert "content" in result
    assert "application/json" in result["content"]
    assert "schema" in result["content"]["application/json"]


def test_request_body_to_dict_with_dict_input():
    """Test request_body_to_dict returns dict as-is (line 130)."""
    input_dict = {"content": {"application/json": {"schema": {"type": "object"}}}}
    result = cicerone_compat.request_body_to_dict(input_dict)
    assert result == input_dict
    assert result is input_dict


def test_response_to_dict_with_description_and_content():
    """Test response_to_dict handles description and content (lines 159-171)."""
    # Create mock objects for the response
    mock_schema = Mock()
    mock_schema.__pydantic_extra__ = {}
    mock_schema.type = "object"
    mock_schema.all_of = None
    mock_schema.one_of = None
    mock_schema.any_of = None
    mock_schema.properties = None
    mock_schema.required = None
    mock_schema.format = None
    mock_schema.items = None
    mock_schema.title = None

    mock_media_type = Mock()
    mock_media_type.schema_ = mock_schema

    mock_response = Mock()
    mock_response.description = "Success response"
    mock_response.content = {"application/json": mock_media_type}

    result = cicerone_compat.response_to_dict(mock_response)

    assert result["description"] == "Success response"
    assert "content" in result
    assert "application/json" in result["content"]
    assert "schema" in result["content"]["application/json"]


def test_response_to_dict_with_dict_input():
    """Test response_to_dict returns dict as-is (line 156)."""
    input_dict = {"description": "Test", "content": {}}
    result = cicerone_compat.response_to_dict(input_dict)
    assert result == input_dict
    assert result is input_dict


def test_operation_to_dict_with_dict_input():
    """Test operation_to_dict returns dict as-is (line 186)."""
    input_dict = {"operationId": "test_operation", "summary": "Test"}
    result = cicerone_compat.operation_to_dict(input_dict)
    assert result == input_dict
    assert result is input_dict


def test_path_item_to_operations_dict_with_path_level_parameters():
    """Test path_item_to_operations_dict handles path-level parameters (lines 259-264)."""
    # Create mock operation
    mock_operation = Mock()
    mock_operation.operation_id = "test_get"
    mock_operation.summary = "Test operation"
    mock_operation.description = None
    mock_operation.parameters = []
    mock_operation.responses = {}
    mock_operation.__pydantic_extra__ = {}
    mock_operation.request_body = None

    # Create mock schema for parameter
    mock_schema = Mock()
    mock_schema.__pydantic_extra__ = {}
    mock_schema.type = "string"
    mock_schema.all_of = None
    mock_schema.one_of = None
    mock_schema.any_of = None
    mock_schema.properties = None
    mock_schema.required = None
    mock_schema.format = None
    mock_schema.items = None
    mock_schema.title = None

    # Create mock parameter
    mock_param = Mock()
    mock_param.name = "id"
    mock_param.in_ = "path"
    mock_param.required = True
    mock_param.schema_ = mock_schema
    mock_param.ref = None

    # Create mock path item with path-level parameters
    mock_path_item = Mock()
    mock_path_item.operations = {"get": mock_operation}
    mock_path_item.parameters = [mock_param]

    result = cicerone_compat.path_item_to_operations_dict(mock_path_item)

    assert "get" in result
    assert "parameters" in result
    assert len(result["parameters"]) == 1


def test_path_item_to_operations_dict_with_pydantic_extra_parameters():
    """Test path_item_to_operations_dict handles parameters in pydantic extra (lines 262-264)."""
    # Create mock operation
    mock_operation = Mock()
    mock_operation.operation_id = "test_get"
    mock_operation.summary = "Test operation"
    mock_operation.description = None
    mock_operation.parameters = []
    mock_operation.responses = {}
    mock_operation.__pydantic_extra__ = {}
    mock_operation.request_body = None

    # Create mock path item WITHOUT direct parameters attribute
    mock_path_item = Mock(spec=[])
    mock_path_item.operations = {"get": mock_operation}
    # Add __pydantic_extra__ with parameters
    mock_path_item.__pydantic_extra__ = {"parameters": [{"name": "id", "in": "path", "required": True}]}

    result = cicerone_compat.path_item_to_operations_dict(mock_path_item)

    assert "get" in result
    assert "parameters" in result
    assert result["parameters"] == [{"name": "id", "in": "path", "required": True}]


def test_get_pydantic_extra_with_no_extra():
    """Test get_pydantic_extra when object has no extra fields."""

    # Create a plain object without __pydantic_extra__
    class PlainObject:
        pass

    obj = PlainObject()

    result = cicerone_compat.get_pydantic_extra(obj, "test_key")

    assert result is None


def test_get_pydantic_extra_with_empty_extra():
    """Test get_pydantic_extra when extra dict is empty."""
    obj = Mock()
    obj.__pydantic_extra__ = {}

    result = cicerone_compat.get_pydantic_extra(obj, "test_key")

    assert result is None


def test_get_pydantic_extra_with_key_present():
    """Test get_pydantic_extra when key is present in extra."""
    obj = Mock()
    obj.__pydantic_extra__ = {"test_key": "test_value"}

    result = cicerone_compat.get_pydantic_extra(obj, "test_key")

    assert result == "test_value"


def test_normalize_openapi_31_schema_only_null_type():
    """Test schema with only null type becomes nullable string."""
    schema = {"type": ["null"]}
    result = normalize_openapi_31_schema(schema)
    assert result["type"] == "string"
    assert result["nullable"] is True


def test_normalize_openapi_31_schema_preserves_existing_nullable():
    """Test that existing nullable: true is preserved."""
    schema = {"type": "string", "nullable": True}
    result = normalize_openapi_31_schema(schema)
    assert result["nullable"] is True


def test_normalize_openapi_31_schema_items():
    """Test normalization of array items."""
    schema = {"type": "array", "items": {"type": ["string", "null"]}}
    result = normalize_openapi_31_schema(schema)
    assert result["items"]["type"] == "string"
    assert result["items"]["nullable"] is True


def test_normalize_openapi_31_schema_allof():
    """Test normalization of allOf schemas."""
    schema = {"allOf": [{"type": ["string", "null"]}, {"minLength": 1}]}
    result = normalize_openapi_31_schema(schema)
    assert result["allOf"][0]["type"] == "string"
    assert result["allOf"][0]["nullable"] is True


def test_normalize_openapi_31_schema_oneof():
    """Test normalization of oneOf schemas."""
    schema = {"oneOf": [{"type": ["integer", "null"]}, {"type": "string"}]}
    result = normalize_openapi_31_schema(schema)
    assert result["oneOf"][0]["type"] == "integer"
    assert result["oneOf"][0]["nullable"] is True


def test_normalize_openapi_31_schema_anyof():
    """Test normalization of anyOf schemas."""
    schema = {"anyOf": [{"type": ["boolean", "null"]}, {"type": "number"}]}
    result = normalize_openapi_31_schema(schema)
    assert result["anyOf"][0]["type"] == "boolean"
    assert result["anyOf"][0]["nullable"] is True


def test_normalize_openapi_31_spec_components_schemas():
    """Test normalization of schemas in components."""
    spec = {
        "openapi": "3.1.0",
        "components": {"schemas": {"NullableString": {"type": ["string", "null"]}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["components"]["schemas"]["NullableString"]["type"] == "string"
    assert result["components"]["schemas"]["NullableString"]["nullable"] is True


def test_normalize_openapi_31_spec_request_body():
    """Test normalization of request body schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "post": {"requestBody": {"content": {"application/json": {"schema": {"type": ["string", "null"]}}}}}
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    schema = result["paths"]["/test"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert schema["type"] == "string"
    assert schema["nullable"] is True


def test_normalize_openapi_31_spec_response_schemas():
    """Test normalization of response schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "get": {
                    "responses": {"200": {"content": {"application/json": {"schema": {"type": ["integer", "null"]}}}}}
                }
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    schema = result["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "integer"
    assert schema["nullable"] is True


def test_normalize_openapi_31_spec_parameter_schemas():
    """Test normalization of parameter schemas."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": {
                "get": {
                    "parameters": [
                        {
                            "name": "test_param",
                            "in": "query",
                            "schema": {"type": ["boolean", "null"]},
                        }
                    ]
                }
            }
        },
    }
    result = normalize_openapi_31_spec(spec)
    param_schema = result["paths"]["/test"]["get"]["parameters"][0]["schema"]
    assert param_schema["type"] == "boolean"
    assert param_schema["nullable"] is True


def test_normalize_openapi_31_spec_non_dict_path_item():
    """Test that non-dict path items are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {
            "/test": "not a dict",
        },
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"] == "not a dict"


def test_normalize_openapi_31_spec_dollar_prefixed_keys():
    """Test that $-prefixed keys (like $ref) are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"$ref": "#/components/paths/TestPath"}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["$ref"] == "#/components/paths/TestPath"


def test_normalize_openapi_31_spec_non_dict_response():
    """Test that non-dict responses are skipped."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"get": {"responses": {"200": "not a dict"}}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["get"]["responses"]["200"] == "not a dict"


def test_normalize_openapi_31_spec_non_dict_parameter():
    """Test that non-dict parameters are handled."""
    spec = {
        "openapi": "3.1.0",
        "paths": {"/test": {"get": {"parameters": ["not a dict"]}}},
    }
    result = normalize_openapi_31_spec(spec)
    assert result["paths"]["/test"]["get"]["parameters"][0] == "not a dict"
