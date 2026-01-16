"""Tests for clientele.api.requests module."""

import inspect
import typing

import pytest
from pydantic import BaseModel

from clientele.api import requests
from clientele.http import response as http_response


class SampleModel(BaseModel):
    name: str
    value: int


class ErrorModel(BaseModel):
    error: str
    code: int


class SampleTypedDict(typing.TypedDict):
    name: str
    value: int


class TestValidateResultParameter:
    def test_validate_result_parameter_missing(self):
        """Test that missing result parameter raises TypeError."""

        def func_without_result():
            pass

        sig = inspect.signature(func_without_result)
        type_hints = typing.get_type_hints(func_without_result)

        with pytest.raises(TypeError, match="must have a 'result' parameter"):
            requests.validate_result_parameter(func_without_result, sig, type_hints)

    def test_validate_result_parameter_no_annotation(self):
        """Test that result parameter without annotation raises TypeError."""

        def func_no_annotation(result):
            return result

        sig = inspect.signature(func_no_annotation)
        type_hints = {}

        with pytest.raises(TypeError, match="lacks a type annotation"):
            requests.validate_result_parameter(func_no_annotation, sig, type_hints)

    def test_validate_result_parameter_valid(self):
        """Test that valid result parameter passes validation."""

        def func_valid(result: dict) -> dict:
            return result

        sig = inspect.signature(func_valid)
        type_hints = typing.get_type_hints(func_valid)

        # Should not raise
        requests.validate_result_parameter(func_valid, sig, type_hints)

    def test_validate_result_parameter_streaming_valid(self):
        """Test streaming validation with AsyncIterator."""

        async def func_stream(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
            return result

        sig = inspect.signature(func_stream)
        type_hints = typing.get_type_hints(func_stream, include_extras=True)

        # Should not raise
        requests.validate_result_parameter(func_stream, sig, type_hints, expect_streaming=True)

    def test_validate_result_parameter_streaming_invalid_type(self):
        """Test that non-streaming type raises error when expect_streaming=True."""

        async def func_not_stream(result: dict) -> dict:
            return result

        sig = inspect.signature(func_not_stream)
        type_hints = typing.get_type_hints(func_not_stream)

        with pytest.raises(TypeError, match="must have a streaming result type"):
            requests.validate_result_parameter(func_not_stream, sig, type_hints, expect_streaming=True)

    def test_validate_result_parameter_streaming_no_inner_type(self):
        """Test that AsyncIterator without inner type raises error."""

        async def func_no_inner(result: typing.AsyncIterator) -> typing.AsyncIterator:
            return result

        sig = inspect.signature(func_no_inner)
        type_hints = typing.get_type_hints(func_no_inner, include_extras=True)

        with pytest.raises(TypeError, match="no inner type specified"):
            requests.validate_result_parameter(func_no_inner, sig, type_hints, expect_streaming=True)

    def test_validate_result_parameter_async_func_with_iterator(self):
        """Test async function with Iterator (should be AsyncIterator) raises error."""

        async def func_wrong_type(result: typing.Iterator[str]) -> typing.Iterator[str]:
            return result

        sig = inspect.signature(func_wrong_type)
        type_hints = typing.get_type_hints(func_wrong_type, include_extras=True)

        with pytest.raises(TypeError, match="must use AsyncIterator, not Iterator"):
            requests.validate_result_parameter(func_wrong_type, sig, type_hints, expect_streaming=True)

    def test_validate_result_parameter_sync_func_with_async_iterator(self):
        """Test sync function with AsyncIterator (should be Iterator) raises error."""

        def func_wrong_type(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
            return result

        sig = inspect.signature(func_wrong_type)
        type_hints = typing.get_type_hints(func_wrong_type, include_extras=True)

        with pytest.raises(TypeError, match="must use Iterator, not AsyncIterator"):
            requests.validate_result_parameter(func_wrong_type, sig, type_hints, expect_streaming=True)


class TestBuildRequestContext:
    def test_build_request_context_basic(self):
        """Test building basic request context."""

        def func(result: dict) -> dict:
            return result

        context = requests.build_request_context("GET", "/test", func)

        assert context.method == "GET"
        assert context.path_template == "/test"
        assert context.func == func
        assert context.streaming is False
        assert context.response_map is None
        assert context.response_parser is None

    def test_build_request_context_with_response_map(self):
        """Test building request context with response_map."""

        def func(result: SampleModel | ErrorModel) -> SampleModel | ErrorModel:
            return result

        response_map = {200: SampleModel, 404: ErrorModel}
        context = requests.build_request_context("GET", "/test", func, response_map=response_map)

        assert context.response_map == response_map

    def test_build_request_context_streaming(self):
        """Test building streaming request context."""

        async def func(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
            return result

        context = requests.build_request_context("GET", "/stream", func, streaming=True)

        assert context.streaming is True

    def test_build_request_context_streaming_with_response_map_raises(self):
        """Test that streaming with response_map raises error."""

        async def func(result: typing.AsyncIterator[str]) -> typing.AsyncIterator[str]:
            return result

        with pytest.raises(TypeError, match="cannot use response_map"):
            requests.build_request_context("GET", "/stream", func, response_map={200: SampleModel}, streaming=True)

    def test_build_request_context_both_response_map_and_parser_raises(self):
        """Test that having both response_map and response_parser raises error."""

        def func(result: SampleModel) -> SampleModel:
            return result

        def parser(response: http_response.Response) -> SampleModel:
            return SampleModel(name="test", value=1)

        with pytest.raises(TypeError, match="cannot have both"):
            requests.build_request_context(
                "GET", "/test", func, response_map={200: SampleModel}, response_parser=parser
            )

    def test_build_request_context_forward_reference_fallback(self):
        """Test handling of forward references that can't be resolved."""

        # Create a function with forward reference annotation using typing.ForwardRef
        def func(result: dict) -> dict:
            return result

        # Manually set __annotations__ to simulate forward reference that can't be resolved
        func.__annotations__ = {"result": "SomeForwardRef", "return": "SomeForwardRef"}

        # This should fall back to using __annotations__ when get_type_hints raises NameError
        context = requests.build_request_context("GET", "/test", func)

        assert context.type_hints is not None
        assert "result" in context.type_hints


class TestValidateResponseMap:
    def test_validate_response_map_valid(self):
        """Test validating valid response_map."""

        def func(result: SampleModel | ErrorModel) -> SampleModel | ErrorModel:
            return result

        type_hints = typing.get_type_hints(func)
        response_map = {200: SampleModel, 404: ErrorModel}

        # Should not raise
        requests._validate_response_map(response_map, func, type_hints)

    def test_validate_response_map_invalid_status_code(self):
        """Test that invalid status code raises ValueError."""

        def func(result: SampleModel) -> SampleModel:
            return result

        type_hints = typing.get_type_hints(func)
        response_map = {999: SampleModel}  # Invalid status code

        with pytest.raises(ValueError, match="Invalid status code 999"):
            requests._validate_response_map(response_map, func, type_hints)

    def test_validate_response_map_non_pydantic_model(self):
        """Test that non-Pydantic model in response_map raises ValueError."""

        def func(result: str) -> str:
            return result

        type_hints = typing.get_type_hints(func)
        response_map = {200: str}  # Not a Pydantic model or TypedDict

        with pytest.raises(ValueError, match="must be a Pydantic BaseModel subclass or TypedDict"):
            requests._validate_response_map(response_map, func, type_hints)

    def test_validate_response_map_model_not_in_result_type(self):
        """Test that model not in result type raises ValueError."""

        def func(result: SampleModel) -> SampleModel:
            return result

        type_hints = typing.get_type_hints(func)
        response_map = {200: SampleModel, 404: ErrorModel}  # ErrorModel not in result type

        with pytest.raises(ValueError, match="is not in the 'result' parameter's type annotation"):
            requests._validate_response_map(response_map, func, type_hints)

    def test_validate_response_map_with_typeddict(self):
        """Test response_map with TypedDict models."""

        def func(result: SampleTypedDict) -> SampleTypedDict:
            return result

        type_hints = typing.get_type_hints(func)
        response_map = {200: SampleTypedDict}

        # Should not raise
        requests._validate_response_map(response_map, func, type_hints)


class TestValidateResponseParser:
    def test_validate_response_parser_valid(self):
        """Test validating valid response_parser."""

        def func(result: SampleModel) -> SampleModel:
            return result

        def parser(response: http_response.Response) -> SampleModel:
            return SampleModel(name="test", value=1)

        type_hints = typing.get_type_hints(func)

        # Should not raise
        requests._validate_response_parser_return_type_matches_result_return_type(parser, func, type_hints)

    def test_validate_response_parser_no_return_annotation(self):
        """Test that parser without return annotation raises TypeError."""

        def func(result: SampleModel) -> SampleModel:
            return result

        def parser(response: http_response.Response):  # No return annotation
            return SampleModel(name="test", value=1)

        type_hints = typing.get_type_hints(func)

        with pytest.raises(TypeError, match="must have a return type annotation"):
            requests._validate_response_parser_return_type_matches_result_return_type(parser, func, type_hints)

    def test_validate_response_parser_mismatched_types(self):
        """Test that mismatched parser and result types raise TypeError."""

        def func(result: SampleModel) -> SampleModel:
            return result

        def parser(response: http_response.Response) -> ErrorModel:  # Different type
            return ErrorModel(error="test", code=1)

        type_hints = typing.get_type_hints(func)

        with pytest.raises(TypeError, match="does not match the type"):
            requests._validate_response_parser_return_type_matches_result_return_type(parser, func, type_hints)

    def test_validate_response_parser_union_types(self):
        """Test response_parser with Union types."""

        def func(result: SampleModel | ErrorModel) -> SampleModel | ErrorModel:
            return result

        def parser(response: http_response.Response) -> SampleModel | ErrorModel:
            if response.status_code == 200:
                return SampleModel(name="ok", value=1)
            return ErrorModel(error="fail", code=404)

        type_hints = typing.get_type_hints(func)

        # Should not raise
        requests._validate_response_parser_return_type_matches_result_return_type(parser, func, type_hints)


class TestGetResultTypesFromTypeHints:
    def test_get_result_types_single_type(self):
        """Test extracting single type from result parameter."""

        def func(result: SampleModel) -> SampleModel:
            return result

        type_hints = typing.get_type_hints(func)
        result_types = requests._get_result_types_from_type_hints(type_hints)

        assert result_types == [SampleModel]

    def test_get_result_types_union(self):
        """Test extracting Union types from result parameter."""

        def func(result: SampleModel | ErrorModel) -> SampleModel | ErrorModel:
            return result

        type_hints = typing.get_type_hints(func)
        result_types = requests._get_result_types_from_type_hints(type_hints)

        assert len(result_types) == 2
        assert SampleModel in result_types
        assert ErrorModel in result_types

    def test_get_result_types_no_result_annotation(self):
        """Test that missing result annotation raises ValueError."""
        type_hints = {}

        with pytest.raises(ValueError, match="must have a 'result' parameter with a type annotation"):
            requests._get_result_types_from_type_hints(type_hints)

    def test_get_result_types_old_style_union(self):
        """Test Union with typing.Union (not | syntax)."""

        def func(result: typing.Union[SampleModel, ErrorModel]) -> typing.Union[SampleModel, ErrorModel]:
            return result

        type_hints = typing.get_type_hints(func)
        result_types = requests._get_result_types_from_type_hints(type_hints)

        assert len(result_types) == 2
        assert SampleModel in result_types
        assert ErrorModel in result_types


class TestPreparedCall:
    def test_prepared_call_creation(self):
        """Test creating PreparedCall instance."""

        def func(result: dict) -> dict:
            return result

        context = requests.build_request_context("GET", "/test", func)
        sig = inspect.signature(func)
        bound_args = sig.bind(result={})

        prepared = requests.PreparedCall(
            context=context,
            bound_arguments=bound_args,
            call_arguments={"result": {}},
            url_path="/test",
            query_params=None,
            data_payload=None,
            headers_override=None,
            result_annotation=dict,
        )

        assert prepared.context == context
        assert prepared.url_path == "/test"
        assert prepared.result_annotation is dict


class TestRequestContext:
    def test_request_context_creation(self):
        """Test creating RequestContext instance."""

        def func(result: dict) -> dict:
            return result

        sig = inspect.signature(func)
        type_hints = typing.get_type_hints(func)

        context = requests.RequestContext(
            method="POST",
            path_template="/api/test",
            func=func,
            signature=sig,
            type_hints=type_hints,
            response_map=None,
            response_parser=None,
            streaming=False,
        )

        assert context.method == "POST"
        assert context.path_template == "/api/test"
        assert context.func == func
        assert context.signature == sig
        assert context.type_hints == type_hints
        assert context.streaming is False
