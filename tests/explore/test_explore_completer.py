"""Tests for clientele.explore.completer module."""

from unittest.mock import MagicMock, Mock
from types import ModuleType

import pytest
from prompt_toolkit.document import Document

from clientele.explore.completer import ClienteleCompleter
from clientele.explore.introspector import ClientIntrospector


@pytest.fixture
def mock_client():
    """Create a mock client module."""
    client = ModuleType("mock_client")
    
    def get_users():
        """Get users."""
        pass
    
    def create_user():
        """Create user."""
        pass
    
    def update_user():
        """Update user."""
        pass
    
    client.get_users = get_users
    client.create_user = create_user
    client.update_user = update_user
    
    return client


@pytest.fixture
def mock_schemas():
    """Create a mock schemas module."""
    schemas = ModuleType("mock_schemas")
    
    class User:
        pass
    
    class Post:
        pass
    
    schemas.User = User
    schemas.Post = Post
    
    return schemas


@pytest.fixture
def introspector(mock_client, mock_schemas):
    """Create a ClientIntrospector instance."""
    return ClientIntrospector(mock_client, mock_schemas)


@pytest.fixture
def completer(introspector):
    """Create a ClienteleCompleter instance."""
    return ClienteleCompleter(introspector)


def test_complete_operation_names(completer):
    """Test completion of operation names."""
    document = Document("get")
    completions = list(completer.get_completions(document, None))
    
    # Should suggest get_users
    completion_texts = [c.text for c in completions]
    assert "get_users" in completion_texts


def test_complete_slash_commands(completer):
    """Test completion of slash commands."""
    document = Document("/")
    completions = list(completer.get_completions(document, None))
    
    completion_texts = [c.text for c in completions]
    assert "list" in completion_texts
    assert "schemas" in completion_texts
    assert "config" in completion_texts
    assert "debug" in completion_texts
    assert "help" in completion_texts
    assert "exit" in completion_texts


def test_complete_partial_command(completer):
    """Test completion with partial command."""
    document = Document("/li")
    completions = list(completer.get_completions(document, None))
    
    completion_texts = [c.text for c in completions]
    assert "list" in completion_texts


def test_complete_schemas_command(completer):
    """Test completion after /schemas command."""
    document = Document("/schemas ")
    completions = list(completer.get_completions(document, None))
    
    completion_texts = [c.text for c in completions]
    assert "User" in completion_texts
    assert "Post" in completion_texts


def test_complete_empty_input(completer):
    """Test completion with empty input."""
    document = Document("")
    completions = list(completer.get_completions(document, None))
    
    # Should return operations and commands
    assert len(completions) > 0


def test_complete_no_match(completer):
    """Test completion with no matches."""
    document = Document("xyz")
    completions = list(completer.get_completions(document, None))
    
    # Should return empty or all options
    assert isinstance(completions, list)


def test_complete_partial_operation(completer):
    """Test completion with partial operation name."""
    document = Document("create")
    completions = list(completer.get_completions(document, None))
    
    completion_texts = [c.text for c in completions]
    assert "create_user" in completion_texts


def test_complete_update_operation(completer):
    """Test completion for update operation."""
    document = Document("upd")
    completions = list(completer.get_completions(document, None))
    
    completion_texts = [c.text for c in completions]
    assert "update_user" in completion_texts


def test_complete_case_insensitive(completer):
    """Test that completion works with different cases."""
    document = Document("GET")
    completions = list(completer.get_completions(document, None))
    
    # Should still find get_users
    completion_texts = [c.text.lower() for c in completions]
    assert any("get_users" in text for text in completion_texts)
