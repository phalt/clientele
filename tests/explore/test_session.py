"""Tests for clientele.explore.session module."""

from clientele.explore.session import SessionConfig


def test_session_config_initialization():
    """Test SessionConfig initializes with correct defaults."""
    config = SessionConfig()
    
    assert config.debug_mode is False
    assert config.config_overrides == {}


def test_session_config_with_debug_mode():
    """Test SessionConfig with debug mode enabled."""
    config = SessionConfig(debug_mode=True)
    
    assert config.debug_mode is True
    assert config.config_overrides == {}


def test_session_config_with_overrides():
    """Test SessionConfig with configuration overrides."""
    overrides = {"base_url": "https://api.example.com", "bearer_token": "test_token"}
    config = SessionConfig(config_overrides=overrides)
    
    assert config.debug_mode is False
    assert config.config_overrides == overrides
    assert config.config_overrides["base_url"] == "https://api.example.com"
    assert config.config_overrides["bearer_token"] == "test_token"


def test_session_config_all_parameters():
    """Test SessionConfig with all parameters set."""
    overrides = {"base_url": "https://test.com"}
    config = SessionConfig(debug_mode=True, config_overrides=overrides)
    
    assert config.debug_mode is True
    assert config.config_overrides == overrides
