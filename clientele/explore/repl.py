"""Main REPL loop for the interactive API explorer."""

from __future__ import annotations

import ast
import typing

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import ThreadedCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.python import PythonLexer
from rich.console import Console

from clientele import settings
from clientele.explore.commands import CommandHandler
from clientele.explore.completer import ClienteleCompleter
from clientele.explore.executor import RequestExecutor
from clientele.explore.formatter import ResponseFormatter
from clientele.explore.introspector import ClientIntrospector
from clientele.explore.session import SessionConfig


class ClienteleREPL:
    """Interactive REPL for exploring APIs."""

    def __init__(self, introspector: ClientIntrospector, config: SessionConfig | None = None):
        """Initialize the REPL.

        Args:
            introspector: Client introspector for operation discovery
            config: Session configuration
        """
        self.introspector = introspector
        self.config = config or SessionConfig()
        self.console = Console()

        # Initialize components
        self.completer = ClienteleCompleter(introspector)
        self.executor = RequestExecutor(introspector, self.config)
        self.formatter = ResponseFormatter(self.console)
        self.command_handler = CommandHandler(introspector, self.config, self.console)

        # Create prompt session
        history_file = self.config.ensure_history_file()
        self.session: PromptSession = PromptSession(
            lexer=PygmentsLexer(PythonLexer),
            completer=ThreadedCompleter(self.completer),
            auto_suggest=AutoSuggestFromHistory(),
            history=FileHistory(str(history_file)),
            multiline=False,
            enable_open_in_editor=False,
        )

    def show_welcome(self) -> None:
        """Display welcome message."""
        welcome = f"""
[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]
[bold cyan]  Clientele Interactive API Explorer v{settings.VERSION}[/bold cyan]
[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]

Type [cyan]/help[/cyan] or [cyan]?[/cyan] for commands, [cyan]/exit[/cyan] or Ctrl+D to quit
Type [cyan]/list[/cyan] to see available operations

Press [bold]TAB[/bold] for autocomplete
"""
        self.console.print(welcome)

    def run(self) -> None:
        """Run the main REPL loop."""
        self.show_welcome()

        while True:
            try:
                # Get input
                text = self.session.prompt(">>> ")

                # Skip empty input
                if not text.strip():
                    continue

                # Handle special commands
                if text.strip().startswith("/"):
                    should_exit = self.command_handler.handle_command(text.strip())
                    if should_exit:
                        self.console.print("\n[cyan]Goodbye! 👋[/cyan]")
                        break
                elif text.strip() == "?":
                    self.command_handler.handle_command("/help")
                else:
                    # Execute operation
                    self._execute_operation(text.strip())

            except KeyboardInterrupt:
                # Ctrl+C - cancel current input
                continue
            except EOFError:
                # Ctrl+D - exit
                self.console.print("\n[cyan]Goodbye! 👋[/cyan]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")

    def _execute_operation(self, text: str) -> None:
        """Execute an API operation.

        Args:
            text: Operation call text (e.g., "get_users(limit=10)")
        """
        # Check if user is trying to inspect a schema (no parentheses and valid identifier)
        if "(" not in text and text.isidentifier():
            # Check if this matches a schema name
            schemas = self.introspector.get_all_schemas()
            if text in schemas:
                # Display schema information
                self.command_handler._show_schema_detail(text)
                return

        try:
            # Parse the operation call
            operation_name, args = self._parse_operation(text)

            # Execute the operation
            result = self.executor.execute(operation_name, args)

            # Format and display the result
            self.formatter.format(result)

        except SyntaxError as e:
            self.console.print(f"[red]Syntax error: {e}[/red]")
            self.console.print("[yellow]Expected format: operation_name(param=value, ...)[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

    def _parse_operation(self, text: str) -> tuple[str, dict[str, typing.Any]]:
        """Parse an operation call into name and arguments.

        Args:
            text: Operation call text (e.g., "get_users(limit=10)")

        Returns:
            Tuple of (operation_name, arguments_dict)

        Raises:
            SyntaxError: If parsing fails
        """
        # Use Python's AST parser to safely parse the call
        try:
            # Add a dummy assignment to make it a valid statement
            tree = ast.parse(f"_result = {text}")

            # Extract the call node
            if not isinstance(tree.body[0], ast.Assign):
                raise SyntaxError("Invalid operation call")

            call_node = tree.body[0].value

            if not isinstance(call_node, ast.Call):
                raise SyntaxError("Expected a function call")

            # Get operation name
            if isinstance(call_node.func, ast.Name):
                operation_name = call_node.func.id
            else:
                raise SyntaxError("Invalid operation name")

            # Parse arguments
            args: dict[str, typing.Any] = {}

            # Handle keyword arguments
            for keyword in call_node.keywords:
                if keyword.arg is None:
                    raise SyntaxError("**kwargs not supported")
                args[keyword.arg] = ast.literal_eval(keyword.value)

            # Handle positional arguments (not recommended, but support it)
            if call_node.args:
                raise SyntaxError("Positional arguments not supported. Use keyword arguments: param=value")

            return operation_name, args

        except ValueError as e:
            raise SyntaxError(f"Invalid argument value: {e}") from e
