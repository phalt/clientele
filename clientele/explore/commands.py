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
        parts = command.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd in [".exit", ".quit"]:
            return True
        elif cmd in [".list", ".operations"]:
            self._list_operations()
        elif cmd == ".schemas":
            if arg:
                self._show_schema_detail(arg)
            else:
                self._list_schemas()
        elif cmd == ".help":
            self._show_help()
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
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
  [cyan].schemas[/cyan]              - List all available schemas
  [cyan].schemas <name>[/cyan]       - Show details for a specific schema
  [cyan].help[/cyan]                  - Show this help message
  [cyan].exit[/cyan], [cyan].quit[/cyan]         - Exit the REPL

[bold]Examples:[/bold]
  [cyan]get_users()[/cyan]                           - Execute operation without parameters
  [cyan]get_user(user_id="123")[/cyan]               - Execute with parameters
  [cyan]create_user(data={"name": "John"})[/cyan]   - Pass complex data
  [cyan].schemas[/cyan]                              - List all schemas
  [cyan].schemas User[/cyan]                         - Show User schema details

[bold]Tips:[/bold]
  • Press TAB to see available completions
  • Press Ctrl+D to exit
  • Press Ctrl+C to cancel current input
"""
        self.console.print(help_text)

    def _list_schemas(self) -> None:
        """List all available Pydantic schemas."""
        schemas = self.introspector.get_all_schemas()

        if not schemas:
            self.console.print("[yellow]No schemas found[/yellow]")
            return

        # Create a table
        table = Table(title="Available Schemas", show_header=True, header_style="bold magenta")
        table.add_column("Schema Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for schema_name in sorted(schemas.keys()):
            schema_class = schemas[schema_name]
            # Get first line of docstring
            doc = (
                typing.get_type_hints(schema_class).__doc__
                if hasattr(typing.get_type_hints(schema_class), "__doc__")
                else None
            )
            if not doc:
                import inspect as insp

                doc = insp.getdoc(schema_class)
            description = doc.split("\n")[0] if doc else ""

            table.add_row(schema_name, description)

        self.console.print(table)
        self.console.print(f"\n[dim]Total: {len(schemas)} schemas[/dim]")
        self.console.print(f"[dim]Use [cyan].schemas <name>[/cyan] to see details[/dim]")

    def _show_schema_detail(self, schema_name: str) -> None:
        """Show detailed information about a specific schema.

        Args:
            schema_name: Name of the schema to inspect
        """
        from rich.panel import Panel

        schema_info = self.introspector.get_schema_info(schema_name)

        if not schema_info:
            self.console.print(f"[red]Schema not found: {schema_name}[/red]")
            self.console.print("[dim]Use [cyan].schemas[/cyan] to see all available schemas[/dim]")
            return

        # Create title with schema name
        title = f"[bold cyan]{schema_info['name']}[/bold cyan]"

        # Build schema details
        details = []

        if schema_info.get("docstring"):
            details.append(f"[bold]Description:[/bold]\n{schema_info['docstring']}\n")

        if schema_info.get("fields"):
            details.append("[bold]Fields:[/bold]")

            # Create fields table
            fields_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
            fields_table.add_column("Field", style="cyan", no_wrap=True)
            fields_table.add_column("Type", style="green")
            fields_table.add_column("Required", style="yellow")
            fields_table.add_column("Description", style="white")

            for field_name, field_data in schema_info["fields"].items():
                field_type = field_data.get("type", "Unknown")
                required = "✓" if field_data.get("required", True) else "✗"
                description = field_data.get("description", "")
                if not description and field_data.get("default") is not None:
                    description = f"Default: {field_data['default']}"

                fields_table.add_row(field_name, str(field_type), required, description)

            # Convert table to string (this is a workaround to add to details list)
            from io import StringIO
            from rich.console import Console as TempConsole

            temp_console = TempConsole(file=StringIO(), width=120)
            temp_console.print(fields_table)
            # Just append the table to be printed later
            details.append("")  # Placeholder

        # Print the panel and then the fields table
        if schema_info.get("docstring"):
            self.console.print(Panel(f"{schema_info['docstring']}", title=title, border_style="cyan"))
        else:
            self.console.print(f"\n{title}\n")

        if schema_info.get("fields"):
            self.console.print("\n[bold]Fields:[/bold]")
            fields_table = Table(show_header=True, header_style="bold magenta")
            fields_table.add_column("Field", style="cyan", no_wrap=True)
            fields_table.add_column("Type", style="green")
            fields_table.add_column("Required", style="yellow")
            fields_table.add_column("Description", style="white")

            for field_name, field_data in schema_info["fields"].items():
                field_type = field_data.get("type", "Unknown")
                # Shorten long type strings
                if len(str(field_type)) > 50:
                    field_type = str(field_type)[:47] + "..."

                required = "✓" if field_data.get("required", True) else "✗"
                description = field_data.get("description", "")
                if not description and field_data.get("default") is not None:
                    description = f"Default: {field_data['default']}"

                fields_table.add_row(field_name, str(field_type), required, description)

            self.console.print(fields_table)
            self.console.print(f"\n[dim]Total: {len(schema_info['fields'])} fields[/dim]")
