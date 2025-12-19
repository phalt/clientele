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


def test_split_ver_returns_list_of_ints():
    """Test that split_ver returns a list of integers."""
    result = settings.split_ver()
    assert isinstance(result, list)
    assert len(result) >= 2
    assert all(isinstance(v, int) for v in result)


def test_py_version_is_list():
    """Test that PY_VERSION is defined and is a list."""
    assert isinstance(settings.PY_VERSION, list)
    assert len(settings.PY_VERSION) >= 2
    assert all(isinstance(v, int) for v in settings.PY_VERSION)
