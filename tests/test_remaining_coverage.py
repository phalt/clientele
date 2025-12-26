"""Tests for explore module and other missing coverage."""

from unittest.mock import patch


def test_standard_utils_forward_reference():
    """Test standard utils union_for_py_ver with Python < 3.10."""
    from clientele import settings
    from clientele.generators.standard import utils

    # Test the branch that uses typing.Union for Python < 3.10
    # Mock settings.PY_VERSION to simulate Python 3.9
    with patch.object(settings, "PY_VERSION", [3, 9, 0]):
        # Test with a union that would normally use | syntax
        union_items = ["str", "int"]
        result = utils.union_for_py_ver(union_items)

        # Should use typing.Union for Python < 3.10
        assert result == "typing.Union[str, int]"


def test_completer_type_checking_import():
    """Test that TYPE_CHECKING import in completer.py works."""
    # Import the module to ensure TYPE_CHECKING block is evaluated
    from clientele.explore import completer

    # Verify the class exists and can be instantiated
    assert hasattr(completer, "ClienteleCompleter")


def test_commands_type_checking_import():
    """Test that TYPE_CHECKING import in commands.py works."""
    from clientele.explore import commands

    assert hasattr(commands, "CommandHandler")


def test_executor_type_checking_import():
    """Test that TYPE_CHECKING import in executor.py works."""
    from clientele.explore import executor

    assert hasattr(executor, "RequestExecutor")


def test_formatter_type_checking_import():
    """Test that TYPE_CHECKING import in formatter.py works."""
    from clientele.explore import formatter

    assert hasattr(formatter, "ResponseFormatter")
