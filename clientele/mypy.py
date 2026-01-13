"""Mypy plugin for clientele decorators.

This plugin removes injected parameters ('result' and 'response') from the
signature of functions/methods decorated with clientele.api.APIClient decorators
(@client.get, @client.post, etc.).

These parameters are used internally by clientele for dependency injection
and should not be passed by callers.

The plugin detects HTTP method decorators (.get, .post, .put, etc.) to identify
clientele-decorated methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mypy.options import Options
    from mypy.plugin import CheckerPluginInterface
    from mypy.types import Type

from mypy.nodes import CallExpr, Decorator, MemberExpr, NameExpr, TypeInfo
from mypy.plugin import AttributeContext, FunctionSigContext, Plugin
from mypy.types import CallableType, FunctionLike, Instance, UnionType, get_proper_type

# Parameters that clientele injects automatically
CLIENTELE_INJECTED_PARAMS = {"result", "response"}

# HTTP method names used by clientele.APIClient decorators
CLIENTELE_HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _is_http_method_decorator(decorator_expr: object) -> bool:
    """Check if decorator is an HTTP method call like @client.get(...).

    Returns True if the decorator is a call to .get(), .post(), .put(), etc.
    regardless of what object it's called on.
    """
    # Check if it's a call expression like @something.method(...)
    if isinstance(decorator_expr, CallExpr):
        # The callee should be a member access like client.get
        callee = decorator_expr.callee
        if isinstance(callee, MemberExpr):
            return callee.name in CLIENTELE_HTTP_METHODS

    # Also check if it's a direct member access like @client.get (without parens)
    if isinstance(decorator_expr, MemberExpr):
        return decorator_expr.name in CLIENTELE_HTTP_METHODS

    return False


def _has_http_method_decorator(node: object) -> bool:
    """Check if a function/method has an HTTP method decorator."""
    if not isinstance(node, Decorator):
        return False

    # Check all decorators for HTTP method patterns
    return any(_is_http_method_decorator(dec) for dec in node.original_decorators)


class ClientelePlugin(Plugin):
    """Plugin to handle clientele decorator parameter injection."""

    def __init__(self, options: Options) -> None:
        super().__init__(options)
        self._dict_type_info: TypeInfo | None = None

    def get_function_signature_hook(self, fullname: str) -> Callable[[FunctionSigContext], FunctionLike] | None:
        """Hook into function signatures to adjust clientele-decorated functions."""
        return self._adjust_function_signature

    def get_attribute_hook(self, fullname: str) -> Callable[[AttributeContext], Type] | None:
        """Hook into attribute access to adjust clientele-decorated methods."""

        # Store fullname for use in the callback
        def callback(ctx: AttributeContext) -> Type:
            return self._adjust_attribute_type(ctx, fullname)

        return callback

    def _adjust_function_signature(self, ctx: FunctionSigContext) -> CallableType:
        """Adjust signature for clientele-decorated functions.

        Check if the function being called has an HTTP method decorator
        (@something.get, @something.post, etc.) by inspecting the AST.
        """
        # Get the function being called from the call expression
        if isinstance(ctx.context, CallExpr):
            callee = ctx.context.callee

            # For plain functions, callee is a NameExpr
            if isinstance(callee, NameExpr) and callee.node and _has_http_method_decorator(callee.node):
                return self._remove_injected_params(ctx.default_signature, ctx.api)

            # For method calls, callee is a MemberExpr (e.g., self._api.user_repos)
            # The attribute hook should handle these, but we need to check here too
            if (
                isinstance(callee, MemberExpr)
                and hasattr(callee, "node")
                and callee.node
                and _has_http_method_decorator(callee.node)
            ):
                return self._remove_injected_params(ctx.default_signature, ctx.api)

        return ctx.default_signature

    def _adjust_attribute_type(self, ctx: AttributeContext, fullname: str) -> Type:
        """Remove clientele-injected parameters from method signature."""
        attr_type = ctx.default_attr_type

        # Only modify callable types (methods/functions)
        if not isinstance(attr_type, CallableType):
            return attr_type

        # Get the type from which this attribute is being accessed
        owner_type = get_proper_type(ctx.type)

        # For instance attributes, check the class's symbol table for decorators
        if isinstance(owner_type, Instance):
            type_info = owner_type.type

            # Extract attribute name from fullname (e.g., "Module.Class.method" -> "method")
            attr_name = fullname.rsplit(".", maxsplit=1)[-1]

            # Look up the symbol in the class's names
            if hasattr(type_info, "names") and attr_name in type_info.names:
                symbol = type_info.names[attr_name]

                # Check if this method has an HTTP method decorator
                if _has_http_method_decorator(symbol.node):
                    return self._remove_injected_params(attr_type, ctx.api)

        return attr_type

    def _remove_injected_params(self, signature: CallableType, api: CheckerPluginInterface) -> CallableType:
        """Remove clientele-injected parameters and allow dicts for Pydantic model params."""
        # Check if any injected parameters exist
        if not signature.arg_names:
            return signature

        # Check if 'result' or 'response' parameters exist
        has_injected_params = any(param in CLIENTELE_INJECTED_PARAMS for param in signature.arg_names)

        # Remove all clientele-injected parameters and modify parameter types
        new_arg_names = []
        new_arg_types = []
        new_arg_kinds = []
        modified_types = False

        for i, arg_name in enumerate(signature.arg_names):
            if arg_name not in CLIENTELE_INJECTED_PARAMS:
                new_arg_names.append(arg_name)
                arg_type = signature.arg_types[i]

                # For any parameter with Pydantic BaseModel type, accept dict too
                if self._is_pydantic_model_type(arg_type):
                    # Create Union[OriginalType, dict[str, Any]]
                    arg_type = self._make_data_param_accept_dict(arg_type, api)
                    modified_types = True

                new_arg_types.append(arg_type)
                new_arg_kinds.append(signature.arg_kinds[i])

        if not has_injected_params and not modified_types:
            # No changes needed
            return signature

        return signature.copy_modified(
            arg_names=new_arg_names,
            arg_types=new_arg_types,
            arg_kinds=new_arg_kinds,
        )

    def _is_pydantic_model_type(self, typ: Type) -> bool:
        """Check if a type is a Pydantic BaseModel instance."""
        proper_type = get_proper_type(typ)
        if not isinstance(proper_type, Instance):
            return False

        type_info = proper_type.type
        # Check if this type inherits from pydantic.BaseModel
        return self._has_base_named(type_info, "pydantic.main.BaseModel")

    def _has_base_named(self, type_info: TypeInfo, fullname: str) -> bool:
        """Check if type_info has a base class with the given fullname."""
        if type_info.fullname == fullname:
            return True

        for base in type_info.mro:
            if base.fullname == fullname:
                return True

        return False

    def _make_data_param_accept_dict(self, original_type: Type, api: CheckerPluginInterface) -> Type:
        """Create Union[OriginalType, dict[str, Any]] for data parameters."""
        from mypy.types import AnyType, TypeOfAny

        # Create dict[str, Any] using the API's named_generic_type method
        str_type = api.named_generic_type("builtins.str", [])
        any_type = AnyType(TypeOfAny.special_form)
        dict_type = api.named_generic_type("builtins.dict", [str_type, any_type])
        return UnionType([original_type, dict_type])


def plugin(version: str) -> type[ClientelePlugin]:
    """Entry point for mypy plugin."""
    return ClientelePlugin
