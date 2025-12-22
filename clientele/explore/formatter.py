"""Response formatting for beautiful output."""

from __future__ import annotations

import json
import typing

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

if typing.TYPE_CHECKING:
    from clientele.explore.executor import ExecutionResult


class ResponseFormatter:
    """Formats execution results for display."""

    def __init__(self, console: Console | None = None):
        """Initialize the formatter.

        Args:
            console: Rich console for output (creates new one if not provided)
        """
        self.console = console or Console()

    def format(self, result: ExecutionResult) -> None:
        """Format and display an execution result.

        Args:
            result: ExecutionResult to format and display
        """
        if not result.success:
            self._format_error(result)
        else:
            self._format_success(result)

    def _format_success(self, result: ExecutionResult) -> None:
        """Format a successful response.

        Args:
            result: ExecutionResult to format
        """
        # Show timing
        self.console.print(f"[green]✓ Success in {result.duration:.2f}s[/green]")

        # Show debug info if available
        if result.debug_info:
            self._format_debug_info(result.debug_info)

        # Format the response
        if result.response is None:
            self.console.print("[dim]No response body[/dim]")
            return

        # Try to convert to JSON for pretty printing
        try:
            # Handle Pydantic models
            if hasattr(result.response, "model_dump"):
                response_dict = result.response.model_dump()
            elif hasattr(result.response, "dict"):
                response_dict = result.response.dict()
            elif isinstance(result.response, dict):
                response_dict = result.response
            elif isinstance(result.response, (list, tuple)):
                # Handle lists
                if result.response and len(result.response) > 0 and hasattr(result.response[0], "model_dump"):
                    response_dict = [item.model_dump() for item in result.response]
                else:
                    response_dict = result.response
            else:
                # Fallback to string representation
                self.console.print(result.response)
                return

            # Pretty print JSON with syntax highlighting
            json_str = json.dumps(response_dict, indent=2, default=str)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(syntax)

        except Exception:
            # Fallback to simple print
            self.console.print(result.response)

    def _format_error(self, result: ExecutionResult) -> None:
        """Format an error response.

        Args:
            result: ExecutionResult with error
        """
        # Show timing
        self.console.print(f"[red]✗ Error in {result.duration:.2f}s[/red]")

        # Show debug info if available
        if result.debug_info:
            self._format_debug_info(result.debug_info)

        # Show error details
        if result.error:
            error_text = f"{type(result.error).__name__}: {str(result.error)}"
            panel = Panel(
                error_text,
                title="[red]Error[/red]",
                border_style="red",
            )
            self.console.print(panel)
        else:
            self.console.print("[red]Unknown error occurred[/red]")

    def _format_debug_info(self, debug_info: dict[str, typing.Any]) -> None:
        """Format debug information about the request.

        Args:
            debug_info: Dictionary containing debug information
        """
        from rich.table import Table

        self.console.print("\n[bold cyan]Debug Information:[/bold cyan]")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Key", style="yellow", no_wrap=True)
        table.add_column("Value", style="white")

        # Show relevant debug info
        if "operation" in debug_info:
            table.add_row("Operation", debug_info["operation"])
        if "method" in debug_info:
            table.add_row("HTTP Method", debug_info["method"])
        if "base_url" in debug_info:
            table.add_row("Base URL", debug_info["base_url"])
        if "args" in debug_info and debug_info["args"]:
            args_str = json.dumps(debug_info["args"], indent=2, default=str)
            table.add_row("Arguments", args_str)
        if "response_type" in debug_info:
            table.add_row("Response Type", debug_info["response_type"])
        if "error" in debug_info:
            table.add_row("Error Details", debug_info["error"])
        if "error_type" in debug_info:
            table.add_row("Error Type", debug_info["error_type"])

        self.console.print(table)
        self.console.print("")  # Empty line for spacing
