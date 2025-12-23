"""Tests for the ClienteleREPL class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from clientele.explore.introspector import ClientIntrospector
from clientele.explore.repl import ClienteleREPL
from clientele.explore.session import SessionConfig


@pytest.fixture
def test_client_path():
    """Path to the test client."""
    return Path(__file__).parent.parent / "test_client"


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


def test_repl_initialization(introspector):
    """Test REPL initializes correctly."""
    repl = ClienteleREPL(introspector)
    assert repl.introspector is introspector
    assert repl.config is not None
    assert repl.console is not None
    assert repl.completer is not None
    assert repl.executor is not None
    assert repl.formatter is not None
    assert repl.command_handler is not None
    assert repl.session is not None


def test_repl_initialization_with_config(introspector):
    """Test REPL initializes with custom config."""
    config = SessionConfig()
    config.debug_mode = True
    repl = ClienteleREPL(introspector, config)
    assert repl.config is config
    assert repl.config.debug_mode is True


def test_show_welcome(repl):
    """Test welcome message display."""
    # Just ensure it doesn't raise an exception
    repl.show_welcome()


def test_parse_operation_simple(repl):
    """Test parsing simple operation call."""
    operation_name, args = repl._parse_operation("simple_request_simple_request_get()")
    assert operation_name == "simple_request_simple_request_get"
    assert args == {}


def test_parse_operation_with_single_arg(repl):
    """Test parsing operation with single argument."""
    operation_name, args = repl._parse_operation("parameter_request_simple_request(your_input='test')")
    assert operation_name == "parameter_request_simple_request"
    assert args == {"your_input": "test"}


def test_parse_operation_with_multiple_args(repl):
    """Test parsing operation with multiple arguments."""
    operation_name, args = repl._parse_operation(
        "request_data_path_request_data(path_parameter='test', data={'name': 'John'})"
    )
    assert operation_name == "request_data_path_request_data"
    assert args == {"path_parameter": "test", "data": {"name": "John"}}


def test_parse_operation_with_numeric_args(repl):
    """Test parsing operation with numeric arguments."""
    operation_name, args = repl._parse_operation("some_op(count=10, price=19.99)")
    assert operation_name == "some_op"
    assert args == {"count": 10, "price": 19.99}


def test_parse_operation_with_boolean_args(repl):
    """Test parsing operation with boolean arguments."""
    operation_name, args = repl._parse_operation("some_op(enabled=True, disabled=False)")
    assert operation_name == "some_op"
    assert args == {"enabled": True, "disabled": False}


def test_parse_operation_with_list_args(repl):
    """Test parsing operation with list arguments."""
    operation_name, args = repl._parse_operation("some_op(items=[1, 2, 3])")
    assert operation_name == "some_op"
    assert args == {"items": [1, 2, 3]}


def test_parse_operation_invalid_syntax(repl):
    """Test parsing invalid syntax raises SyntaxError."""
    with pytest.raises(SyntaxError):
        repl._parse_operation("not a valid call")


def test_parse_operation_positional_args_not_supported(repl):
    """Test that positional arguments are not supported."""
    with pytest.raises(SyntaxError, match="Positional arguments not supported"):
        repl._parse_operation("some_op('arg1', 'arg2')")


def test_parse_operation_kwargs_not_supported(repl):
    """Test that **kwargs is not supported."""
    with pytest.raises(SyntaxError, match="\\*\\*kwargs not supported"):
        # This creates an AST with **kwargs
        repl._parse_operation("some_op(**{'key': 'value'})")


def test_parse_operation_invalid_arg_value(repl):
    """Test parsing with invalid argument value."""
    with pytest.raises(SyntaxError, match="Invalid argument value"):
        # This should fail because undefined_var is not a literal
        repl._parse_operation("some_op(arg=undefined_var)")


def test_parse_operation_no_parentheses(repl):
    """Test parsing operation without parentheses."""
    with pytest.raises(SyntaxError):
        repl._parse_operation("operation_name")


def test_parse_operation_complex_dict(repl):
    """Test parsing operation with complex dictionary."""
    operation_name, args = repl._parse_operation("some_op(data={'nested': {'key': 'value'}, 'list': [1, 2]})")
    assert operation_name == "some_op"
    assert args == {"data": {"nested": {"key": "value"}, "list": [1, 2]}}


def test_parse_operation_empty_string(repl):
    """Test parsing operation with empty string argument."""
    operation_name, args = repl._parse_operation("some_op(text='')")
    assert operation_name == "some_op"
    assert args == {"text": ""}


def test_parse_operation_none_value(repl):
    """Test parsing operation with None value."""
    operation_name, args = repl._parse_operation("some_op(value=None)")
    assert operation_name == "some_op"
    assert args == {"value": None}


def test_execute_operation_calls_executor(repl):
    """Test that _execute_operation calls executor."""
    with patch.object(repl.executor, "execute") as mock_execute:
        from clientele.explore.executor import ExecutionResult

        mock_execute.return_value = ExecutionResult(
            success=True, response={"status": "ok"}, duration=0.1, operation="test_op"
        )

        repl._execute_operation("test_op()")

        assert mock_execute.called


def test_execute_operation_formats_result(repl):
    """Test that _execute_operation formats the result."""
    with patch.object(repl.executor, "execute") as mock_execute, patch.object(repl.formatter, "format") as mock_format:
        from clientele.explore.executor import ExecutionResult

        result = ExecutionResult(success=True, response={"status": "ok"}, duration=0.1, operation="test_op")
        mock_execute.return_value = result

        repl._execute_operation("test_op()")

        assert mock_format.called
        mock_format.assert_called_once_with(result)


def test_execute_operation_handles_syntax_error(repl):
    """Test that _execute_operation handles syntax errors."""
    # Just ensure it doesn't raise an exception
    repl._execute_operation("invalid syntax here")


def test_execute_operation_handles_general_error(repl):
    """Test that _execute_operation handles general errors."""
    with patch.object(repl, "_parse_operation", side_effect=Exception("Test error")):
        # Just ensure it doesn't raise an exception
        repl._execute_operation("test_op()")
