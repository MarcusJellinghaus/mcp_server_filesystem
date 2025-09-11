"""Tests for reference project CLI parsing and validation."""

import argparse
from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_filesystem.main import parse_args, validate_reference_projects


class TestReferenceProjectCLI:
    """Test CLI argument parsing and validation."""

    def test_parse_single_reference_project(self) -> None:
        """Test parsing single reference project argument."""
        with patch('sys.argv', ['script.py', '--project-dir', '/tmp', 
                                '--reference-project', 'proj1=/path/to/proj1']):
            args = parse_args()
            assert args.reference_project == ['proj1=/path/to/proj1']

    def test_parse_multiple_reference_projects(self) -> None:
        """Test parsing multiple reference project arguments."""
        with patch('sys.argv', ['script.py', '--project-dir', '/tmp',
                                '--reference-project', 'proj1=/path/to/proj1',
                                '--reference-project', 'proj2=/path/to/proj2']):
            args = parse_args()
            assert args.reference_project == ['proj1=/path/to/proj1', 'proj2=/path/to/proj2']

    @patch('mcp_server_filesystem.main.Path.exists')
    @patch('mcp_server_filesystem.main.Path.is_dir')
    def test_auto_rename_duplicates(self, mock_is_dir: MagicMock, mock_exists: MagicMock) -> None:
        """Test auto-renaming duplicate project names."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Test duplicate names get auto-renamed
        reference_args = ['proj=/path/to/proj1', 'proj=/path/to/proj2', 'proj=/path/to/proj3']
        result = validate_reference_projects(reference_args)
        
        expected = {
            'proj': Path('/path/to/proj1').absolute(),
            'proj_2': Path('/path/to/proj2').absolute(), 
            'proj_3': Path('/path/to/proj3').absolute()
        }
        assert result == expected

    @patch('mcp_server_filesystem.main.structured_logger')
    @patch('mcp_server_filesystem.main.Path.exists')
    def test_invalid_format_warnings(self, mock_exists: MagicMock, mock_logger: MagicMock) -> None:
        """Test warnings for invalid argument formats."""
        mock_exists.return_value = False
        
        # Test invalid format (no '=' separator)
        reference_args = ['invalid_format', 'valid=/path/to/proj']
        result = validate_reference_projects(reference_args)
        
        # Should log warning for invalid format
        mock_logger.warning.assert_called()
        # Check if the warning was called with the expected message
        calls = mock_logger.warning.call_args_list
        assert len(calls) > 0
        # Look for the specific warning message about missing '='
        found_invalid_format = any('missing' in str(call) and '=' in str(call) for call in calls)
        assert found_invalid_format

    @patch('mcp_server_filesystem.main.Path.exists')
    @patch('mcp_server_filesystem.main.Path.is_dir')
    def test_path_normalization(self, mock_is_dir: MagicMock, mock_exists: MagicMock) -> None:
        """Test conversion to absolute paths."""
        # Mock path validation
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Test relative path gets converted to absolute
        reference_args = ['proj=./relative/path']
        result = validate_reference_projects(reference_args)
        
        # Should contain absolute path
        assert 'proj' in result
        assert result['proj'].is_absolute()
        
    @patch('mcp_server_filesystem.main.structured_logger')
    @patch('mcp_server_filesystem.main.Path.exists')  
    def test_nonexistent_path_warning(self, mock_exists: MagicMock, mock_logger: MagicMock) -> None:
        """Test warnings for non-existent paths."""
        mock_exists.return_value = False
        
        reference_args = ['proj=/nonexistent/path']
        result = validate_reference_projects(reference_args)
        
        # Should log warning and return empty dict
        mock_logger.warning.assert_called()
        assert result == {}

    @patch('mcp_server_filesystem.main.Path.exists')
    @patch('mcp_server_filesystem.main.Path.is_dir')
    def test_empty_name_validation(self, mock_is_dir: MagicMock, mock_exists: MagicMock) -> None:
        """Test validation of empty project names."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Test empty name gets rejected
        reference_args = ['=/path/to/proj']
        with patch('mcp_server_filesystem.main.structured_logger') as mock_logger:
            result = validate_reference_projects(reference_args)
            
            # Should log warning for empty name
            mock_logger.warning.assert_called()
            assert result == {}
