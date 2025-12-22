"""Special commands handler for the REPL."""

from __future__ import annotations

import typing

from rich.console import Console
from rich.table import Table

if typing.TYPE_CHECKING:
    from clientele.explore.introspector import ClientIntrospector


class CommandHandler:
    """Handles special commands in the REPL."""

    def __init__(self, introspector: ClientIntrospector, console: Console | None = None):
        """Initialize the command handler.

        Args:
            introspector: Client introspector for operation discovery
            console: Rich console for output
        """
        self.introspector = introspector
        self.console = console or Console()

    def handle_command(self, command: str) -> bool:
        """Handle a special command.

        Args:
            command: Command string (including the leading .)

        Returns:
            True if should exit REPL, False otherwise
        """
        command = command.strip()

        if command in [".exit", ".quit"]:
            return True
        elif command in [".list", ".operations"]:
            self._list_operations()
        elif command == ".help":
            self._show_help()
        else:
            self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
            self.console.print("Type [cyan].help[/cyan] for available commands")

        return False

    def _list_operations(self) -> None:
        """List all available operations."""
        if not self.introspector.operations:
            self.console.print("[yellow]No operations found[/yellow]")
            return

        # Create a table
        table = Table(title="Available Operations", show_header=True, header_style="bold magenta")
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Method", style="green")
        table.add_column("Description", style="white")

        for op_name, op_info in sorted(self.introspector.operations.items()):
            # Get first line of docstring
            description = ""
            if op_info.docstring:
                description = op_info.docstring.split("\n")[0]

            table.add_row(op_name, op_info.http_method, description)

        self.console.print(table)
        self.console.print(f"\n[dim]Total: {len(self.introspector.operations)} operations[/dim]")

    def _show_help(self) -> None:
        """Show help message."""
        help_text = """
[bold cyan]Clientele Interactive API Explorer[/bold cyan]

[bold]Usage:[/bold]
  • Type operation names and press TAB to autocomplete
  • Execute operations with Python-like syntax: [cyan]operation_name(param=value)[/cyan]
  • Use UP/DOWN arrows to navigate command history

[bold]Special Commands:[/bold]
  [cyan].list[/cyan], [cyan].operations[/cyan]  - List all available operations
  [cyan].help[/cyan]                  - Show this help message
  [cyan].exit[/cyan], [cyan].quit[/cyan]         - Exit the REPL

[bold]Examples:[/bold]
  [cyan]get_users()[/cyan]                           - Execute operation without parameters
  [cyan]get_user(user_id="123")[/cyan]               - Execute with parameters
  [cyan]create_user(data={"name": "John"})[/cyan]   - Pass complex data

[bold]Tips:[/bold]
  • Press TAB to see available completions
  • Press Ctrl+D to exit
  • Press Ctrl+C to cancel current input
"""
        self.console.print(help_text)
