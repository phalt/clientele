"""Basic tests for explore module to ensure it can be imported and initialized."""

from pathlib import Path

from clientele.explore.session import SessionConfig


def test_session_config_initialization():
    """Test SessionConfig initializes with default values."""
    config = SessionConfig()

    assert config.output_format == "json"
    assert config.debug_mode is False
    assert config.config_overrides == {}
    assert isinstance(config.history_file, Path)


def test_session_config_toggle_debug():
    """Test toggling debug mode."""
    config = SessionConfig()

    assert config.debug_mode is False
    config.debug_mode = True
    assert config.debug_mode is True
    config.debug_mode = False
    assert config.debug_mode is False


def test_session_config_set_overrides():
    """Test setting configuration overrides."""
    config = SessionConfig()

    config.config_overrides["base_url"] = "https://api.example.com"
    config.config_overrides["bearer_token"] = "test-token"

    assert config.config_overrides["base_url"] == "https://api.example.com"
    assert config.config_overrides["bearer_token"] == "test-token"


def test_session_config_ensure_history_file():
    """Test history file creation."""
    config = SessionConfig()

    # Just verify the method returns the correct path
    result = config.ensure_history_file()
    assert result == config.history_file
    # File operations happen but we can't easily mock Path methods
