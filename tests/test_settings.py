"""Tests for settings module."""

from clientele import settings


def test_version_is_string():
    """Test that VERSION is defined as a string."""
    assert isinstance(settings.VERSION, str)
    assert len(settings.VERSION) > 0


def test_version_format():
    """Test that VERSION follows semantic versioning."""
    parts = settings.VERSION.split(".")
    assert len(parts) >= 2  # At least major.minor
    assert parts[0].isdigit()
    assert parts[1].isdigit()


def test_py_version_exposes_major_and_minor():
    """Test that PY_VERSION provides integer major/minor components."""
    assert isinstance(settings.PY_VERSION[0], int)
    assert isinstance(settings.PY_VERSION[1], int)
    assert settings.PY_VERSION.major >= 3
