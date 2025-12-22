"""Tests for clientele.explore.repl module."""

from unittest.mock import Mock, patch, MagicMock
import pytest
from clientele.explore.repl import ExploreREPL


def test_repl_initialization():
    """Test ExploreREPL initializes correctly."""
    mock_client = Mock()
    mock_schemas = Mock()
    mock_config = Mock()
    
    with patch('clientele.explore.repl.ClientIntrospector'):
        with patch('clientele.explore.repl.RequestExecutor'):
            with patch('clientele.explore.repl.CommandHandler'):
                with patch('clientele.explore.repl.ResponseFormatter'):
                    with patch('clientele.explore.repl.ExploreCompleter'):
                        repl = ExploreREPL(mock_client, mock_schemas, mock_config)
                        
                        assert repl.client_module == mock_client
                        assert repl.schemas_module == mock_schemas
                        assert repl.config_module == mock_config


def test_is_command_detection():
    """Test detecting slash commands vs operations."""
    mock_client = Mock()
    mock_schemas = Mock()
    mock_config = Mock()
    
    with patch('clientele.explore.repl.ClientIntrospector'):
        with patch('clientele.explore.repl.RequestExecutor'):
            with patch('clientele.explore.repl.CommandHandler'):
                with patch('clientele.explore.repl.ResponseFormatter'):
                    with patch('clientele.explore.repl.ExploreCompleter'):
                        repl = ExploreREPL(mock_client, mock_schemas, mock_config)
                        
                        assert repl._is_command("/list") is True
                        assert repl._is_command("/help") is True
                        assert repl._is_command("?") is True
                        assert repl._is_command("get_user(id=1)") is False
                        assert repl._is_command("pokemon_list()") is False


def test_parse_operation_call():
    """Test parsing operation calls."""
    mock_client = Mock()
    mock_schemas = Mock()
    mock_config = Mock()
    
    with patch('clientele.explore.repl.ClientIntrospector'):
        with patch('clientele.explore.repl.RequestExecutor'):
            with patch('clientele.explore.repl.CommandHandler'):
                with patch('clientele.explore.repl.ResponseFormatter'):
                    with patch('clientele.explore.repl.ExploreCompleter'):
                        repl = ExploreREPL(mock_client, mock_schemas, mock_config)
                        
                        # Test with parameters
                        name, kwargs = repl._parse_operation_call('get_user(id=1, name="test")')
                        assert name == "get_user"
                        assert "id" in kwargs
                        assert kwargs["id"] == 1
                        
                        # Test without parameters
                        name, kwargs = repl._parse_operation_call('list_users()')
                        assert name == "list_users"
                        assert kwargs == {}


def test_welcome_message():
    """Test welcome message display."""
    mock_client = Mock()
    mock_schemas = Mock()
    mock_config = Mock()
    
    with patch('clientele.explore.repl.ClientIntrospector') as mock_intro:
        mock_intro.return_value.operations = {"test_op": Mock()}
        with patch('clientele.explore.repl.RequestExecutor'):
            with patch('clientele.explore.repl.CommandHandler'):
                with patch('clientele.explore.repl.ResponseFormatter'):
                    with patch('clientele.explore.repl.ExploreCompleter'):
                        with patch('clientele.explore.repl.Console') as mock_console:
                            repl = ExploreREPL(mock_client, mock_schemas, mock_config)
                            repl._show_welcome()
                            
                            # Console print should be called
                            assert mock_console.return_value.print.called


def test_execute_operation_call():
    """Test executing an operation call."""
    mock_client = Mock()
    mock_schemas = Mock()
    mock_config = Mock()
    
    with patch('clientele.explore.repl.ClientIntrospector'):
        with patch('clientele.explore.repl.RequestExecutor') as mock_executor:
            with patch('clientele.explore.repl.CommandHandler'):
                with patch('clientele.explore.repl.ResponseFormatter') as mock_formatter:
                    with patch('clientele.explore.repl.ExploreCompleter'):
                        # Setup mock result
                        mock_result = Mock(success=True, response={"test": "data"})
                        mock_executor.return_value.execute.return_value = mock_result
                        
                        repl = ExploreREPL(mock_client, mock_schemas, mock_config)
                        repl._execute_operation("test_op", {"id": 1})
                        
                        # Executor should be called
                        mock_executor.return_value.execute.assert_called_once()
                        # Formatter should be called
                        mock_formatter.return_value.format.assert_called_once()
