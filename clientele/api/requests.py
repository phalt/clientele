from __future__ import annotations

import inspect
import types
import typing

import pydantic

from clientele.api import type_utils
from clientele.http import response as http_response
from clientele.http import status_codes


class PreparedCall(pydantic.BaseModel):
    """
    Encapsulates all data needed to execute an HTTP request.

    Contains parsed arguments, URL path, query parameters, request body,
    headers, and result type annotation for response parsing.
    """

    model_config = {"arbitrary_types_allowed": True}

    context: RequestContext
    bound_arguments: inspect.BoundArguments
    call_arguments: dict[str, typing.Any]
    url_path: str
    query_params: dict[str, typing.Any] | None
    data_payload: dict[str, typing.Any] | None
    headers_override: dict[str, str] | None
    result_annotation: typing.Any


class RequestContext(pydantic.BaseModel):
    """
    Captures metadata about a decorated HTTP method.

    Stores the HTTP method, path template, original function, signature,
    type hints, and response map to enable request preparation and execution
    without re-parsing function metadata on every call.
    """

    model_config = {"arbitrary_types_allowed": True}

    method: str
    path_template: str
    func: typing.Callable[..., typing.Any]
    signature: inspect.Signature
    type_hints: dict[str, typing.Any]
    response_map: dict[int, type[typing.Any]] | None = None
    response_parser: (
        typing.Callable[[http_response.Response], typing.Any] | typing.Callable[[str], typing.Any] | None
    ) = None
    streaming: bool = False


def validate_result_parameter(
    func: typing.Callable[..., typing.Any],
    signature: inspect.Signature,
    type_hints: dict[str, typing.Any],
    expect_streaming: bool = False,
) -> None:
    """
    Validates that the decorated function has a 'result' parameter with a type annotation.

    The 'result' parameter is mandatory and drives response hydration.

    Args:
        func: The function to validate
        signature: The function's signature
        type_hints: The function's type hints
        expect_streaming: If True, validates that result is Iterator/AsyncIterator
    """
    func_name = getattr(func, "__name__", "<function>")

    # Check if 'result' parameter exists
    if "result" not in signature.parameters:
        raise TypeError(
            f"Function '{func_name}' must have a 'result' parameter. "
            "The 'result' parameter is required and its type annotation determines how the HTTP response is parsed."
        )

    # Check if 'result' has a type annotation
    result_param = signature.parameters["result"]
    result_annotation = type_hints.get("result", result_param.annotation if result_param else inspect._empty)

    if result_annotation is inspect._empty:
        raise TypeError(
            f"Function '{func_name}' has a 'result' parameter but it lacks a type annotation. "
            "The 'result' parameter must be annotated with the expected response type (e.g., 'result: User')."
        )

    # Streaming-specific validation
    if expect_streaming:
        if not type_utils.is_streaming_type(result_annotation):
            raise TypeError(
                f"Function '{func_name}' decorated with stream decorator must have a streaming result type "
                f"(e.g., AsyncIterator[Token]), but got {result_annotation}."
            )

        inner_type = type_utils.get_streaming_inner_type(result_annotation)
        if inner_type is None:
            raise TypeError(
                f"Function '{func_name}' has a streaming result type but no inner type specified. "
                f"Use AsyncIterator[YourType] to specify the type of streamed items."
            )

        # Validate that async/sync function matches AsyncIterator/Iterator type
        is_async_func = inspect.iscoroutinefunction(func)
        is_async_result = type_utils.is_async_streaming_type(result_annotation)

        if is_async_func and not is_async_result:
            type_name = inner_type.__name__ if hasattr(inner_type, "__name__") else str(inner_type)
            raise TypeError(
                f"Async function '{func_name}' must use AsyncIterator, not Iterator. "
                f"Change the result type annotation to AsyncIterator[{type_name}]."
            )

        if not is_async_func and is_async_result:
            type_name = inner_type.__name__ if hasattr(inner_type, "__name__") else str(inner_type)
            raise TypeError(
                f"Synchronous function '{func_name}' must use Iterator, not AsyncIterator. "
                f"Either declare the function as async or change the result type to Iterator[{type_name}]."
            )


def build_request_context(
    method: str,
    path: str,
    func: typing.Callable[..., typing.Any],
    response_map: dict[int, type[typing.Any]] | None = None,
    response_parser: typing.Callable[[http_response.Response], typing.Any]
    | typing.Callable[[str], typing.Any]
    | None = None,
    streaming: bool = False,
) -> RequestContext:
    signature = inspect.signature(func)
    # Get type hints with proper handling of forward references
    # This follows the pattern used in FastAPI and other server frameworks
    try:
        type_hints = typing.get_type_hints(func, include_extras=True)
    except NameError:
        # Forward references that can't be resolved - use raw annotations
        type_hints = func.__annotations__.copy()

    # Validate that the function has a 'result' parameter with a type annotation
    validate_result_parameter(func, signature, type_hints, expect_streaming=streaming)

    if streaming and response_map is not None:
        raise TypeError(
            f"Function '{getattr(func, '__name__', '<function>')}' with streaming=True cannot use response_map."
        )

    if response_map is not None and response_parser is not None:
        raise TypeError(
            f"Function '{getattr(func, '__name__', '<function>')}' cannot have both "
            "'response_map' and 'response_parser' defined. Please provide only one."
        )

    # Validate response_map if provided
    if response_map is not None:
        _validate_response_map(response_map, func, type_hints)

    if response_parser is not None:
        _validate_response_parser_return_type_matches_result_return_type(
            response_parser=response_parser, func=func, type_hints=type_hints, streaming=streaming
        )

    return RequestContext(
        method=method,
        path_template=path,
        func=func,
        signature=signature,
        type_hints=type_hints,
        response_map=response_map,
        response_parser=response_parser,
        streaming=streaming,
    )


def _validate_response_map(
    response_map: dict[int, type[typing.Any]], func: typing.Callable[..., typing.Any], type_hints: dict[str, typing.Any]
) -> None:
    """
    Validates that response_map contains valid status codes and Pydantic models or TypedDicts,
    and that all response models are in the function's result parameter type annotation.
    """
    # Validate all keys are valid HTTP status codes
    for status_code in response_map.keys():
        if not status_codes.codes.is_valid_status_code(status_code):
            raise ValueError(f"Invalid status code {status_code} in response_map")

    # Validate all values are Pydantic BaseModel subclasses or TypedDict classes
    for status_code, model_class in response_map.items():
        if not (type_utils.is_pydantic_model(model_class) or type_utils.is_typeddict(model_class)):
            raise ValueError(
                f"response_map value for status code {status_code} must be a Pydantic BaseModel subclass or TypedDict"
            )

    # Get the result parameter annotation
    result_types = _get_result_types_from_type_hints(type_hints)

    # Check that all response_map models are in the result types
    for status_code, model_class in response_map.items():
        if model_class not in result_types:
            missing_model = model_class.__name__
            func_name = getattr(func, "__name__", "<function>")
            raise ValueError(
                f"Response model '{missing_model}' for status code {status_code} "
                f"is not in the 'result' parameter's type annotation. "
                f"Please add '{missing_model}' to the 'result' parameter type of '{func_name}'."
            )


def _validate_response_parser_return_type_matches_result_return_type(
    response_parser: typing.Callable[[http_response.Response], typing.Any] | typing.Callable[[str], typing.Any],
    func: typing.Callable[..., typing.Any],
    type_hints: dict[str, typing.Any],
    streaming: bool = False,
) -> None:
    """
    Validates that the return type of the response_parser matches the type of the 'result' parameter.
    For streaming, the parser should return the inner type (T from AsyncIterator[T]).
    """
    func_name = getattr(func, "__name__", "<function>")

    # Get the return type of the response_parser using get_type_hints to handle string annotations
    try:
        parser_type_hints = typing.get_type_hints(response_parser)
        parser_return_annotation = parser_type_hints.get("return", inspect._empty)
    except Exception:
        # Fallback to inspect.signature if get_type_hints fails
        parser_signature = inspect.signature(response_parser)
        parser_return_annotation = parser_signature.return_annotation

    if parser_return_annotation is inspect._empty:
        raise TypeError(f"The response_parser provided for function '{func_name}' must have a return type annotation.")

    parser_return_types: list[typing.Any] = []
    origin = typing.get_origin(parser_return_annotation)
    # Also check if the annotation itself is a UnionType (Python 3.10+ `X | Y` syntax)
    if origin in [typing.Union, types.UnionType] or isinstance(parser_return_annotation, types.UnionType):
        parser_return_types = list(typing.get_args(parser_return_annotation))
    else:
        parser_return_types = [parser_return_annotation]

    # For streaming, get the inner type from AsyncIterator[T] or Iterator[T]
    if streaming:
        result_annotation = type_hints.get("result", inspect._empty)
        if result_annotation is inspect._empty:
            raise ValueError("Streaming function must have a 'result' parameter with a type annotation")

        # Extract the inner type from AsyncIterator[T] or Iterator[T]
        inner_type = type_utils.get_streaming_inner_type(result_annotation)
        if inner_type is None:
            raise TypeError(f"Could not extract inner type from streaming result type: {result_annotation}")

        # For streaming, parser should return the inner type
        # If inner type is a Union, decompose it for comparison
        origin = typing.get_origin(inner_type)
        if origin in [typing.Union, types.UnionType] or isinstance(inner_type, types.UnionType):
            result_types = list(typing.get_args(inner_type))
        else:
            result_types = [inner_type]
    else:
        result_types = _get_result_types_from_type_hints(type_hints)

    def _stringify_types(types_list: list[typing.Any]) -> list[str]:
        result = []
        for t in types_list:
            if isinstance(t, str):
                result.append(t)
            elif hasattr(t, "__name__"):
                result.append(t.__name__)
            else:
                # For types without __name__ (like UnionType), convert to string
                result.append(str(t))
        return result

    stringified_parser_types = _stringify_types(parser_return_types)
    stringified_return_types = _stringify_types(result_types)
    if not stringified_return_types == stringified_parser_types:
        raise TypeError(
            f"The return type of the response_parser for function '{func_name}': "
            f"[{', '.join([t for t in stringified_parser_types])}] does not "
            "match the type(s) of the 'result' parameter: "
            f"[{', '.join([t for t in stringified_return_types])}]."
        )


def _get_result_types_from_type_hints(
    type_hints: dict[str, typing.Any],
) -> list[typing.Any]:
    """
    Extracts all types from the 'result' parameter annotation (handles Union types).
    """
    result_annotation = type_hints.get("result", inspect._empty)

    if result_annotation is inspect._empty:
        # This should not happen since we validate result parameter earlier, but defensive check
        raise ValueError("Function decorated with response_map must have a 'result' parameter with a type annotation")

    result_types: list[typing.Any] = []
    origin = typing.get_origin(result_annotation)
    if origin in [typing.Union, types.UnionType]:
        result_types = list(typing.get_args(result_annotation))
    else:
        result_types = [result_annotation]

    return result_types
