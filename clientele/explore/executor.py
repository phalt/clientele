"""Request executor for running API operations."""

from __future__ import annotations

import asyncio
import inspect
import time
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from clientele.explore.introspector import ClientIntrospector
    from clientele.explore.session import SessionConfig


@dataclass
class ExecutionResult:
    """Result of executing an API operation."""

    success: bool
    response: typing.Any
    duration: float
    operation: str
    error: Exception | None = None
    debug_info: dict[str, typing.Any] | None = None  # HTTP request/response details


class RequestExecutor:
    """Executes API operations using the generated client."""

    def __init__(self, introspector: ClientIntrospector, session_config: SessionConfig | None = None):
        """Initialize the executor.

        Args:
            introspector: Client introspector for operation discovery
            session_config: Session configuration (for debug mode)
        """
        self.introspector = introspector
        self.session_config = session_config

    def execute(self, operation_name: str, args: dict[str, typing.Any]) -> ExecutionResult:
        """Execute an API operation.

        Args:
            operation_name: Name of the operation to execute
            args: Arguments to pass to the operation

        Returns:
            ExecutionResult with response data and metadata
        """
        # Get operation info
        op_info = self.introspector.operations.get(operation_name)
        if not op_info:
            return ExecutionResult(
                success=False,
                response=None,
                duration=0.0,
                operation=operation_name,
                error=ValueError(f"Operation not found: {operation_name}"),
            )

        # Initialize timing variable
        start_time = time.time()
        debug_info: dict[str, typing.Any] | None = (
            {} if self.session_config and self.session_config.debug_mode else None
        )

        try:
            # Validate arguments
            self._validate_args(op_info, args)

            # Convert dict arguments to Pydantic models where needed
            args = self._convert_dict_args_to_models(op_info, args)

            # Execute the operation
            start_time = time.time()

            if self.introspector.is_class_based:
                # For class-based clients, call the method on the instance
                method = getattr(self.introspector.client_instance, operation_name)
            else:
                # For function-based clients, use the function directly
                method = op_info.function

            # Capture debug info if enabled
            if debug_info is not None:
                debug_info["operation"] = operation_name
                debug_info["method"] = op_info.http_method
                debug_info["args"] = args
                # Try to get base URL from config
                try:
                    import sys

                    package_name = self.introspector.client_path.name
                    config_module_name = f"{package_name}.config"
                    if config_module_name in sys.modules:
                        config_module = sys.modules[config_module_name]
                        if hasattr(config_module, "api_base_url"):
                            debug_info["base_url"] = config_module.api_base_url()
                except Exception:
                    pass

            # Check if the operation is async
            if inspect.iscoroutinefunction(method):
                # Run async operation in event loop
                result = asyncio.run(method(**args))
            else:
                # Run sync operation normally
                result = method(**args)

            duration = time.time() - start_time

            # Add response info to debug
            if debug_info is not None:
                debug_info["response_type"] = type(result).__name__
                if hasattr(result, "__dict__"):
                    debug_info["response_preview"] = str(result)[:200]

            return ExecutionResult(
                success=True,
                response=result,
                duration=duration,
                operation=operation_name,
                error=None,
                debug_info=debug_info,
            )

        except Exception as e:
            duration = time.time() - start_time

            # Add error info to debug
            if debug_info is not None:
                debug_info["error"] = str(e)
                debug_info["error_type"] = type(e).__name__

            return ExecutionResult(
                success=False,
                response=None,
                duration=duration,
                operation=operation_name,
                error=e,
                debug_info=debug_info,
            )

    def _validate_args(self, op_info, args: dict[str, typing.Any]) -> None:
        """Validate arguments against operation signature.

        Args:
            op_info: OperationInfo object
            args: Arguments to validate

        Raises:
            ValueError: If validation fails
        """
        # Check for missing required arguments
        for param_name, param_info in op_info.parameters.items():
            if param_info["required"] and param_name not in args:
                raise ValueError(f"Missing required parameter: {param_name}")

        # Check for unknown arguments
        valid_params = set(op_info.parameters.keys())
        for arg_name in args:
            if arg_name not in valid_params:
                raise ValueError(f"Unknown parameter: {arg_name}")

    def _convert_dict_args_to_models(self, op_info, args: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """Convert dictionary arguments to Pydantic models where needed.

        Args:
            op_info: OperationInfo object
            args: Arguments to convert

        Returns:
            Arguments with dicts converted to Pydantic models where appropriate
        """
        # Get type hints for the operation function
        try:
            type_hints = typing.get_type_hints(op_info.function)
        except Exception:
            # If we can't get type hints, return args unchanged
            return args

        converted_args = {}
        for arg_name, arg_value in args.items():
            # Only convert if the argument is a dict
            if not isinstance(arg_value, dict):
                converted_args[arg_name] = arg_value
                continue

            # Get the expected type for this parameter
            expected_type = type_hints.get(arg_name)
            if expected_type is None:
                converted_args[arg_name] = arg_value
                continue

            # Handle Optional types - unwrap to get the actual type
            origin = typing.get_origin(expected_type)
            if origin is typing.Union:
                # For Optional[X], get X (the non-None type)
                type_args = typing.get_args(expected_type)
                non_none_types = [t for t in type_args if t is not type(None)]
                if len(non_none_types) == 1:
                    expected_type = non_none_types[0]

            # Check if the expected type is a Pydantic model
            if self._is_pydantic_model(expected_type):
                try:
                    # Instantiate the Pydantic model from the dict
                    converted_args[arg_name] = expected_type(**arg_value)
                except Exception as e:
                    # If conversion fails, raise a helpful error with the validation details
                    error_type = type(e).__name__
                    raise ValueError(
                        f"Failed to convert dict to {expected_type.__name__} for parameter '{arg_name}'. "
                        f"{error_type}: {e}"
                    ) from e
            else:
                # Not a Pydantic model, keep the dict as is
                converted_args[arg_name] = arg_value

        return converted_args

    def _is_pydantic_model(self, type_obj: typing.Any) -> bool:
        """Check if a type is a Pydantic model.

        Args:
            type_obj: Type to check

        Returns:
            True if the type is a Pydantic model, False otherwise
        """
        # Check if it's a class with model_fields (Pydantic v2) or __fields__ (Pydantic v1)
        return inspect.isclass(type_obj) and (hasattr(type_obj, "model_fields") or hasattr(type_obj, "__fields__"))
