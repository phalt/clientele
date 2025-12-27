"""Special commands handler for the REPL."""

from __future__ import annotations

import typing

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

if typing.TYPE_CHECKING:
    from clientele.explore.introspector import ClientIntrospector
    from clientele.explore.session import SessionConfig


class CommandHandler:
    """Handles special commands in the REPL."""

    def __init__(
        self,
        introspector: ClientIntrospector,
        session_config: SessionConfig | None = None,
        console: Console | None = None,
    ):
        """Initialize the command handler.

        Args:
            introspector: Client introspector for operation discovery
            session_config: Session configuration
            console: Rich console for output
        """
        self.introspector = introspector
        self.session_config = session_config
        self.console = console or Console()
        self._temp_config_instance = None  # Store temporary config instance

    def _get_config_instance(self, config_module):
        """Get or create a config instance from the config module.

        This handles three cases:
        1. Module has a singleton 'config' instance (functional clients)
        2. Module has a 'Config' class but no singleton (class-based clients)
        3. Old function-based config (backward compatibility)

        Args:
            config_module: The loaded config module

        Returns:
            The config instance if available, None otherwise
        """
        # Case 1: Module has singleton config instance
        if hasattr(config_module, "config"):
            return config_module.config

        # Case 2: Module has Config class but no singleton - create temporary instance
        if hasattr(config_module, "Config"):
            # Reuse the same temporary instance across calls
            if self._temp_config_instance is None:
                try:
                    # Try to instantiate with no arguments (default config)
                    self._temp_config_instance = config_module.Config()
                except Exception:
                    # If instantiation fails, we can't use this config
                    return None
            return self._temp_config_instance

        # Case 3: Old function-based config (return None, will be handled separately)
        return None

    def handle_command(self, command: str) -> bool:
        """Handle a special command.

        Args:
            command: Command string (including the leading /)

        Returns:
            True if should exit REPL, False otherwise
        """
        command = command.strip()
        parts = command.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd in ["/exit", "/quit"]:
            return True
        elif cmd in ["/list", "/operations"]:
            self._list_operations()
        elif cmd == "/schemas":
            if arg:
                self._show_schema_detail(arg)
            else:
                self._list_schemas()
        elif cmd == "/config":
            self._handle_config(arg)
        elif cmd == "/debug":
            self._handle_debug(arg)
        elif cmd == "/help":
            self._show_help()
        else:
            self.console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            self.console.print("Type [cyan]/help[/cyan] for available commands")

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
  • Inspect schemas by typing their name: [cyan]SchemaName[/cyan]
  • Use UP/DOWN arrows to navigate command history

[bold]Special Commands:[/bold]
  [cyan]/list[/cyan], [cyan]/operations[/cyan]  - List all available operations
  [cyan]/schemas[/cyan]              - List all available schemas
  [cyan]/schemas <name>[/cyan]       - Show details for a specific schema
  [cyan]/config[/cyan]               - Show current configuration
  [cyan]/config set <key> <value>[/cyan] - Set a configuration value
  [cyan]/debug on[/cyan]             - Enable request/response logging
  [cyan]/debug off[/cyan]            - Disable request/response logging
  [cyan]/help[/cyan]                  - Show this help message
  [cyan]/exit[/cyan], [cyan]/quit[/cyan]         - Exit the REPL

[bold]Examples:[/bold]
  [cyan]get_users()[/cyan]                           - Execute operation without parameters
  [cyan]get_user(user_id="123")[/cyan]               - Execute with parameters
  [cyan]create_user(data={"name": "John"})[/cyan]   - Pass complex data
  [cyan]UserResponse[/cyan]                          - Inspect a schema
  [cyan]/schemas[/cyan]                              - List all schemas
  [cyan]/schemas User[/cyan]                         - Show User schema details
  [cyan]/config[/cyan]                               - Show current config
  [cyan]/config set base_url https://api.example.com[/cyan] - Set base URL
  [cyan]/debug on[/cyan]                             - Enable debug mode

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
        self.console.print("[dim]Use [cyan].schemas <name>[/cyan] to see details[/dim]")

    def _show_schema_detail(self, schema_name: str) -> None:
        """Show detailed information about a specific schema.

        Args:
            schema_name: Name of the schema to inspect
        """

        schema_info = self.introspector.get_schema_info(schema_name)

        if not schema_info:
            self.console.print(f"[red]Schema not found: {schema_name}[/red]")
            self.console.print("[dim]Use [cyan]/schemas[/cyan] to see all available schemas[/dim]")
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

            for field_name, field_data in schema_info["fields"].items():
                field_type = field_data.get("type", "Unknown")
                # Simplify type display - remove verbose typing module prefixes
                field_type_str = self._simplify_type_display(str(field_type))
                required = "✓" if field_data.get("required", True) else "✗"

                fields_table.add_row(field_name, field_type_str, required)

            self.console.print(fields_table)
            self.console.print(f"\n[dim]Total: {len(schema_info['fields'])} fields[/dim]")

    def _simplify_type_display(self, type_str: str) -> str:
        """Simplify type display by removing verbose prefixes.

        Args:
            type_str: Type string to simplify

        Returns:
            Simplified type string
        """
        # Remove common verbose patterns
        replacements = {
            "typing.": "",
            "Annotated[": "",
            ", ...]": "]",
        }
        for old, new in replacements.items():
            type_str = type_str.replace(old, new)

        # Shorten very long type strings
        return type_str[:47] + "..." if len(type_str) > 50 else type_str

    def _handle_config(self, arg: str | None) -> None:
        """Handle /config command.

        Args:
            arg: Optional arguments (e.g., "set key value")
        """
        if not arg:
            # Show current configuration
            self._show_config()
        elif arg.startswith("set "):
            # Set configuration value
            parts = arg[4:].split(maxsplit=1)
            if len(parts) != 2:
                self.console.print("[red]Usage: /config set <key> <value>[/red]")
                self.console.print("[dim]Example: /config set base_url https://pokeapi.co[/dim]")
                return
            key, value = parts
            self._set_config(key, value)
        else:
            self.console.print(f"[yellow]Unknown config command: {arg}[/yellow]")
            self.console.print("[dim]Use '/config' to show config or '/config set <key> <value>' to set values[/dim]")

    def _show_config(self) -> None:
        """Show current configuration from config module and runtime overrides."""
        import sys

        # Get the config module
        package_name = self.introspector.client_path.name
        config_module_name = f"{package_name}.config"

        if config_module_name not in sys.modules:
            self.console.print("[yellow]No configuration module found[/yellow]")
            return

        config_module = sys.modules[config_module_name]

        # Create configuration table
        table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        table.add_column("Source", style="yellow")

        # Get config instance (if available)
        config_instance = self._get_config_instance(config_module)

        # Map of display names to attribute/function names
        config_attrs = {
            "base_url": "api_base_url",
            "bearer_token": "bearer_token",
            "user_key": "user_key",
            "pass_key": "pass_key",
        }

        for display_name, attr_name in config_attrs.items():
            try:
                # Check for runtime override first
                if self.session_config and display_name in self.session_config.config_overrides:
                    value = self.session_config.config_overrides[display_name]
                    source = "runtime"
                else:
                    # Try new Pydantic Config class format first
                    if config_instance is not None:
                        if hasattr(config_instance, attr_name):
                            value = getattr(config_instance, attr_name)
                            source = "config.py"
                        else:
                            continue
                    # Fall back to old function-based format
                    elif hasattr(config_module, attr_name):
                        func = getattr(config_module, attr_name)
                        # Try calling as function for old format (e.g., get_bearer_token())
                        if callable(func):
                            value = func()
                        else:
                            value = func
                        source = "config.py"
                    # For old format with different function names
                    elif display_name == "bearer_token" and hasattr(config_module, "get_bearer_token"):
                        value = config_module.get_bearer_token()
                        source = "config.py"
                    elif display_name == "user_key" and hasattr(config_module, "get_user_key"):
                        value = config_module.get_user_key()
                        source = "config.py"
                    elif display_name == "pass_key" and hasattr(config_module, "get_pass_key"):
                        value = config_module.get_pass_key()
                        source = "config.py"
                    else:
                        continue

                # Mask sensitive values
                if display_name in ["bearer_token", "pass_key"] and value and value != "token" and value != "password":
                    value = "***" + value[-4:] if len(value) > 4 else "***"

                table.add_row(display_name, str(value), source)
            except Exception as e:
                table.add_row(display_name, f"[red]Error: {e}[/red]", "error")

        # Add additional headers
        if config_instance is not None:
            # New format: config.additional_headers (dict attribute)
            if hasattr(config_instance, "additional_headers"):
                headers = config_instance.additional_headers
                if headers:
                    for key, val in headers.items():
                        table.add_row(f"header.{key}", str(val), "config.py")
        elif hasattr(config_module, "additional_headers"):
            # Old format: additional_headers() function
            try:
                headers = config_module.additional_headers()
                if headers:
                    for key, val in headers.items():
                        table.add_row(f"header.{key}", str(val), "config.py")
            except Exception:
                pass

        self.console.print(table)

        # Show debug mode
        if self.session_config:
            debug_status = "[green]ON[/green]" if self.session_config.debug_mode else "[dim]OFF[/dim]"
            self.console.print(f"\n[bold]Debug Mode:[/bold] {debug_status}")

        self.console.print("\n[dim]Use '/config set <key> <value>' to override values for this session[/dim]")
        self.console.print("[dim]Supported keys: base_url, bearer_token, user_key, pass_key[/dim]")

    def _set_config(self, key: str, value: str) -> None:
        """Set a configuration value for the current session.

        Args:
            key: Configuration key
            value: Configuration value
        """
        if not self.session_config:
            self.console.print("[red]Session config not available[/red]")
            return

        # Validate key
        valid_keys = ["base_url", "bearer_token", "user_key", "pass_key"]
        if key not in valid_keys:
            self.console.print(f"[red]Invalid config key: {key}[/red]")
            self.console.print(f"[dim]Supported keys: {', '.join(valid_keys)}[/dim]")
            return

        # Store the override
        self.session_config.config_overrides[key] = value
        self.console.print(f"[green]✓[/green] Set {key} = {value}")
        self.console.print("[dim]This override applies only to the current REPL session[/dim]")

        # Apply the override to the config module
        self._apply_config_override(key, value)

    def _apply_config_override(self, key: str, value: str) -> None:
        """Apply a config override to the loaded config module.

        Args:
            key: Configuration key
            value: Configuration value
        """
        import sys

        package_name = self.introspector.client_path.name
        config_module_name = f"{package_name}.config"

        if config_module_name not in sys.modules:
            return

        config_module = sys.modules[config_module_name]

        # Map display names to attribute names
        attr_map = {
            "base_url": "api_base_url",
            "bearer_token": "bearer_token",
            "user_key": "user_key",
            "pass_key": "pass_key",
        }

        attr_name = attr_map.get(key)
        if not attr_name:
            return

        # Get or create config instance using the helper method
        config_instance = self._get_config_instance(config_module)

        if config_instance is not None:
            # New Pydantic Config format: Update the instance attribute
            if hasattr(config_instance, attr_name):
                setattr(config_instance, attr_name, value)
        else:
            # Old function-based config format: Replace the function with a lambda
            # The old format had functions like get_bearer_token() that returned config values.
            # We replace these with lambdas that return the overridden value.
            # Map display names to old function names
            old_func_map = {
                "base_url": "api_base_url",
                "bearer_token": "get_bearer_token",
                "user_key": "get_user_key",
                "pass_key": "get_pass_key",
            }
            func_name = old_func_map.get(key)
            if func_name and hasattr(config_module, func_name):
                # Replace the old function with a new one that returns the override value
                # Note: Captures value at definition time (v=value) to avoid late-binding closure issues
                setattr(config_module, func_name, lambda v=value: v)

    def _handle_debug(self, arg: str | None) -> None:
        """Handle /debug command.

        Args:
            arg: "on" or "off" to enable/disable debug mode
        """
        if not self.session_config:
            self.console.print("[red]Session config not available[/red]")
            return

        if not arg:
            # Show current debug status
            status = "[green]ON[/green]" if self.session_config.debug_mode else "[dim]OFF[/dim]"
            self.console.print(f"[bold]Debug Mode:[/bold] {status}")
            self.console.print("\n[dim]Use '/debug on' or '/debug off' to toggle debug mode[/dim]")
            return

        arg = arg.lower()
        if arg == "on":
            self.session_config.debug_mode = True
            self.console.print("[green]✓ Debug mode enabled[/green]")
            self.console.print("[dim]HTTP requests and responses will be logged[/dim]")
        elif arg == "off":
            self.session_config.debug_mode = False
            self.console.print("[yellow]Debug mode disabled[/yellow]")
        else:
            self.console.print(f"[red]Invalid argument: {arg}[/red]")
            self.console.print("[dim]Use '/debug on' or '/debug off'[/dim]")
