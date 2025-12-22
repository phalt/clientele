"""Context-aware autocomplete for the REPL."""

from __future__ import annotations

import typing

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

if typing.TYPE_CHECKING:
    from clientele.explore.introspector import ClientIntrospector


class ClienteleCompleter(Completer):
    """Autocomplete for operations, parameters, and special commands."""

    # Special commands available in the REPL
    SPECIAL_COMMANDS = [
        ("/list", "List all available operations"),
        ("/operations", "List all available operations (alias for /list)"),
        ("/schemas", "List all available schemas or show schema details"),
        ("/config", "Show or set configuration"),
        ("/debug", "Enable/disable debug mode"),
        ("/help", "Show help message"),
        ("/exit", "Exit the REPL"),
        ("/quit", "Exit the REPL (alias for /exit)"),
    ]

    def __init__(self, introspector: ClientIntrospector):
        """Initialize the completer.

        Args:
            introspector: Client introspector for operation discovery
        """
        self.introspector = introspector

    def get_completions(self, document: Document, complete_event):
        """Generate completions based on current context.

        Args:
            document: Current document state
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor
        word = document.get_word_before_cursor()

        # Special commands (starting with /)
        if text.startswith("/"):
            # Check if we're completing after "/schemas "
            if text.startswith("/schemas "):
                schema_arg = text[9:]  # Everything after "/schemas "
                yield from self._complete_schema_names(schema_arg)
            else:
                yield from self._complete_special_commands(word)

        # Inside function call - suggest parameters
        elif "(" in text and ")" not in text:
            yield from self._complete_parameters(text, word)

        # Top-level - suggest operations
        else:
            yield from self._complete_operations(word)

    def _complete_special_commands(self, word: str):
        """Complete special commands.

        Args:
            word: Current word being typed

        Yields:
            Completion objects for matching special commands
        """
        for cmd, description in self.SPECIAL_COMMANDS:
            if cmd.startswith(word):
                yield Completion(
                    text=cmd,
                    start_position=-len(word),
                    display_meta=description,
                )

    def _complete_schema_names(self, word: str):
        """Complete schema names after /schemas command.

        Args:
            word: Current word being typed

        Yields:
            Completion objects for matching schema names
        """
        schemas = self.introspector.get_all_schemas()
        for schema_name in schemas.keys():
            if schema_name.startswith(word):
                yield Completion(
                    text=schema_name,
                    start_position=-len(word),
                    display_meta="Pydantic schema",
                )

    def _complete_operations(self, word: str):
        """Complete operation names.

        Args:
            word: Current word being typed

        Yields:
            Completion objects for matching operations
        """
        for op_name, op_info in self.introspector.operations.items():
            if op_name.startswith(word):
                # Create a brief description
                meta = f"{op_info.http_method}"
                if op_info.docstring:
                    # Use first line of docstring
                    first_line = op_info.docstring.split("\n")[0]
                    meta = f"{op_info.http_method} - {first_line[:50]}"

                yield Completion(
                    text=op_name,
                    start_position=-len(word),
                    display_meta=meta,
                )

    def _complete_parameters(self, text: str, word: str):
        """Complete parameter names when inside a function call.

        Args:
            text: Full text before cursor
            word: Current word being typed

        Yields:
            Completion objects for matching parameters
        """
        # Extract the function name (everything before '(')
        func_name = text.split("(")[0].strip()

        # Get operation info
        op_info = self.introspector.operations.get(func_name)
        if not op_info:
            return

        # Parse already-provided parameters
        in_parens = text.split("(", 1)[1] if "(" in text else ""
        provided_params = set()
        for part in in_parens.split(","):
            if "=" in part:
                param_name = part.split("=")[0].strip()
                provided_params.add(param_name)

        # Suggest remaining parameters
        for param_name, param_info in op_info.parameters.items():
            if param_name in provided_params:
                continue

            if param_name.startswith(word):
                # Format type info
                param_type = param_info["type"]
                type_str = self._format_type(param_type)

                required_str = "required" if param_info["required"] else "optional"

                meta = f"{type_str} ({required_str})"

                yield Completion(
                    text=f"{param_name}=",
                    start_position=-len(word),
                    display_meta=meta,
                )

    def _format_type(self, type_hint: typing.Any) -> str:
        """Format a type hint for display.

        Args:
            type_hint: Type hint to format

        Returns:
            Formatted type string
        """
        if type_hint is typing.Any:
            return "Any"

        # Handle typing module types
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__

        # Handle string representations
        type_str = str(type_hint)

        # Simplify common patterns
        type_str = type_str.replace("typing.", "")
        type_str = type_str.replace("<class '", "").replace("'>", "")

        return type_str
