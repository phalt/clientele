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
        debug_info = {} if self.session_config and self.session_config.debug_mode else None

        try:
            # Validate arguments
            self._validate_args(op_info, args)

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
