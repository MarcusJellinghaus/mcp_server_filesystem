"""Basic integration tests for gitignore functionality."""

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from src.file_tools.directory_utils import filter_files_with_gitignore


def test_no_gitignore_spec():
    """Test with no gitignore spec."""
    files = ["file1.txt", "file2.log"]
    result = filter_files_with_gitignore(files, None)
    assert result == files


def test_basic_extension_filtering():
    """Test basic extension-based filtering."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["*.log"])
    files = ["file1.txt", "file2.log", "data.csv"]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["file1.txt", "data.csv"]
    
    assert set(filtered) == set(expected)


def test_directory_pattern():
    """Test directory pattern with trailing slash."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["build/"])
    files = [
        "file1.txt", 
        "build/output.txt", 
        "src/main.py"
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["file1.txt", "src/main.py"]
    
    assert set(filtered) == set(expected)
