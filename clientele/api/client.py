from __future__ import annotations

import inspect
import re
import types
import typing
from functools import wraps
from typing import Any, Callable, TypeVar, cast, get_type_hints, is_typeddict
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.api import http_status

try:  # pragma: no cover - conditional import
    from pydantic import TypeAdapter

    _HAS_TYPE_ADAPTER = True
except ImportError:  # pragma: no cover - fallback for Pydantic v1
    # TypeAdapter is used for validating complex types like List[Model], Optional[Model], etc.
    # It's available in Pydantic v2 and provides better type handling than parse_obj_as.
    # For Pydantic v1, we fall back to parse_obj_as which has similar functionality.
    TypeAdapter = None  # type: ignore[assignment, misc]
    _HAS_TYPE_ADAPTER = False

try:  # pragma: no cover - conditional import
    from pydantic.tools import parse_obj_as
except Exception:  # pragma: no cover - fallback for Pydantic v2 only environments
    # parse_obj_as is the Pydantic v1 equivalent of TypeAdapter.
    # In Pydantic v2-only environments, this import will fail and we use TypeAdapter instead.
    parse_obj_as = None


_F = TypeVar("_F", bound=Callable[..., Any])
_PATH_PARAM_PATTERN = re.compile(r"{([^{}]+)}")


def _is_pydantic_model(annotation: Any) -> bool:
    """Check if annotation is a Pydantic BaseModel class."""
    return inspect.isclass(annotation) and issubclass(annotation, BaseModel)


def _is_typeddict(annotation: Any) -> bool:
    """
    Check if annotation is a TypedDict class.

    This wrapper exists for:
    1. Consistency with _is_pydantic_model helper
    2. Future extensibility if TypedDict detection needs special handling
    3. Centralized location for TypedDict checking logic
    """
    return is_typeddict(annotation)


class _RequestContext(BaseModel):
    """
    Captures metadata about a decorated HTTP method.

    Stores the HTTP method, path template, original function, signature,
    type hints, and response map to enable request preparation and execution
    without re-parsing function metadata on every call.
    """

    model_config = {"arbitrary_types_allowed": True}

    method: str
    path_template: str
    func: Callable[..., Any]
    signature: inspect.Signature
    type_hints: dict[str, Any]
    response_map: dict[int, type[Any]] | None = None
    response_parser: Callable[[httpx.Response], Any] | None = None


def _validate_result_parameter(
    func: Callable[..., Any], signature: inspect.Signature, type_hints: dict[str, Any]
) -> None:
    """
    Validates that the decorated function has a 'result' parameter with a type annotation.

    The 'result' parameter is mandatory and drives response hydration.
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


def build_request_context(
    method: str,
    path: str,
    func: Callable[..., Any],
    response_map: dict[int, type[Any]] | None = None,
    response_parser: Callable[[httpx.Response], Any] | None = None,
) -> _RequestContext:
    signature = inspect.signature(func)
    # Get type hints with proper handling of forward references
    # This follows the pattern used in FastAPI and other server frameworks
    try:
        type_hints = get_type_hints(func, include_extras=True)
    except NameError:
        # Forward references that can't be resolved - use raw annotations
        type_hints = func.__annotations__.copy()

    # Validate that the function has a 'result' parameter with a type annotation
    _validate_result_parameter(func, signature, type_hints)

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
            response_parser=response_parser, func=func, type_hints=type_hints
        )

    return _RequestContext(
        method=method,
        path_template=path,
        func=func,
        signature=signature,
        type_hints=type_hints,
        response_map=response_map,
        response_parser=response_parser,
    )


def _get_result_types_from_type_hints(
    type_hints: dict[str, Any],
) -> list[Any]:
    """
    Extracts all types from the 'result' parameter annotation (handles Union types).
    """
    result_annotation = type_hints.get("result", inspect._empty)

    if result_annotation is inspect._empty:
        # This should not happen since we validate result parameter earlier, but defensive check
        raise ValueError("Function decorated with response_map must have a 'result' parameter with a type annotation")

    result_types: list[Any] = []
    origin = typing.get_origin(result_annotation)
    if origin in [typing.Union, types.UnionType]:
        result_types = list(typing.get_args(result_annotation))
    else:
        result_types = [result_annotation]

    return result_types


def _validate_response_parser_return_type_matches_result_return_type(
    response_parser: Callable[[httpx.Response], Any],
    func: Callable[..., Any],
    type_hints: dict[str, Any],
) -> None:
    """
    Validates that the return type of the response_parser matches the type of the 'result' parameter.
    """
    func_name = getattr(func, "__name__", "<function>")

    # Get the return type of the response_parser
    parser_signature = inspect.signature(response_parser)
    parser_return_annotation = parser_signature.return_annotation

    if parser_return_annotation is inspect._empty:
        raise TypeError(f"The response_parser provided for function '{func_name}' must have a return type annotation.")

    parser_return_types: list[Any] = []
    origin = typing.get_origin(parser_return_annotation)
    if origin in [typing.Union, types.UnionType]:
        parser_return_types = list(typing.get_args(parser_return_annotation))
    else:
        parser_return_types = [parser_return_annotation]

    result_types = _get_result_types_from_type_hints(type_hints)

    if not [ptype.__name__ for ptype in result_types] == parser_return_types:
        raise TypeError(
            f"The return type of the response_parser for function '{func_name}': "
            f"[{', '.join([t for t in parser_return_types])}] does not "
            "match the type(s) of the 'result' parameter: "
            f"[{', '.join([t.__name__ for t in result_types])}]."
        )


def _validate_response_map(
    response_map: dict[int, type[Any]], func: Callable[..., Any], type_hints: dict[str, Any]
) -> None:
    """
    Validates that response_map contains valid status codes and Pydantic models or TypedDicts,
    and that all response models are in the function's result parameter type annotation.
    """
    # Validate all keys are valid HTTP status codes
    for status_code in response_map.keys():
        if not http_status.codes.is_valid_status_code(status_code):
            raise ValueError(f"Invalid status code {status_code} in response_map")

    # Validate all values are Pydantic BaseModel subclasses or TypedDict classes
    for status_code, model_class in response_map.items():
        if not (_is_pydantic_model(model_class) or _is_typeddict(model_class)):
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


class _PreparedCall(BaseModel):
    """
    Encapsulates all data needed to execute an HTTP request.

    Contains parsed arguments, URL path, query parameters, request body,
    headers, and result type annotation for response parsing.
    """

    model_config = {"arbitrary_types_allowed": True}

    context: _RequestContext
    bound_arguments: inspect.BoundArguments
    call_arguments: dict[str, Any]
    url_path: str
    query_params: dict[str, Any] | None
    data_payload: dict[str, Any] | None
    headers_override: dict[str, str] | None
    result_annotation: Any


class APIClient:
    """Clientele is a tool for building typed HTTP API clients.

    Supports common HTTP verbs (GET, POST, PUT, PATCH, DELETE) and works with
    both synchronous and ``async`` functions.

    Args:
        config: Optional BaseConfig instance for configuring the client.
        base_url: Optional base URL for the API. Required if config is not provided.
        httpx_client: Optional pre-configured httpx.Client instance. If not provided,
            a new client will be created using the config values.
            The client is reused across all synchronous requests for connection pooling.
        httpx_async_client: Optional pre-configured httpx.AsyncClient instance. If not
            provided, a new async client will be created using the config values.
            The client is reused across all asynchronous requests for connection pooling.

    Basic example:
    ```
    from clientele import api as clientele_api
    from my_api_client import config, schemas

    api_client = clientele_api.APIClient(config=config.Config())

    @api_client.get("/users")
    def list_users(result: schemas.ResponseListUsers) -> schemas.ResponseListUsers:
        return result
    ```

    Custom httpx client example:

    ```
    import httpx
    from clientele import api as clientele_api

    # Your custom httpx client with specific settings
    custom_client = httpx.Client(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100)
    )

    api_client = clientele_api.APIClient(
        base_url="https://api.example.com",
        httpx_client=custom_client
    )

    ... use the client as normal ...
    ```

    See https://phalt.github.io/clientele for full documentation.
    """

    def __init__(
        self,
        *,
        config: api_config.BaseConfig | None = None,
        base_url: str | None = None,
        httpx_client: httpx.Client | None = None,
        httpx_async_client: httpx.AsyncClient | None = None,
    ) -> None:
        if config and (httpx_client or httpx_async_client):
            raise ValueError("Cannot provide both 'config' and custom httpx clients")
        if config is None:
            # Enforce base_url when no config is provided
            if base_url is None:
                raise ValueError("Cannot provide both 'config' and 'base_url'.")

            config = api_config.get_default_config(base_url=base_url)
        self.config = config

        # Create or use provided singleton clients for connection pooling
        self._sync_client = httpx_client or self._build_client()
        self._async_client = httpx_async_client or self._build_async_client()

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        self._sync_client.close()

    async def aclose(self) -> None:
        """Close the asynchronous HTTP client."""
        await self._async_client.aclose()

    def get(
        self,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        return self._create_decorator("GET", path, response_map=response_map, response_parser=response_parser)

    def post(
        self,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        return self._create_decorator("POST", path, response_map=response_map, response_parser=response_parser)

    def put(
        self,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        return self._create_decorator("PUT", path, response_map=response_map, response_parser=response_parser)

    def patch(
        self,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        return self._create_decorator("PATCH", path, response_map=response_map, response_parser=response_parser)

    def delete(
        self,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        return self._create_decorator("DELETE", path, response_map=response_map, response_parser=response_parser)

    def _create_decorator(
        self,
        method: str,
        path: str,
        *,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            context = build_request_context(
                method, path, func, response_map=response_map, response_parser=response_parser
            )

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await self._execute_async(context, args, kwargs)

                # Preserve the original signature for IDE support
                async_wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
                return cast(_F, async_wrapper)

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._execute_sync(context, args, kwargs)

            # Preserve the original signature for IDE support
            wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
            return cast(_F, wrapper)

        return decorator

    def _build_client(self) -> httpx.Client:
        return httpx.Client(**self.config.httpx_client_options())

    def _build_async_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**self.config.httpx_client_options())

    def _prepare_call(self, context: _RequestContext, args: tuple[Any, ...], kwargs: dict[str, Any]) -> _PreparedCall:
        """
        Parse function arguments into an HTTP request specification.

        Binds arguments to the function signature, extracts path parameters,
        query parameters, request body, and headers. Returns a _PreparedCall
        with all necessary data for executing the HTTP request.
        """
        kwargs_copy = dict(kwargs)
        # Extract reserved keywords that control request behavior
        query_override = kwargs_copy.pop("query", None) if "query" not in context.signature.parameters else None
        headers_override = kwargs_copy.pop("headers", None) if "headers" not in context.signature.parameters else None

        recognized_kwargs = {k: v for k, v in kwargs_copy.items() if k in context.signature.parameters}
        extra_kwargs = {k: v for k, v in kwargs_copy.items() if k not in context.signature.parameters}

        bound_arguments = context.signature.bind_partial(*args, **recognized_kwargs)
        bound_arguments.apply_defaults()
        call_arguments = bound_arguments.arguments
        # Note: extra_kwargs are NOT added to call_arguments - they're for query params only

        request_arguments = dict(call_arguments)
        request_arguments.pop("self", None)
        request_arguments.pop("result", None)
        request_arguments.pop("response", None)

        path_params: dict[str, Any] = {}
        for name in _PATH_PARAM_PATTERN.findall(context.path_template):
            # Check request_arguments first, then fall back to extra_kwargs
            if name in request_arguments:
                path_params[name] = request_arguments.pop(name)
            elif name in extra_kwargs:
                # For endpoints without explicit signatures, path params come from extra_kwargs
                path_params[name] = extra_kwargs.pop(name)
            else:
                raise ValueError(f"Missing path parameter '{name}' for path '{context.path_template}'")

        # Build query params
        # If query was explicitly passed and not in signature, use it as override
        if query_override is not None:
            query_params = query_override
        # If query is in the signature, use its value from request_arguments
        elif "query" in request_arguments:
            query_params = request_arguments.pop("query")
        # Otherwise, use remaining arguments plus extra kwargs
        else:
            query_params = {k: v for k, v in request_arguments.items() if k != "data"}
            query_params.update(extra_kwargs)

        # Filter out None values from query params to avoid adding empty parameters to the URL
        if query_params:
            query_params = {k: v for k, v in query_params.items() if v is not None}

        data_payload: dict[str, Any] | None = None
        if context.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Fetch 'data' payload for methods that support a body
            data_param = context.signature.parameters.get("data")
            data_annotation = context.type_hints.get("data", data_param.annotation if data_param else inspect._empty)

            # Check if data is in call_arguments or extra_kwargs (for endpoints without explicit signatures)
            if "data" in call_arguments:
                data_payload = self._prepare_body(call_arguments, data_param, data_annotation)
            elif "data" in extra_kwargs:
                # For endpoints without explicit signatures, data comes from extra_kwargs
                temp_args = {"data": extra_kwargs.pop("data")}
                # Create a minimal data parameter if none exists
                if data_param is None:
                    data_param = inspect.Parameter("data", inspect.Parameter.KEYWORD_ONLY)
                data_payload = self._prepare_body(temp_args, data_param, data_annotation)
            else:
                data_payload = self._prepare_body(call_arguments, data_param, data_annotation)

        url_path = self._substitute_path(context.path_template, path_params)
        result_annotation = context.type_hints.get("result", inspect._empty)

        return _PreparedCall(
            context=context,
            bound_arguments=bound_arguments,
            call_arguments=call_arguments,
            url_path=url_path,
            query_params=query_params,
            data_payload=data_payload,
            headers_override=headers_override,
            result_annotation=result_annotation,
        )

    def _execute_sync(self, context: _RequestContext, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        prepared = self._prepare_call(context, args, kwargs)
        response = self._send_request(
            method=context.method,
            url=prepared.url_path,
            query_params=prepared.query_params,
            data_payload=prepared.data_payload,
            headers_override=prepared.headers_override,
            response_map=context.response_map,
        )
        result = self._finalise_call(prepared=prepared, response=response)
        if inspect.isawaitable(result):
            raise TypeError(
                "Synchronous handlers cannot return awaitable results; declare the function as async instead"
            )
        return result

    async def _execute_async(self, context: _RequestContext, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        prepared = self._prepare_call(context, args, kwargs)
        response = await self._send_request_async(
            method=context.method,
            url=prepared.url_path,
            query_params=prepared.query_params,
            data_payload=prepared.data_payload,
            headers_override=prepared.headers_override,
            response_map=context.response_map,
        )
        result = self._finalise_call(prepared=prepared, response=response)
        if inspect.isawaitable(result):
            return await result
        return result

    def _prepare_body(
        self, call_arguments: dict[str, Any], data_param: inspect.Parameter | None, data_annotation: Any
    ) -> dict[str, Any] | None:
        if data_param is None:
            return None

        payload = call_arguments.get("data")
        if payload is None:
            return None

        annotation = data_annotation
        if annotation is inspect._empty:
            return payload

        # Handle Pydantic BaseModel instances
        if isinstance(payload, BaseModel):
            return self._dump_model(payload)

        # Handle Pydantic BaseModel classes (validate and dump)
        if _is_pydantic_model(annotation):
            validator = annotation.model_validate if hasattr(annotation, "model_validate") else annotation.parse_obj
            model_instance = validator(payload)
            return self._dump_model(model_instance)

        # Handle TypedDict classes
        # TypedDicts don't have runtime validation, so we just ensure the payload is a dict
        if _is_typeddict(annotation):
            if not isinstance(payload, dict):
                raise TypeError(f"Expected dict for TypedDict {annotation.__name__}, got {type(payload).__name__}")
            return payload

        return payload

    def _dump_model(self, model: BaseModel) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()

    def _send_request(
        self,
        *,
        method: str,
        url: str,
        query_params: dict[str, Any] | None,
        data_payload: dict[str, Any] | None,
        headers_override: dict[str, str] | None,
        response_map: dict[int, type[Any]] | None = None,
    ) -> httpx.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        request_kwargs: dict[str, Any] = {"params": query_params, "headers": headers}
        if data_payload is not None:
            request_kwargs["json"] = data_payload

        response = self._sync_client.request(method, url, **request_kwargs)
        # Only raise for status if we don't have a response_map
        # If we have a response_map, we want to handle error responses
        if response_map is None:
            response.raise_for_status()
        return response

    async def _send_request_async(
        self,
        *,
        method: str,
        url: str,
        query_params: dict[str, Any] | None,
        data_payload: dict[str, Any] | None,
        headers_override: dict[str, str] | None,
        response_map: dict[int, type[Any]] | None = None,
    ) -> httpx.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        request_kwargs: dict[str, Any] = {"params": query_params, "headers": headers}
        if data_payload is not None:
            request_kwargs["json"] = data_payload

        response = await self._async_client.request(method, url, **request_kwargs)
        # Only raise for status if we don't have a response_map
        # If we have a response_map, we want to handle error responses
        if response_map is None:
            response.raise_for_status()
        return response

    def _finalise_call(
        self,
        prepared: _PreparedCall,
        response: httpx.Response,
    ) -> Any:
        parsed_result = self._parse_response(
            response=response,
            annotation=prepared.result_annotation,
            response_map=prepared.context.response_map,
            response_parser=prepared.context.response_parser,
        )

        # Update call_arguments with injected values from parsed_result and response
        if "result" in prepared.context.signature.parameters:
            prepared.call_arguments["result"] = parsed_result
        if "response" in prepared.context.signature.parameters:
            prepared.call_arguments["response"] = response

        # Call the function with all arguments including injected ones
        return prepared.context.func(**prepared.call_arguments)

    def _parse_response(
        self,
        response: httpx.Response,
        annotation: Any,
        response_map: dict[int, type[Any]] | None = None,
        response_parser: Callable[[httpx.Response], Any] | None = None,
    ) -> Any:
        # Extract payload from response
        payload: Any
        if not response.content:
            payload = None
        else:
            # Default to JSON for API responses
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type or not content_type:
                # JSON content or no content-type specified - assume JSON
                try:
                    payload = response.json()
                except (ValueError, TypeError):
                    # Not valid JSON - fallback to text
                    payload = response.text
            else:
                # Explicit non-JSON content type
                payload = response.text

        if response_parser is not None:
            # If a custom response_parser is provided, use it directly
            return response_parser(response)

        # If response_map is provided, use it to determine the response model
        if response_map is not None:
            status_code = response.status_code
            if status_code not in response_map:
                expected_codes = ", ".join(map(str, response_map.keys()))
                raise api_exceptions.APIException(
                    response=response,
                    reason=f"Unexpected status code {status_code}. Expected one of: {expected_codes}",
                )
            # Get the model for this status code and validate
            model_class = response_map[status_code]
            if payload is None:
                return None
            # Check if it's a Pydantic model or TypedDict
            if _is_pydantic_model(model_class):
                return self._validate_model(model_class, payload)
            elif _is_typeddict(model_class):
                return self._validate_typeddict(model_class, payload)
            else:
                # Fallback to returning payload as-is
                return payload

        # Standard parsing logic when no response_map
        if annotation is inspect._empty:
            return payload

        if payload is None:
            return None

        if _is_pydantic_model(annotation):
            return self._validate_model(annotation, payload)

        if _is_typeddict(annotation):
            return self._validate_typeddict(annotation, payload)

        if _HAS_TYPE_ADAPTER and TypeAdapter is not None:
            adapter = TypeAdapter(annotation)
            return adapter.validate_python(payload)

        if parse_obj_as is not None:
            return parse_obj_as(annotation, payload)

        return payload

    def _validate_model(self, model_class: type[BaseModel], payload: Any) -> BaseModel:
        """Validate payload using a Pydantic model, supporting both v1 and v2."""
        if hasattr(model_class, "model_validate"):
            return model_class.model_validate(payload)
        return model_class.parse_obj(payload)

    def _validate_typeddict(self, typeddict_class: type[Any], payload: Any) -> dict[str, Any]:
        """
        Validate payload as a TypedDict.

        TypedDicts don't have runtime validation like Pydantic models,
        so we just ensure the payload is a dict and return it.
        The type checker will verify the structure at static analysis time.
        """
        if not isinstance(payload, dict):
            raise TypeError(f"Expected dict for TypedDict {typeddict_class.__name__}, got {type(payload).__name__}")
        # Return the payload as-is; TypedDict is for type checking, not runtime validation
        return payload

    def _substitute_path(self, path_template: str, values: dict[str, Any]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            return quote(str(values.get(key)), safe="")

        return _PATH_PARAM_PATTERN.sub(replacer, path_template)
