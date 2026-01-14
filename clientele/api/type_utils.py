from __future__ import annotations

import inspect
import typing

import pydantic


def is_typeddict(annotation: typing.Any) -> bool:
    return typing.is_typeddict(annotation)


def is_pydantic_model(annotation: typing.Any) -> bool:
    """Check if annotation is a Pydantic BaseModel class."""
    return inspect.isclass(annotation) and issubclass(annotation, pydantic.BaseModel)


def is_streaming_type(annotation: typing.Any) -> bool:
    """
    Check if annotation is Iterator, AsyncIterator, etc.

    Args:
        annotation: The type annotation to check

    Returns:
        True if the annotation is a streaming type (Iterator or AsyncIterator)
    """
    origin = typing.get_origin(annotation)
    return origin in [
        typing.get_origin(typing.Iterator),
        typing.get_origin(typing.AsyncIterator),
    ]


def get_streaming_inner_type(annotation: typing.Any) -> typing.Any:
    """
    Extract T from AsyncIterator[T] or Iterator[T].

    Args:
        annotation: The streaming type annotation

    Returns:
        The inner type or None if not found
    """
    if not is_streaming_type(annotation):
        return None

    args = typing.get_args(annotation)
    return args[0] if args else None


def is_async_streaming_type(annotation: typing.Any) -> bool:
    """
    Check specifically for async streaming types.

    Args:
        annotation: The type annotation to check

    Returns:
        True if the annotation is AsyncIterator or AsyncGenerator
    """
    origin = typing.get_origin(annotation)
    return origin in [typing.get_origin(typing.AsyncIterator), typing.get_origin(typing.AsyncGenerator)]


def validate_typeddict(typeddict_class: type[typing.Any], payload: typing.Any) -> dict[str, typing.Any]:
    """
    Validate payload as a TypedDict.

    TypedDicts don't have runtime validation like Pydantic models,
    so we just ensure the payload is a dict and return it.
    The type checker will verify the structure at static analysis time.
    """
    if not isinstance(payload, dict):
        raise TypeError(f"Expected dict for TypedDict {typeddict_class.__name__}, got {type(payload).__name__}")
    return payload


def validate_model(model_class: type[pydantic.BaseModel], payload: typing.Any) -> pydantic.BaseModel:
    """Validate payload using a Pydantic model."""
    return model_class.model_validate(payload)
