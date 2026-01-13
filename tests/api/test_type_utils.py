"""Tests for clientele.api.type_utils module."""

import typing

import pytest
from pydantic import BaseModel, ValidationError

from clientele.api import type_utils


class SampleModel(BaseModel):
    name: str
    value: int


class SampleTypedDict(typing.TypedDict):
    name: str
    value: int


class TestIsPydanticModel:
    def test_is_pydantic_model_with_basemodel(self):
        """Test that BaseModel subclasses are recognized."""
        assert type_utils.is_pydantic_model(SampleModel) is True

    def test_is_pydantic_model_with_instance(self):
        """Test that BaseModel instances are NOT recognized (must be class)."""
        instance = SampleModel(name="test", value=42)
        assert type_utils.is_pydantic_model(instance) is False

    def test_is_pydantic_model_with_dict(self):
        """Test that dict is not a Pydantic model."""
        assert type_utils.is_pydantic_model(dict) is False

    def test_is_pydantic_model_with_str(self):
        """Test that str is not a Pydantic model."""
        assert type_utils.is_pydantic_model(str) is False


class TestIsTypedDict:
    def test_is_typeddict_with_typeddict(self):
        """Test that TypedDict classes are recognized."""
        assert type_utils.is_typeddict(SampleTypedDict) is True

    def test_is_typeddict_with_dict(self):
        """Test that regular dict is not a TypedDict."""
        assert type_utils.is_typeddict(dict) is False

    def test_is_typeddict_with_pydantic_model(self):
        """Test that Pydantic models are not TypedDicts."""
        assert type_utils.is_typeddict(SampleModel) is False


class TestIsStreamingType:
    def test_is_streaming_type_with_async_iterator(self):
        """Test AsyncIterator is recognized as streaming type."""
        annotation = typing.AsyncIterator[str]
        assert type_utils.is_streaming_type(annotation) is True

    def test_is_streaming_type_with_iterator(self):
        """Test Iterator is recognized as streaming type."""
        annotation = typing.Iterator[str]
        assert type_utils.is_streaming_type(annotation) is True

    def test_is_streaming_type_with_list(self):
        """Test that List is not a streaming type."""
        annotation = typing.List[str]
        assert type_utils.is_streaming_type(annotation) is False

    def test_is_streaming_type_with_plain_type(self):
        """Test that plain types are not streaming types."""
        assert type_utils.is_streaming_type(str) is False


class TestGetStreamingInnerType:
    def test_get_streaming_inner_type_async_iterator(self):
        """Test extracting inner type from AsyncIterator."""
        annotation = typing.AsyncIterator[str]
        assert type_utils.get_streaming_inner_type(annotation) is str

    def test_get_streaming_inner_type_iterator(self):
        """Test extracting inner type from Iterator."""
        annotation = typing.Iterator[int]
        assert type_utils.get_streaming_inner_type(annotation) is int

    def test_get_streaming_inner_type_pydantic_model(self):
        """Test extracting Pydantic model from AsyncIterator."""
        annotation = typing.AsyncIterator[SampleModel]
        assert type_utils.get_streaming_inner_type(annotation) is SampleModel

    def test_get_streaming_inner_type_non_streaming(self):
        """Test that non-streaming types return None."""
        assert type_utils.get_streaming_inner_type(str) is None

    def test_get_streaming_inner_type_without_args(self):
        """Test streaming type without type args returns None."""
        # This is a tricky case - typing.AsyncIterator without [T]
        # In Python 3.9+, this might not be possible, but we test the logic
        annotation = typing.AsyncIterator
        result = type_utils.get_streaming_inner_type(annotation)
        # The function checks is_streaming_type first, which might return False
        # or it returns None because args is empty
        assert result is None


class TestIsAsyncStreamingType:
    def test_is_async_streaming_type_async_iterator(self):
        """Test AsyncIterator is recognized as async streaming."""
        annotation = typing.AsyncIterator[str]
        assert type_utils.is_async_streaming_type(annotation) is True

    def test_is_async_streaming_type_async_generator(self):
        """Test AsyncGenerator is recognized as async streaming."""
        annotation = typing.AsyncGenerator[str, None]
        assert type_utils.is_async_streaming_type(annotation) is True

    def test_is_async_streaming_type_iterator(self):
        """Test Iterator is NOT async streaming."""
        annotation = typing.Iterator[str]
        assert type_utils.is_async_streaming_type(annotation) is False

    def test_is_async_streaming_type_plain_type(self):
        """Test plain types are not async streaming."""
        assert type_utils.is_async_streaming_type(str) is False


class TestValidateTypedDict:
    def test_validate_typeddict_with_valid_dict(self):
        """Test validating a valid dict for TypedDict."""
        payload = {"name": "test", "value": 42}
        result = type_utils.validate_typeddict(SampleTypedDict, payload)
        assert result == payload

    def test_validate_typeddict_with_non_dict(self):
        """Test that non-dict payload raises TypeError."""
        with pytest.raises(TypeError, match="Expected dict for TypedDict"):
            type_utils.validate_typeddict(SampleTypedDict, "not a dict")

    def test_validate_typeddict_with_none(self):
        """Test that None raises TypeError."""
        with pytest.raises(TypeError, match="Expected dict for TypedDict"):
            type_utils.validate_typeddict(SampleTypedDict, None)

    def test_validate_typeddict_with_list(self):
        """Test that list raises TypeError."""
        with pytest.raises(TypeError, match="Expected dict for TypedDict"):
            type_utils.validate_typeddict(SampleTypedDict, [1, 2, 3])


class TestValidateModel:
    def test_validate_model_with_valid_dict(self):
        """Test validating dict into Pydantic model."""
        payload = {"name": "test", "value": 42}
        result = type_utils.validate_model(SampleModel, payload)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42

    def test_validate_model_with_invalid_dict(self):
        """Test that invalid dict raises ValidationError."""
        payload = {"name": "test", "value": "not an int"}
        with pytest.raises(ValidationError):
            type_utils.validate_model(SampleModel, payload)

    def test_validate_model_with_missing_field(self):
        """Test that missing required field raises ValidationError."""
        payload = {"name": "test"}  # Missing 'value'
        with pytest.raises(ValidationError):
            type_utils.validate_model(SampleModel, payload)

    def test_validate_model_with_extra_fields(self):
        """Test that extra fields are handled correctly."""
        payload = {"name": "test", "value": 42, "extra": "ignored"}
        result = type_utils.validate_model(SampleModel, payload)
        assert isinstance(result, SampleModel)
        assert result.name == "test"
        assert result.value == 42
        # Extra field should be ignored by default in Pydantic
