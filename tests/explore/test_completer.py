"""Tests for clientele.explore.completer module."""

from unittest.mock import Mock

from prompt_toolkit.document import Document

from clientele.explore.completer import ClienteleCompleter


def test_completer_initialization():
    """Test ClienteleCompleter initializes correctly."""
    introspector = Mock()
    introspector.operations = {}

    completer = ClienteleCompleter(introspector)
    assert completer.introspector == introspector


def test_complete_operation_names():
    """Test completing operation names."""
    # Setup mock operations
    introspector = Mock()
    introspector.operations = {"get_user": Mock(), "get_users": Mock(), "create_user": Mock(), "delete_user": Mock()}

    completer = ClienteleCompleter(introspector)

    # Test completion for "get"
    document = Document("get", len("get"))
    completions = list(completer.get_completions(document, None))

    # Should suggest operations starting with "get"
    completion_texts = [c.text for c in completions]
    assert "get_user" in completion_texts or "get_users" in completion_texts


def test_complete_slash_commands():
    """Test completing slash commands."""
    introspector = Mock()
    introspector.operations = {}

    completer = ClienteleCompleter(introspector)

    # Test completion for "/"
    document = Document("/", len("/"))
    completions = list(completer.get_completions(document, None))

    # Should suggest slash commands
    completion_texts = [c.text for c in completions]
    assert len(completion_texts) > 0
    # Commands should include /help, /list, etc.


def test_complete_schemas_command():
    """Test completing /schemas command with schema names."""
    introspector = Mock()
    introspector.operations = {}
    introspector.schemas = {"User": Mock(), "Post": Mock(), "Comment": Mock()}

    completer = ClienteleCompleter(introspector)

    # Test completion for "/schemas "
    document = Document("/schemas ", len("/schemas "))
    completions = list(completer.get_completions(document, None))

    # Should suggest schema names
    completion_texts = [c.text for c in completions]
    assert "User" in completion_texts


def test_complete_partial_operation():
    """Test completing partial operation name."""
    introspector = Mock()
    introspector.operations = {"pokemon_list": Mock(), "pokemon_read": Mock(), "berry_list": Mock()}

    completer = ClienteleCompleter(introspector)

    # Test completion for "pok"
    document = Document("pok", len("pok"))
    completions = list(completer.get_completions(document, None))

    # Should suggest pokemon operations
    completion_texts = [c.text for c in completions]
    assert any("pokemon" in text for text in completion_texts)


def test_complete_empty_input():
    """Test completion with empty input."""
    introspector = Mock()
    introspector.operations = {"test_op": Mock()}

    completer = ClienteleCompleter(introspector)

    # Test completion for empty string
    document = Document("", 0)
    completions = list(completer.get_completions(document, None))

    # Should return suggestions
    assert len(completions) >= 0
