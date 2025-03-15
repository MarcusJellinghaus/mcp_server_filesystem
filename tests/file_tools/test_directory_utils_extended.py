"""Basic integration tests for directory_utils module with GitWildMatchPattern."""

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from src.file_tools.directory_utils import filter_files_with_gitignore


def test_basic_filtering():
    """Test basic file filtering with GitWildMatchPattern."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["*.log"])
    files = ["file1.txt", "file2.log"]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["file1.txt"]
    
    assert set(filtered) == set(expected)
