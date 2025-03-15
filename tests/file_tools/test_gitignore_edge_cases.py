"""Basic tests for gitignore functionality."""

import pytest
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from src.file_tools.directory_utils import filter_files_with_gitignore


def test_path_normalization():
    """Test path normalization with different slash styles."""
    spec = PathSpec.from_lines(GitWildMatchPattern, ["docs/api/"])
    files = [
        "docs/api/index.html",
        "docs\\api\\reference.txt"
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    assert len(filtered) == 0, "Both paths should be filtered with normalized slashes"


def test_multiple_patterns():
    """Test multiple patterns together."""
    spec = PathSpec.from_lines(GitWildMatchPattern, [
        "*.log",
        "build/",
        "temp/",
    ])
    
    files = [
        "file.txt",
        "debug.log",
        "build/output.js",
        "temp/cache.dat",
        "src/module.js",
    ]
    
    filtered = filter_files_with_gitignore(files, spec)
    expected = ["file.txt", "src/module.js"]
    
    assert set(filtered) == set(expected)
