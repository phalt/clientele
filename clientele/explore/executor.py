"""Request executor for running API operations."""

from __future__ import annotations

import asyncio
import inspect
import time
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from clientele.explore.introspector import ClientIntrospector


@dataclass
class ExecutionResult:
    """Result of executing an API operation."""

    success: bool
    response: typing.Any
    duration: float
    operation: str
    error: Exception | None = None


class RequestExecutor:
    """Executes API operations using the generated client."""

    def __init__(self, introspector: ClientIntrospector):
        """Initialize the executor.

        Args:
            introspector: Client introspector for operation discovery
        """
        self.introspector = introspector

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

            # Check if the operation is async
            if inspect.iscoroutinefunction(method):
                # Run async operation in event loop
                result = asyncio.run(method(**args))
            else:
                # Run sync operation normally
                result = method(**args)

            duration = time.time() - start_time

            return ExecutionResult(
                success=True,
                response=result,
                duration=duration,
                operation=operation_name,
                error=None,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                response=None,
                duration=duration,
                operation=operation_name,
                error=e,
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
