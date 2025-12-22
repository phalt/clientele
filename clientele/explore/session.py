"""Session management for the REPL."""

from __future__ import annotations

from pathlib import Path


class SessionConfig:
    """Configuration for a REPL session.

    Attributes:
        output_format: Output format (json, table, or raw)
        history_file: Path to command history file
        debug_mode: Enable HTTP request/response logging
        config_overrides: Runtime configuration overrides
    """

    def __init__(self):
        """Initialize session configuration."""
        self.output_format = "json"  # json, table, or raw
        self.history_file = Path.home() / ".clientele_history"
        self.debug_mode = False  # Enable HTTP request/response logging
        self.config_overrides: dict[str, str] = {}  # Runtime config overrides

    def ensure_history_file(self) -> Path:
        """Ensure history file exists and return its path.

        Returns:
            Path to history file
        """
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.touch(exist_ok=True)
        return self.history_file
