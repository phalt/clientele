from __future__ import annotations

import functools
import inspect
import re
import time
import typing
from urllib import parse

import httpx
import pydantic

from clientele.api import config as api_config
from clientele.api import exceptions as api_exceptions
from clientele.api import requests, type_utils
from clientele.http import httpx_backend as http_httpx
from clientele.http import response as http_response

_F = typing.TypeVar("_F", bound=typing.Callable[..., typing.Any])
_PATH_PARAM_PATTERN = re.compile(r"{([^{}]+)}")


class APIClient:
    """Clientele is a tool for building typed HTTP API clients with decorators.

    Supports common HTTP verbs (GET, POST, PUT, PATCH, DELETE) and works with
    both synchronous and ``async`` functions.

    Args:
        config: Optional BaseConfig instance for configuring the client.
        base_url: Optional base URL for the API. Required if config is not provided.

    Basic example:
    ```python
    from clientele import api
    from .schemas import Pokemon

    client = api.APIClient(base_url="https://pokeapi.co/api/v2/")

    @client.get("/pokemon/{id}")
    def get_pokemon_name(id: int, result: Pokemon) -> str:
        return result.name
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
        if config is None:
            # Enforce base_url when no config is provided
            if base_url is None:
                raise ValueError("Must provide either 'config' or 'base_url'.")
        self.configure(
            config=config,
            base_url=base_url,
        )

    def configure(
        self,
        *,
        config: api_config.BaseConfig | None = None,
        base_url: str | None = None,
    ) -> None:
        """Reconfigure the API client with a new configuration."""

        if config:
            self.config = config
        elif base_url:
            self.config = api_config.get_default_config(base_url=base_url)

        # Set http_backend if not already set
        if self.config.http_backend is None:
            self.config.http_backend = http_httpx.HttpxHTTPBackend(
                client_options=self.config.httpx_client_options(),
            )

    def close(self) -> None:
        """Close the synchronous HTTP client."""
        if self.config.http_backend is not None:
            self.config.http_backend.close()

    async def aclose(self) -> None:
        """Close the asynchronous HTTP client."""
        if self.config.http_backend is not None:
            await self.config.http_backend.aclose()

    def request(
        self,
        method: str,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]],
        data: dict[str, typing.Any] | pydantic.BaseModel | None = None,
        query: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        **path_params: typing.Any,
    ) -> typing.Any:
        """
        Execute an HTTP request and hydrate the response according to the provided response_map.

        This method can be used for making requests without decorating a function.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (appended to base_url)
            response_map: Mapping of status codes to response models
            data: Request body payload (for POST, PUT, etc.)
            query: Query parameters (optional)
            headers: Additional request headers (optional)
            **path_params: Path parameters to substitute in the URL path
        """
        url_path = self._substitute_path(path, path_params)
        data_payload = self._prepare_data_payload(data)
        response = self._send_request(
            method=method,
            url=url_path,
            query_params=query,
            data_payload=data_payload,
            headers_override=headers,
            response_map=response_map,
        )
        return self._parse_response(
            response=response,
            annotation=inspect._empty,
            response_map=response_map,
        )

    async def arequest(
        self,
        method: str,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]],
        data: dict[str, typing.Any] | pydantic.BaseModel | None = None,
        query: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        **path_params: typing.Any,
    ) -> typing.Any:
        """
        Execute an async HTTP request and hydrate the response according to the provided response_map.

        This method can be used for making requests without decorating a function.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (appended to base_url)
            response_map: Mapping of status codes to response models
            data: Request body payload (for POST, PUT, etc.)
            query: Query parameters (optional)
            headers: Additional request headers (optional)
            **path_params: Path parameters to substitute in the URL path
        """
        url_path = self._substitute_path(path, path_params)
        data_payload = self._prepare_data_payload(data)
        response = await self._send_request_async(
            method=method,
            url=url_path,
            query_params=query,
            data_payload=data_payload,
            headers_override=headers,
            response_map=response_map,
        )
        return self._parse_response(
            response=response,
            annotation=inspect._empty,
            response_map=response_map,
        )

    def _prepare_data_payload(
        self, data: dict[str, typing.Any] | pydantic.BaseModel | None
    ) -> dict[str, typing.Any] | None:
        if isinstance(data, pydantic.BaseModel):
            return data.model_dump(mode="json")

        return data

    def get(
        self,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        return self._create_decorator(
            "GET",
            path,
            response_map=response_map,
            response_parser=response_parser,
            streaming_response=streaming_response,
        )

    def post(
        self,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        return self._create_decorator(
            "POST",
            path,
            response_map=response_map,
            response_parser=response_parser,
            streaming_response=streaming_response,
        )

    def put(
        self,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        return self._create_decorator(
            "PUT",
            path,
            response_map=response_map,
            response_parser=response_parser,
            streaming_response=streaming_response,
        )

    def patch(
        self,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        return self._create_decorator(
            "PATCH",
            path,
            response_map=response_map,
            response_parser=response_parser,
            streaming_response=streaming_response,
        )

    def delete(
        self,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        return self._create_decorator(
            "DELETE",
            path,
            response_map=response_map,
            response_parser=response_parser,
            streaming_response=streaming_response,
        )

    def _create_decorator(
        self,
        method: str,
        path: str,
        *,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
        streaming_response: bool = False,
    ) -> typing.Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            context = requests.build_request_context(
                method,
                path,
                func,
                response_map=response_map,
                response_parser=response_parser,
                streaming=streaming_response,
            )

            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                    if streaming_response:
                        return await self._execute_async_stream(context, args, kwargs)
                    return await self._execute_async(context, args, kwargs)

                # Preserve the original signature for IDE support
                async_wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
                return typing.cast(_F, async_wrapper)

            @functools.wraps(func)
            def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                if streaming_response:
                    return self._execute_sync_stream(context, args, kwargs)
                return self._execute_sync(context, args, kwargs)

            # Preserve the original signature for IDE support
            wrapper.__signature__ = context.signature  # type: ignore[attr-defined]
            return typing.cast(_F, wrapper)

        return decorator

    def _prepare_call(
        self, context: requests.RequestContext, args: tuple[typing.Any, ...], kwargs: dict[str, typing.Any]
    ) -> requests.PreparedCall:
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

        path_params: dict[str, typing.Any] = {}
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

        data_payload: dict[str, typing.Any] | None = None
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

        return requests.PreparedCall(
            context=context,
            bound_arguments=bound_arguments,
            call_arguments=call_arguments,
            url_path=url_path,
            query_params=query_params,
            data_payload=data_payload,
            headers_override=headers_override,
            result_annotation=result_annotation,
        )

    def _execute_sync(
        self, context: requests.RequestContext, args: tuple[typing.Any, ...], kwargs: dict[str, typing.Any]
    ) -> typing.Any:
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
        return result

    async def _execute_async(
        self, context: requests.RequestContext, args: tuple[typing.Any, ...], kwargs: dict[str, typing.Any]
    ) -> typing.Any:
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
        return await result

    async def _execute_async_stream(
        self, context: requests.RequestContext, args: tuple[typing.Any, ...], kwargs: dict[str, typing.Any]
    ) -> typing.Any:
        """
        Execute an async streaming request.
        """

        prepared = self._prepare_call(context, args, kwargs)

        # Extract the inner type from AsyncIterator[T]
        inner_type = type_utils.get_streaming_inner_type(prepared.result_annotation)

        # Build request kwargs
        headers = {**self.config.headers, **(prepared.headers_override or {})}
        request_kwargs: dict[str, typing.Any] = {
            "params": prepared.query_params,
            "headers": headers,
        }
        if prepared.data_payload is not None:
            request_kwargs["json"] = prepared.data_payload

        if self.config.logger is not None:
            self.config.logger.debug(f"HTTP Streaming Request: {context.method} {prepared.url_path}")

        # For streaming, response_parser must accept str, not Response
        # Type narrowing: in streaming mode, parser is Callable[[str], Any] | None
        streaming_parser: typing.Callable[[str], typing.Any] | None = None
        if context.response_parser is not None:
            # In streaming context, this is guaranteed to be Callable[[str], Any]
            streaming_parser = context.response_parser  # type: ignore[assignment]

        if not self.config.http_backend:
            raise RuntimeError("HTTP backend is not configured.")
        stream_generator = self.config.http_backend.handle_async_stream(
            method=context.method,
            url=prepared.url_path,
            inner_type=inner_type,
            response_parser=streaming_parser,
            **request_kwargs,
        )

        # Inject the generator as 'result' and call the user's function
        prepared.call_arguments["result"] = stream_generator

        # The user's function should just return the result
        result = prepared.context.func(**prepared.call_arguments)

        # The user function should return the generator (or yield from it)
        if inspect.isawaitable(result):
            result = await result

        return result

    def _execute_sync_stream(
        self, context: requests.RequestContext, args: tuple[typing.Any, ...], kwargs: dict[str, typing.Any]
    ) -> typing.Any:
        """
        Execute a sync streaming request.

        Uses the HTTP backend's streaming handler for true streaming
        without buffering the entire response into memory. Streams line-by-line.

        For Server-Sent Events (SSE) format parsing, use a custom response_parser
        that extracts the data from SSE fields (e.g., "data: {json}").
        """

        prepared = self._prepare_call(context, args, kwargs)

        # Extract the inner type from Iterator[T]
        inner_type = type_utils.get_streaming_inner_type(prepared.result_annotation)

        if self.config.http_backend is None:
            raise RuntimeError("HTTP backend is not configured.")

        # Build request kwargs
        headers = {**self.config.headers, **(prepared.headers_override or {})}
        request_kwargs: dict[str, typing.Any] = {
            "params": prepared.query_params,
            "headers": headers,
        }
        if prepared.data_payload is not None:
            request_kwargs["json"] = prepared.data_payload

        if self.config.logger is not None:
            self.config.logger.debug(f"HTTP Streaming Request: {context.method} {prepared.url_path}")

        # For streaming, response_parser must accept str, not Response
        # Type narrowing: in streaming mode, parser is Callable[[str], Any] | None
        streaming_parser: typing.Callable[[str], typing.Any] | None = None
        if context.response_parser is not None:
            # In streaming context, this is guaranteed to be Callable[[str], Any]
            streaming_parser = context.response_parser  # type: ignore[assignment]

        stream_generator = self.config.http_backend.handle_sync_stream(
            method=context.method,
            url=prepared.url_path,
            inner_type=inner_type,
            response_parser=streaming_parser,
            **request_kwargs,
        )

        # Inject the generator as 'result' and call the user's function
        prepared.call_arguments["result"] = stream_generator

        # The user's function should just return the result
        result = prepared.context.func(**prepared.call_arguments)

        return result

    def _prepare_body(
        self, call_arguments: dict[str, typing.Any], data_param: inspect.Parameter | None, data_annotation: typing.Any
    ) -> dict[str, typing.Any] | None:
        if data_param is None:
            return None

        payload = call_arguments.get("data")
        if payload is None:
            return None

        annotation = data_annotation
        if annotation is inspect._empty:
            return payload

        if isinstance(payload, pydantic.BaseModel):
            return payload.model_dump(mode="json")

        if type_utils.is_pydantic_model(annotation):
            model_instance = annotation.model_validate(payload)
            return model_instance.model_dump(mode="json")

        if type_utils.is_typeddict(annotation):
            if not isinstance(payload, dict):
                raise TypeError(f"Expected dict for TypedDict {annotation.__name__}, got {type(payload).__name__}")
            return payload

        return payload

    def _send_request(
        self,
        *,
        method: str,
        url: str,
        query_params: dict[str, typing.Any] | None,
        data_payload: dict[str, typing.Any] | None,
        headers_override: dict[str, str] | None,
        response_map: dict[int, type[typing.Any]] | None = None,
    ) -> http_response.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        request_kwargs: dict[str, typing.Any] = {"params": query_params, "headers": headers}
        if data_payload is not None:
            request_kwargs["json"] = data_payload

        if self.config.http_backend is None:
            raise RuntimeError("HTTP backend is not configured.")

        if self.config.logger:
            self.config.logger.debug(f"HTTP Request: {method} {url}")
            self.config.logger.debug(f"Request Query Params: {query_params}")
            self.config.logger.debug(f"Request Payload: {data_payload}")
            self.config.logger.debug(f"Request Headers: {headers}")

        start_time = time.perf_counter()
        response = self.config.http_backend.send_sync_request(method, url, **request_kwargs)
        elapsed_time = time.perf_counter() - start_time

        if self.config.logger:
            self.config.logger.debug(f"HTTP Response: {method} {url} -> {response.status_code} ({elapsed_time:.3f}s)")
            self.config.logger.debug(f"Response Content: {response.text}")
            self.config.logger.debug(f"Response Headers: {response.headers}")

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
        query_params: dict[str, typing.Any] | None,
        data_payload: dict[str, typing.Any] | None,
        headers_override: dict[str, str] | None,
        response_map: dict[int, type[typing.Any]] | None = None,
    ) -> http_response.Response:
        headers = {**self.config.headers, **(headers_override or {})}

        request_kwargs: dict[str, typing.Any] = {"params": query_params, "headers": headers}
        if data_payload is not None:
            request_kwargs["json"] = data_payload

        if self.config.http_backend is None:
            raise RuntimeError("HTTP backend is not configured.")

        if self.config.logger is not None:
            self.config.logger.debug(f"HTTP Request: {method} {url}")

        start_time = time.perf_counter()
        response = await self.config.http_backend.send_async_request(method, url, **request_kwargs)
        elapsed_time = time.perf_counter() - start_time

        if self.config.logger:
            self.config.logger.debug(
                f"HTTP Response: {method} {url} -> {response.status_code} ({elapsed_time:.3f}s)\n"
                f"Content: {response.text}"
            )

        # Only raise for status if we don't have a response_map
        # If we have a response_map, we want to handle error responses
        if response_map is None:
            response.raise_for_status()
        return response

    def _finalise_call(
        self,
        prepared: requests.PreparedCall,
        response: http_response.Response,
    ) -> typing.Any:
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
        response: http_response.Response,
        annotation: typing.Any,
        response_map: dict[int, type[typing.Any]] | None = None,
        response_parser: typing.Callable[[http_response.Response], typing.Any]
        | typing.Callable[[str], typing.Any]
        | None = None,
    ) -> typing.Any:
        # Extract payload from response
        payload: typing.Any
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
            # For non-streaming, parser accepts Response; for streaming it accepts str
            return response_parser(response)  # type: ignore[arg-type]

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
            if type_utils.is_pydantic_model(model_class):
                return type_utils.validate_model(model_class, payload)
            elif type_utils.is_typeddict(model_class):
                return type_utils.validate_typeddict(model_class, payload)
            else:
                # Use TypeAdapter for complex types like list[Model], dict, etc.
                adapter = pydantic.TypeAdapter(model_class)
                return adapter.validate_python(payload)

        # Standard parsing logic when no response_map
        if annotation is inspect._empty:
            return payload

        if payload is None:
            return None

        if type_utils.is_pydantic_model(annotation):
            return type_utils.validate_model(annotation, payload)

        if type_utils.is_typeddict(annotation):
            return type_utils.validate_typeddict(annotation, payload)

        adapter = pydantic.TypeAdapter(annotation)
        return adapter.validate_python(payload)

    def _substitute_path(self, path_template: str, values: dict[str, typing.Any]) -> str:
        def replacer(match: re.Match[str]) -> str:
            key = match.group(1)
            return parse.quote(str(values.get(key)), safe="")

        return _PATH_PARAM_PATTERN.sub(replacer, path_template)
