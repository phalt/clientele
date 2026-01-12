"""Additional tests to achieve 100% coverage for ClienteleREPL."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from clientele.explore.introspector import ClientIntrospector
from clientele.explore.repl import ClienteleREPL
from clientele.explore.session import SessionConfig


@pytest.fixture
def test_client_path():
    """Path to the test client."""
    return Path(__file__).parent.parent / "old_clients" / "test_client"


@pytest.fixture
def introspector(test_client_path):
    """Create a ClientIntrospector with loaded test client."""
    intro = ClientIntrospector(test_client_path)
    intro.load_client()
    intro.discover_operations()
    return intro


@pytest.fixture
def repl(introspector):
    """Create a ClienteleREPL instance."""
    config = SessionConfig()
    return ClienteleREPL(introspector, config)


def test_run_loop_with_exit_command(introspector):
    """Test run() method exits when /exit command is issued."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to return /exit
    with patch.object(repl.session, "prompt", return_value="/exit"):
        with patch.object(repl.command_handler, "handle_command", return_value=True) as mock_handler:
            with patch.object(repl, "show_welcome"):
                repl.run()
                mock_handler.assert_called_once_with("/exit")


def test_run_loop_with_empty_input(introspector):
    """Test run() method skips empty input."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to return empty string then /exit
    with patch.object(repl.session, "prompt", side_effect=["", "  ", "/exit"]):
        with patch.object(repl.command_handler, "handle_command", return_value=True):
            with patch.object(repl, "show_welcome"):
                repl.run()


def test_run_loop_with_help_shortcut(introspector):
    """Test run() method handles '?' as help command."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to return ? then /exit
    with patch.object(repl.session, "prompt", side_effect=["?", "/exit"]):
        with patch.object(repl.command_handler, "handle_command", return_value=False) as mock_handler:
            # First call returns False (don't exit), second returns True (exit)
            mock_handler.side_effect = [False, True]
            with patch.object(repl, "show_welcome"):
                repl.run()
                # Should have been called twice: once for /help, once for /exit
                assert mock_handler.call_count == 2
                # First call should be /help
                assert mock_handler.call_args_list[0][0][0] == "/help"


def test_run_loop_with_operation_call(introspector):
    """Test run() method executes operation calls."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to return an operation call then /exit
    with patch.object(repl.session, "prompt", side_effect=["test_op()", "/exit"]):
        with patch.object(repl, "_execute_operation") as mock_execute:
            with patch.object(repl.command_handler, "handle_command", return_value=True):
                with patch.object(repl, "show_welcome"):
                    repl.run()
                    mock_execute.assert_called_once_with("test_op()")


def test_run_loop_with_keyboard_interrupt(introspector):
    """Test run() method continues on KeyboardInterrupt (Ctrl+C)."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to raise KeyboardInterrupt then return /exit
    with patch.object(repl.session, "prompt", side_effect=[KeyboardInterrupt(), "/exit"]):
        with patch.object(repl.command_handler, "handle_command", return_value=True):
            with patch.object(repl, "show_welcome"):
                repl.run()


def test_run_loop_with_eof_error(introspector):
    """Test run() method exits on EOFError (Ctrl+D)."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to raise EOFError
    with patch.object(repl.session, "prompt", side_effect=EOFError()):
        with patch.object(repl, "show_welcome"):
            repl.run()


def test_run_loop_with_unexpected_exception(introspector):
    """Test run() method handles unexpected exceptions."""
    repl = ClienteleREPL(introspector)

    # Mock the prompt to raise an unexpected exception then /exit
    with patch.object(repl.session, "prompt", side_effect=[RuntimeError("Unexpected!"), "/exit"]):
        with patch.object(repl.command_handler, "handle_command", return_value=True):
            with patch.object(repl, "show_welcome"):
                repl.run()


def test_execute_operation_inspects_operation_by_name(repl):
    """Test _execute_operation shows operation details when given an operation name without parentheses."""
    # Add an operation to the introspector
    repl.introspector.operations["test_operation"] = Mock()

    with patch.object(repl.command_handler, "_show_operation_detail") as mock_show_operation:
        repl._execute_operation("test_operation")
        mock_show_operation.assert_called_once_with("test_operation")


def test_parse_operation_with_invalid_operation_name_type(repl):
    """Test _parse_operation raises SyntaxError for non-Name operation (e.g., attribute access)."""
    with pytest.raises(SyntaxError, match="Invalid operation name"):
        # This creates a Call node with an Attribute instead of Name
        repl._parse_operation("module.operation()")


def test_parse_operation_with_complex_expression(repl):
    """Test _parse_operation raises SyntaxError for complex expressions."""
    with pytest.raises(SyntaxError, match="Expected a function call"):
        # This is not a function call
        repl._parse_operation("1 + 1")


def test_parse_operation_with_non_call_expression(repl):
    """Test _parse_operation raises SyntaxError when expression is not a call."""
    with pytest.raises(SyntaxError, match="Expected a function call"):
        # This will parse but the value won't be a Call node
        repl._parse_operation("just_a_variable")


def test_execute_operation_prints_syntax_error_message(repl):
    """Test _execute_operation prints syntax error messages."""
    with patch.object(repl.console, "print") as mock_print:
        repl._execute_operation("invalid syntax (")

        # Should print two messages: the error and the expected format
        assert mock_print.call_count == 2
        assert "Syntax error" in str(mock_print.call_args_list[0])
        assert "Expected format" in str(mock_print.call_args_list[1])


def test_execute_operation_prints_general_error_message(repl):
    """Test _execute_operation prints general error messages."""
    with patch.object(repl.executor, "execute", side_effect=RuntimeError("Test error")):
        with patch.object(repl.console, "print") as mock_print:
            repl._execute_operation("test_op()")

            # Should print error message
            assert mock_print.call_count == 1
            assert "Error" in str(mock_print.call_args_list[0])
            assert "Test error" in str(mock_print.call_args_list[0])


def test_run_full_workflow_with_commands_and_operations(introspector):
    """Test complete run() workflow with various inputs."""
    repl = ClienteleREPL(introspector)

    # Simulate a realistic session
    inputs = [
        "",  # Empty line (skip)
        "  ",  # Whitespace only (skip)
        "?",  # Help shortcut
        "/list",  # List command
        "some_op(param=1)",  # Operation call
        "/exit",  # Exit
    ]

    with patch.object(repl.session, "prompt", side_effect=inputs):
        with patch.object(repl.command_handler, "handle_command") as mock_handler:
            # Set up return values: False for ?, /list, True for /exit
            mock_handler.side_effect = [False, False, True]
            with patch.object(repl, "_execute_operation") as mock_execute:
                with patch.object(repl, "show_welcome"):
                    repl.run()

                    # Verify command handler was called 3 times (?, /list, /exit)
                    assert mock_handler.call_count == 3
                    # Verify execute was called once
                    assert mock_execute.call_count == 1


def test_execute_operation_with_schema_inspection_fallback(repl):
    """Test that operation name inspection works even if it's not in operations dict."""
    # Clear operations to test the fallback path
    repl.introspector.operations.clear()

    # Try to inspect a non-existent operation (should not crash)
    with patch.object(repl.command_handler, "_show_operation_detail") as mock_show_operation:
        repl._execute_operation("NonExistent")
        # Should not be called since it's not in operations
        mock_show_operation.assert_not_called()


def test_run_loop_with_slash_command_that_does_not_exit(introspector):
    """Test run() continues when command handler returns False."""
    repl = ClienteleREPL(introspector)

    # Mock commands that don't exit, then one that does
    with patch.object(repl.session, "prompt", side_effect=["/list", "/help", "/exit"]):
        with patch.object(repl.command_handler, "handle_command") as mock_handler:
            # First two return False (continue), last returns True (exit)
            mock_handler.side_effect = [False, False, True]
            with patch.object(repl, "show_welcome"):
                repl.run()
                assert mock_handler.call_count == 3


def test_parse_operation_with_non_assignment_statement(repl):
    """Test _parse_operation raises SyntaxError when AST doesn't create an assignment."""
    import ast

    mock_tree = ast.parse("pass")  # This creates an Expr node, not Assign

    with patch("ast.parse", return_value=mock_tree):
        with pytest.raises(SyntaxError, match="Invalid operation call"):
            repl._parse_operation("anything()")
