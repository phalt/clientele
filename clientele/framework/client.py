from __future__ import annotations

import inspect
import re
import types
import typing
from functools import wraps
from typing import Any, Callable, TypeVar, cast, get_type_hints
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from .config import Config
from .exceptions import APIException
from .http_status import codes

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
    parse_obj_as = None  # type: ignore[assignment]


_F = TypeVar("_F", bound=Callable[..., Any])
_PATH_PARAM_PATTERN = re.compile(r"{([^{}]+)}")


class _RequestContext(BaseModel):
    """
    Captures metadata about a decorated HTTP method.

    Stores the HTTP method, path template, original function, signature, and
    type hints to enable request preparation and execution without re-parsing
    function metadata on every call.
    """

    model_config = {"arbitrary_types_allowed": True}

    method: str
    path_template: str
    func: Callable[..., Any]
    signature: inspect.Signature
    type_hints: dict[str, Any]
    response_map: dict[int, type[BaseModel]] | None = None


def _build_request_context(
    method: str, path: str, func: Callable[..., Any], response_map: dict[int, type[BaseModel]] | None = None
) -> _RequestContext:
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Validate response_map if provided
    if response_map is not None:
        _validate_response_map(response_map, func, type_hints)
    
    return _RequestContext(
        method=method,
        path_template=path,
        func=func,
        signature=signature,
        type_hints=type_hints,
        response_map=response_map,
    )


def _validate_response_map(response_map: dict[int, type[BaseModel]], func: Callable[..., Any], type_hints: dict[str, Any]) -> None:
    """
    Validates that response_map contains valid status codes and Pydantic models,
    and that all response models are in the function's return type annotation.
    """
    # Validate all keys are valid HTTP status codes
    for status_code in response_map.keys():
        if not codes.is_valid_status_code(status_code):
            raise ValueError(f"Invalid status code {status_code} in response_map")
    
    # Validate all values are Pydantic BaseModel subclasses
    for status_code, model_class in response_map.items():
        if not (inspect.isclass(model_class) and issubclass(model_class, BaseModel)):
            raise ValueError(f"response_map value for status code {status_code} must be a Pydantic BaseModel subclass")
    
    # Get the return annotation
    return_annotation = type_hints.get("return", func.__annotations__.get("return", inspect._empty))
    
    if return_annotation is inspect._empty:
        raise ValueError("Function decorated with response_map must have a return type annotation")
    
    # Extract all types from the return annotation (handle Union types)
    return_types: list[Any] = []
    origin = typing.get_origin(return_annotation)
    if origin in [typing.Union, types.UnionType]:
        return_types = list(typing.get_args(return_annotation))
    else:
        return_types = [return_annotation]
    
    # Check that all response_map models are in the return types
    for status_code, model_class in response_map.items():
        if model_class not in return_types:
            missing_model = model_class.__name__
            raise ValueError(
                f"Response model '{missing_model}' for status code {status_code} "
                f"is not in the function's return type annotation. "
                f"Please add '{missing_model}' to the return type of '{func.__name__}'."
            )


class _PreparedCall(BaseModel):
    """
    Encapsulates all data needed to execute an HTTP request.

    Contains parsed arguments, URL path, query parameters, request body,
    headers, and return type annotation for response parsing.
    """

    model_config = {"arbitrary_types_allowed": True}

    context: _RequestContext
    bound_arguments: inspect.BoundArguments
    call_arguments: dict[str, Any]
    url_path: str
    query_params: dict[str, Any] | None
    data_payload: Any
    headers_override: dict[str, str] | None
    return_annotation: Any


class Client:
    """A decorator-driven HTTP client for sync and async requests.

    Supports common HTTP verbs (GET, POST, PUT, PATCH, DELETE) and works with
    both synchronous and ``async`` decorated callables without separate
    classes. Decorated functions must have a real body; the wrapper executes
    the HTTP request before calling the function and injects the parsed
    response via a ``result`` argument when present.
    """

    def __init__(
        self,
        *,
        config: Config | None = None,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool | None = None,
        auth: httpx.Auth | tuple[str, str] | None = None,
        verify: bool | str | None = None,
        http2: bool | None = None,
        limits: httpx.Limits | None = None,
        proxies: httpx.Proxy | None = None,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
        cookies: httpx.Cookies | None = None,
    ) -> None:
        if config is None:
            # Enforce base_url when no config is provided
            if base_url is None:
                raise ValueError("Either 'config' or 'base_url' must be provided")

            config = Config(
                base_url=base_url,
                headers=headers or {},
                timeout=timeout if timeout is not None else 5.0,
                follow_redirects=follow_redirects if follow_redirects is not None else False,
                auth=auth,
                verify=True if verify is None else verify,
                http2=http2 or False,
                limits=limits,
                proxies=proxies,
                transport=transport,
                cookies=cookies,
            )
        self.config = config

    def get(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("GET", path, response_map=response_map)

    def post(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("POST", path, response_map=response_map)

    def put(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("PUT", path, response_map=response_map)

    def patch(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("PATCH", path, response_map=response_map)

    def delete(self, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        return self._create_decorator("DELETE", path, response_map=response_map)

    def _create_decorator(self, method: str, path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            context = _build_request_context(method, path, func, response_map=response_map)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await self._execute_async(context, args, kwargs)

                return cast(_F, async_wrapper)

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._execute_sync(context, args, kwargs)

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
            if name not in request_arguments:
                raise ValueError(f"Missing path parameter '{name}' for path '{context.path_template}'")
            path_params[name] = request_arguments.pop(name)

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

        data_payload: Any = None
        if context.method in {"POST", "PUT", "PATCH", "DELETE"}:
            data_param = context.signature.parameters.get("data")
            data_annotation = context.type_hints.get("data", data_param.annotation if data_param else inspect._empty)
            data_payload = self._prepare_body(call_arguments, data_param, data_annotation)

        url_path = self._substitute_path(context.path_template, path_params)
        return_annotation = context.type_hints.get("return", context.signature.return_annotation)

        return _PreparedCall(
            context=context,
            bound_arguments=bound_arguments,
            call_arguments=call_arguments,
            url_path=url_path,
            query_params=query_params,
            data_payload=data_payload,
            headers_override=headers_override,
            return_annotation=return_annotation,
        )

    def _execute_sync(self, context: _RequestContext, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        prepared = self._prepare_call(context, args, kwargs)
        response = self._send_request(
            method=context.method,
            url=prepared.url_path,
            query_params=prepared.query_params,
            data_payload=prepared.data_payload,
            headers_override=prepared.headers_override,
        )
        result = self._finalize_call(prepared, response)
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
        )
        result = self._finalize_call(prepared, response)
        if inspect.isawaitable(result):
            return await result
        return result

    def _prepare_body(
        self, call_arguments: dict[str, Any], data_param: inspect.Parameter | None, data_annotation: Any
    ) -> Any:
        if data_param is None:
            return None

        payload = call_arguments.get("data")
        if payload is None:
            return None

        annotation = data_annotation
        if annotation is inspect._empty:
            return payload

        if isinstance(payload, BaseModel):
            return self._dump_model(payload)

        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            validator = annotation.model_validate if hasattr(annotation, "model_validate") else annotation.parse_obj
            model_instance = validator(payload)
            return self._dump_model(model_instance)

        return payload

    def _dump_model(self, model: BaseModel) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()  # type: ignore[no-any-return]

    def _send_request(
        self,
        *,
        method: str,
        url: str,
        query_params: dict[str, Any] | None,
        data_payload: Any,
        headers_override: dict[str, str] | None,
    ) -> httpx.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        with self._build_client() as client:
            request_kwargs: dict[str, Any] = {"params": query_params, "headers": headers}
            if data_payload is not None:
                request_kwargs["json"] = data_payload

            response = client.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response

    async def _send_request_async(
        self,
        *,
        method: str,
        url: str,
        query_params: dict[str, Any] | None,
        data_payload: Any,
        headers_override: dict[str, str] | None,
    ) -> httpx.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        async with self._build_async_client() as client:
            request_kwargs: dict[str, Any] = {"params": query_params, "headers": headers}
            if data_payload is not None:
                request_kwargs["json"] = data_payload

            response = await client.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response

    def _finalize_call(self, prepared: _PreparedCall, response: httpx.Response) -> Any:
        parsed_result = self._parse_response(response, prepared.return_annotation, prepared.context.response_map)

        # Update call_arguments with injected values
        if "result" in prepared.context.signature.parameters:
            prepared.call_arguments["result"] = parsed_result
        if "response" in prepared.context.signature.parameters:
            prepared.call_arguments["response"] = response

        # Call the function with all arguments including injected ones
        return prepared.context.func(**prepared.call_arguments)

    def _parse_response(self, response: httpx.Response, annotation: Any, response_map: dict[int, type[BaseModel]] | None = None) -> Any:
        # If response_map is provided, use it to determine the response model
        if response_map is not None:
            status_code = response.status_code
            if status_code not in response_map:
                raise APIException(
                    response=response,
                    reason=f"Unexpected status code {status_code}. Expected one of: {', '.join(map(str, response_map.keys()))}"
                )
            # Get the model for this status code
            model_class = response_map[status_code]
            
            # Parse the response using the model
            payload: Any
            if not response.content:
                payload = None
            else:
                content_type = response.headers.get("content-type", "").lower()
                if "json" in content_type:
                    payload = response.json()
                else:
                    payload = response.text
            
            if payload is None:
                return None
                
            if hasattr(model_class, "model_validate"):
                return model_class.model_validate(payload)
            return model_class.parse_obj(payload)
        
        # Original parsing logic when no response_map
        payload: Any
        if not response.content:
            payload = None
        else:
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type:
                payload = response.json()
            else:
                payload = response.text

        if annotation is inspect._empty:
            return payload

        if payload is None:
            return None

        if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
            if hasattr(annotation, "model_validate"):
                return annotation.model_validate(payload)
            return annotation.parse_obj(payload)

        if _HAS_TYPE_ADAPTER and TypeAdapter is not None:
            adapter = TypeAdapter(annotation)
            return adapter.validate_python(payload)

        if parse_obj_as is not None:
            return parse_obj_as(annotation, payload)

        return payload

    def _substitute_path(self, path_template: str, values: dict[str, Any]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            return quote(str(values.get(key)), safe="")

        return _PATH_PARAM_PATTERN.sub(replacer, path_template)
