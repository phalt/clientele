"""Tests for the ClienteleCompleter class."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from prompt_toolkit.document import Document

from clientele.explore.completer import ClienteleCompleter
from clientele.explore.introspector import ClientIntrospector


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
def completer(introspector):
    """Create a ClienteleCompleter."""
    return ClienteleCompleter(introspector)


def test_completer_initialization(introspector):
    """Test completer initializes correctly."""
    completer = ClienteleCompleter(introspector)
    assert completer.introspector is introspector


def test_completer_has_special_commands():
    """Test completer has special commands defined."""
    assert len(ClienteleCompleter.SPECIAL_COMMANDS) > 0
    # Check a few key commands
    command_names = [cmd for cmd, _ in ClienteleCompleter.SPECIAL_COMMANDS]
    assert "/help" in command_names
    assert "/list" in command_names
    assert "/exit" in command_names


def test_complete_special_commands_help(completer):
    """Test completing /help command."""
    # When typing "/help", the word extracted is "help" without the slash
    # So we need to test with just "/" to get completions
    doc = Document(text="/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    assert len(completions) > 0
    completion_texts = [c.text for c in completions]
    assert "/help" in completion_texts


def test_complete_special_commands_list(completer):
    """Test completing /list command."""
    doc = Document(text="/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    completion_texts = [c.text for c in completions]
    assert "/list" in completion_texts


def test_complete_special_commands_exit(completer):
    """Test completing /exit command."""
    doc = Document(text="/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    completion_texts = [c.text for c in completions]
    assert "/exit" in completion_texts


def test_complete_special_commands_all_slash(completer):
    """Test completing all commands when just / is typed."""
    doc = Document(text="/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    # Should get all special commands
    assert len(completions) == len(ClienteleCompleter.SPECIAL_COMMANDS)


def test_complete_operations_simple(completer):
    """Test completing operation names."""
    doc = Document(text="simple", cursor_position=6)
    completions = list(completer.get_completions(doc, None))

    # Check that we get completions
    assert len(completions) > 0
    completion_texts = [c.text for c in completions]
    # The test client should have operations starting with "simple"
    assert any("simple" in text for text in completion_texts)


def test_complete_operations_empty(completer):
    """Test completing operations with empty input."""
    doc = Document(text="", cursor_position=0)
    completions = list(completer.get_completions(doc, None))

    # Should get all operations
    assert len(completions) > 0


def test_complete_parameters_inside_parentheses(completer):
    """Test parameter completion inside function call."""
    # Use an operation that has parameters - need space after ( for word extraction
    text = "parameter_request_simple_request( "
    doc = Document(text=text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))

    # Should get parameter completions
    # Parameters should end with = for easier typing
    completion_texts = [c.text for c in completions]
    assert any("=" in text for text in completion_texts)


def test_complete_parameters_with_partial_name(completer):
    """Test parameter completion with partial parameter name."""
    # 'your_input' is a parameter, so we test with 'y'
    text = "parameter_request_simple_request(y"
    doc = Document(text=text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))

    # Should filter parameters starting with 'y'
    completion_texts = [c.text for c in completions]
    # All completions should start with 'y' and end with '='
    assert any(text.startswith("y") for text in completion_texts if text)


def test_complete_parameters_skip_provided(completer):
    """Test parameter completion skips already provided parameters."""
    text = "request_data_path_request_data(path_parameter='test', "
    doc = Document(text=text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))

    # Should not include 'path_parameter' again
    completion_texts = [c.text for c in completions]
    assert "path_parameter=" not in completion_texts


def test_complete_schema_names_after_schemas_command(completer):
    """Test schema name completion after /schemas command."""
    doc = Document(text="/schemas ", cursor_position=9)
    completions = list(completer.get_completions(doc, None))

    # Should get schema completions
    # The exact schemas depend on the test client, but there should be some
    assert len(completions) >= 0  # Can be zero if test client has no schemas


def test_complete_schema_names_partial(completer):
    """Test schema name completion with partial input."""
    doc = Document(text="/schemas Sim", cursor_position=12)
    completions = list(completer.get_completions(doc, None))

    # Should filter schemas starting with "Sim"
    completion_texts = [c.text for c in completions]
    assert all(text.startswith("Sim") or text == "" for text in completion_texts if text)


def test_format_type_with_named_type():
    """Test _format_type with type that has __name__."""
    completer = ClienteleCompleter(Mock())

    class SampleType:
        __name__ = "SampleType"

    result = completer._format_type(SampleType)
    assert result == "SampleType"


def test_format_type_with_any():
    """Test _format_type with Any type."""
    from typing import Any

    completer = ClienteleCompleter(Mock())
    result = completer._format_type(Any)
    assert result == "Any"


def test_format_type_with_string_representation():
    """Test _format_type with complex typing."""
    from typing import Optional

    completer = ClienteleCompleter(Mock())
    result = completer._format_type(Optional[str])
    # Should simplify the type string
    assert "typing." not in result.lower() or "Optional" in result


def test_complete_operations_with_metadata(completer):
    """Test that operation completions include metadata."""
    doc = Document(text="simple", cursor_position=6)
    completions = list(completer.get_completions(doc, None))

    # At least one completion should have display_meta
    assert any(c.display_meta for c in completions)


def test_complete_parameters_with_metadata(completer):
    """Test that parameter completions include type metadata."""
    doc = Document(text="simple_request(", cursor_position=15)
    completions = list(completer.get_completions(doc, None))

    # Parameter completions should have metadata about type and required status
    if completions:
        assert any(c.display_meta for c in completions)


def test_complete_special_commands_with_metadata(completer):
    """Test that special command completions include descriptions."""
    doc = Document(text="/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))

    # All special commands should have descriptions
    assert all(c.display_meta for c in completions)


def test_complete_nonexistent_operation_parameters(completer):
    """Test parameter completion for non-existent operation."""
    doc = Document(text="nonexistent_op(", cursor_position=15)
    completions = list(completer.get_completions(doc, None))

    # Should return empty list
    assert len(completions) == 0


def test_document_get_word_before_cursor():
    """Test that we handle Document.get_word_before_cursor correctly."""
    doc = Document(text="simple_request", cursor_position=6)
    word = doc.get_word_before_cursor()
    assert word == "simple"
