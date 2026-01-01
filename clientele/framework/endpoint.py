"""
Non-decorator endpoint API for clientele.

Provides an escape hatch for defining endpoints without decorators while
maintaining full feature parity with decorator-based endpoints.

Example usage:
    from clientele import endpoint
    from schemas import User, NotFoundError

    # Create endpoint
    get_user = endpoint.get(
        "/users/{user_id}",
        response_map={200: User, 404: NotFoundError},
    )

    # Attach signature via stub function
    @get_user.signature
    def _(user_id: int, expand: bool = False) -> User | NotFoundError:
        ...

    # Bind to client
    get_user = get_user.bind(client)

    # Call like normal function
    result = get_user(user_id=123, expand=True)
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from clientele.framework.client import Client, _RequestContext

_F = TypeVar("_F", bound=Callable[..., Any])


class Endpoint:
    """
    Represents an unbound HTTP endpoint that can be bound to a client.

    Endpoints are created via endpoint.get(), endpoint.post(), etc.
    They must be bound to a client instance via .bind(client) before use.
    """

    def __init__(
        self,
        method: str,
        path: str,
        response_map: dict[int, type[BaseModel]] | None = None,
    ) -> None:
        self.method = method
        self.path = path
        self.response_map = response_map
        self._signature_func: Callable[..., Any] | None = None

    def signature(self, func: _F) -> Endpoint:
        """
        Attach a signature to this endpoint via a stub function.

        The stub function is never executed - it's only used to capture
        the function signature and type annotations for IDE support.

        Example:
            get_user = endpoint.get("/users/{user_id}")

            @get_user.signature
            def _(user_id: int, expand: bool = False) -> User:
                ...

        Args:
            func: A stub function with the desired signature

        Returns:
            self (for method chaining)
        """
        self._signature_func = func
        return self

    def bind(self, client: Client) -> Callable[..., Any]:
        """
        Bind this endpoint to a client instance, returning a callable.

        The returned callable will execute HTTP requests using the bound client
        and behaves identically to decorator-defined endpoints.

        Args:
            client: The Client instance to bind to

        Returns:
            A callable that executes the HTTP request when called
        """
        # Create a stub function if one wasn't provided via .signature()
        if self._signature_func is None:
            # Create a minimal stub with *args, **kwargs
            # We'll need to handle parameter extraction differently
            def default_stub(*args: Any, **kwargs: Any) -> Any: ...

            stub_func = default_stub
            has_custom_signature = False
        else:
            stub_func = self._signature_func
            has_custom_signature = True

        # Save the original signature before creating context
        sig = inspect.signature(stub_func)

        # Get type hints with proper handling of forward references
        # This follows the pattern used in FastAPI and other frameworks
        from typing import get_type_hints as typing_get_type_hints

        try:
            type_hints = typing_get_type_hints(stub_func, include_extras=True)
        except (NameError, AttributeError):
            # Forward references that can't be resolved - use raw annotations
            type_hints = stub_func.__annotations__.copy()

        # Create context without validation (endpoint stubs are exempt)
        context = _RequestContext(
            method=self.method,
            path_template=self.path,
            func=stub_func,
            signature=sig,
            type_hints=type_hints,
            response_map=self.response_map,
        )

        # Check if the client is async by checking if it has async methods
        # We'll determine sync vs async based on whether the stub is async
        is_async = inspect.iscoroutinefunction(stub_func)

        if is_async:

            @wraps(stub_func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # For endpoints without custom signatures, we need to handle kwargs specially
                if not has_custom_signature:
                    # All kwargs should be treated as potential path/query/data params
                    return await client._execute_async(context, args, kwargs)
                return await client._execute_async(context, args, kwargs)

            # Preserve the original signature for IDE support
            async_wrapper.__signature__ = sig  # type: ignore[attr-defined]
            return async_wrapper
        else:

            @wraps(stub_func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # For endpoints without custom signatures, we need to handle kwargs specially
                if not has_custom_signature:
                    # All kwargs should be treated as potential path/query/data params
                    return client._execute_sync(context, args, kwargs)
                return client._execute_sync(context, args, kwargs)

            # Preserve the original signature for IDE support
            wrapper.__signature__ = sig  # type: ignore[attr-defined]
            return wrapper


def get(path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Endpoint:
    """
    Create a GET endpoint.

    Args:
        path: URL path template (e.g., "/users/{user_id}")
        response_map: Optional mapping of status codes to response models

    Returns:
        An Endpoint object that can be bound to a client

    Example:
        get_user = endpoint.get("/users/{user_id}", response_map={200: User, 404: NotFoundError})
        get_user = get_user.bind(client)
    """
    return Endpoint("GET", path, response_map)


def post(path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Endpoint:
    """
    Create a POST endpoint.

    Args:
        path: URL path template (e.g., "/users")
        response_map: Optional mapping of status codes to response models

    Returns:
        An Endpoint object that can be bound to a client

    Example:
        create_user = endpoint.post("/users", response_map={201: User, 422: ValidationError})
        create_user = create_user.bind(client)
    """
    return Endpoint("POST", path, response_map)


def put(path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Endpoint:
    """
    Create a PUT endpoint.

    Args:
        path: URL path template (e.g., "/users/{user_id}")
        response_map: Optional mapping of status codes to response models

    Returns:
        An Endpoint object that can be bound to a client

    Example:
        update_user = endpoint.put("/users/{user_id}", response_map={200: User})
        update_user = update_user.bind(client)
    """
    return Endpoint("PUT", path, response_map)


def patch(path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Endpoint:
    """
    Create a PATCH endpoint.

    Args:
        path: URL path template (e.g., "/users/{user_id}")
        response_map: Optional mapping of status codes to response models

    Returns:
        An Endpoint object that can be bound to a client

    Example:
        patch_user = endpoint.patch("/users/{user_id}", response_map={200: User})
        patch_user = patch_user.bind(client)
    """
    return Endpoint("PATCH", path, response_map)


def delete(path: str, *, response_map: dict[int, type[BaseModel]] | None = None) -> Endpoint:
    """
    Create a DELETE endpoint.

    Args:
        path: URL path template (e.g., "/users/{user_id}")
        response_map: Optional mapping of status codes to response models

    Returns:
        An Endpoint object that can be bound to a client

    Example:
        delete_user = endpoint.delete("/users/{user_id}")
        delete_user = delete_user.bind(client)
    """
    return Endpoint("DELETE", path, response_map)
