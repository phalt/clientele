"""Tests for utility functions."""

from clientele.utils import get_client_project_directory_path


def test_get_client_project_directory_path():
    """Test converting output directory to dot-notation path."""
    # Test basic conversion
    result = get_client_project_directory_path("path/to/client")
    assert result == "path.to"

    # Test single level
    result = get_client_project_directory_path("client")
    assert result == ""

    # Test with multiple levels
    result = get_client_project_directory_path("a/b/c/d")
    assert result == "a.b.c"


def test_get_client_project_directory_path_edge_cases():
    """Test edge cases for path conversion."""
    # Empty string
    result = get_client_project_directory_path("")
    assert result == ""

    # Path with trailing slash
    result = get_client_project_directory_path("path/to/client/")
    assert result == "path.to.client"
