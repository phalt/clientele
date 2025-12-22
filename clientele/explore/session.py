"""Session management for the REPL."""

from __future__ import annotations

from pathlib import Path


class SessionConfig:
    """Configuration for a REPL session."""

    def __init__(self):
        """Initialize session configuration."""
        self.output_format = "json"  # json, table, or raw
        self.history_file = Path.home() / ".clientele_history"

    def ensure_history_file(self) -> Path:
        """Ensure history file exists and return its path.

        Returns:
            Path to history file
        """
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.touch(exist_ok=True)
        return self.history_file
