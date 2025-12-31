from __future__ import annotations

import inspect
import re
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Iterable, TypeVar, get_type_hints
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from .config import Config

try:  # pragma: no cover - conditional import
    from pydantic import TypeAdapter

    _HAS_TYPE_ADAPTER = True
except ImportError:  # pragma: no cover - fallback for Pydantic v1
    TypeAdapter = None  # type: ignore
    _HAS_TYPE_ADAPTER = False

try:  # pragma: no cover - conditional import
    from pydantic.tools import parse_obj_as
except Exception:  # pragma: no cover - fallback for Pydantic v2 only environments
    parse_obj_as = None  # type: ignore


_F = TypeVar("_F", bound=Callable[..., Any])
_PATH_PARAM_PATTERN = re.compile(r"{([^{}]+)}")


@dataclass
class _RequestContext:
    method: str
    path_template: str
    func: Callable[..., Any]
    signature: inspect.Signature
    type_hints: dict[str, Any]


def _build_request_context(method: str, path: str, func: Callable[..., Any]) -> _RequestContext:
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    return _RequestContext(
        method=method,
        path_template=path,
        func=func,
        signature=signature,
        type_hints=type_hints,
    )


@dataclass
class _PreparedCall:
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
        proxies: httpx._types.ProxiesTypes | None = None,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
        cookies: httpx._types.CookieTypes | None = None,
    ) -> None:
        if config is None:
            config = Config(
                base_url=base_url or "http://localhost",
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
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    def __enter__(self) -> "Client":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    async def __aenter__(self) -> "Client":
        await self.aopen()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.aclose()

    def open(self) -> None:
        """Instantiate a persistent ``httpx.Client``."""

        if self._client is None:
            self._client = self._build_client()

    async def aopen(self) -> None:
        """Instantiate a persistent ``httpx.AsyncClient``."""

        if self._async_client is None:
            self._async_client = self._build_async_client()

    def close(self) -> None:
        """Close the persistent client if it exists."""

        if self._client is not None:
            self._client.close()
            self._client = None

    async def aclose(self) -> None:
        """Close the persistent async client if it exists."""

        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None

    def get(self, path: str) -> Callable[[_F], _F]:
        return self._create_decorator("GET", path)

    def post(self, path: str) -> Callable[[_F], _F]:
        return self._create_decorator("POST", path)

    def put(self, path: str) -> Callable[[_F], _F]:
        return self._create_decorator("PUT", path)

    def patch(self, path: str) -> Callable[[_F], _F]:
        return self._create_decorator("PATCH", path)

    def delete(self, path: str) -> Callable[[_F], _F]:
        return self._create_decorator("DELETE", path)

    def _create_decorator(self, method: str, path: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            context = _build_request_context(method, path, func)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    return await self._execute_async(context, args, kwargs)

                return async_wrapper

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return self._execute_sync(context, args, kwargs)

            return wrapper

        return decorator

    def _build_client(self) -> httpx.Client:
        return httpx.Client(**self.config.httpx_client_options())

    def _build_async_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**self.config.httpx_client_options())

    @contextmanager
    def _get_client(self) -> Iterable[httpx.Client]:
        if self._client is not None:
            yield self._client
        else:
            with self._build_client() as client:
                yield client

    @asynccontextmanager
    async def _get_async_client(self) -> Iterable[httpx.AsyncClient]:
        if self._async_client is not None:
            yield self._async_client
        else:
            async with self._build_async_client() as client:
                yield client

    def _prepare_call(self, context: _RequestContext, args: tuple[Any, ...], kwargs: dict[str, Any]) -> _PreparedCall:
        kwargs_copy = dict(kwargs)
        reserved_kwargs = {name: kwargs_copy.pop(name) for name in ("headers", "query") if name in kwargs_copy}

        recognized_kwargs = {k: v for k, v in kwargs_copy.items() if k in context.signature.parameters}
        extra_kwargs = {k: v for k, v in kwargs_copy.items() if k not in context.signature.parameters}

        bound_arguments = context.signature.bind_partial(*args, **recognized_kwargs)
        bound_arguments.apply_defaults()
        call_arguments = bound_arguments.arguments
        call_arguments.update(reserved_kwargs)
        call_arguments.update(extra_kwargs)

        request_arguments = dict(call_arguments)
        request_arguments.pop("self", None)
        request_arguments.pop("result", None)
        request_arguments.pop("response", None)

        query_override = request_arguments.pop("query", None)
        headers_override = request_arguments.pop("headers", None)

        path_params: dict[str, Any] = {}
        for name in _PATH_PARAM_PATTERN.findall(context.path_template):
            if name not in request_arguments:
                raise ValueError(f"Missing path parameter '{name}' for path '{context.path_template}'")
            path_params[name] = request_arguments.pop(name)

        query_params = (
            query_override
            if query_override is not None
            else {k: v for k, v in request_arguments.items() if k != "data"}
        )

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

        with self._get_client() as client:
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

        async with self._get_async_client() as client:
            request_kwargs: dict[str, Any] = {"params": query_params, "headers": headers}
            if data_payload is not None:
                request_kwargs["json"] = data_payload

            response = await client.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response

    def _finalize_call(self, prepared: _PreparedCall, response: httpx.Response) -> Any:
        parsed_result = self._parse_response(response, prepared.return_annotation)

        if "result" in prepared.context.signature.parameters:
            prepared.call_arguments["result"] = parsed_result
        if "response" in prepared.context.signature.parameters:
            prepared.call_arguments["response"] = response

        return prepared.context.func(*prepared.bound_arguments.args, **prepared.bound_arguments.kwargs)

    def _parse_response(self, response: httpx.Response, annotation: Any) -> Any:
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

        if _HAS_TYPE_ADAPTER:
            adapter = TypeAdapter(annotation)  # type: ignore[arg-type]
            return adapter.validate_python(payload)

        if parse_obj_as is not None:
            return parse_obj_as(annotation, payload)

        return payload

    def _substitute_path(self, path_template: str, values: dict[str, Any]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            return quote(str(values.get(key)), safe="")

        return _PATH_PARAM_PATTERN.sub(replacer, path_template)
