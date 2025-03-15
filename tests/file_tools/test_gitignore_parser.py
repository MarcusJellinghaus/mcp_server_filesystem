"""Test cases for directory_utils module with the gitignore-parser library."""

import os
import tempfile
from pathlib import Path

import pytest
from gitignore_parser import parse_gitignore

from src.file_tools.directory_utils import filter_files_with_gitignore


def test_filter_files_none_matcher():
    """Test with no gitignore matcher."""
    files = ["file1.txt", "file2.log"]
    result = filter_files_with_gitignore(files, None)
    assert result == files


def create_temp_gitignore(content: str) -> Path:
    """Create a temporary .gitignore file with given content."""
    temp_dir = tempfile.mkdtemp()
    gitignore_path = Path(temp_dir) / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write(content)
    return gitignore_path


def test_basic_extension_filtering():
    """Test basic extension-based filtering."""
    gitignore_path = create_temp_gitignore("*.log")
    matcher = parse_gitignore(gitignore_path)
    
    # Using absolute paths for test
    cwd = os.getcwd()
    files = [
        "file1.txt",
        "file2.log", 
        "data.csv"
    ]
    
    # Convert to absolute paths for testing
    abs_files = [os.path.join(cwd, f) for f in files]
    
    filtered = filter_files_with_gitignore(abs_files, matcher)
    expected = [os.path.join(cwd, "file1.txt"), os.path.join(cwd, "data.csv")]
    
    assert set(filtered) == set(expected)


def test_directory_pattern():
    """Test directory pattern with trailing slash."""
    gitignore_path = create_temp_gitignore("build/")
    matcher = parse_gitignore(gitignore_path)
    
    # Using absolute paths for test
    cwd = os.getcwd()
    files = [
        "file1.txt",
        "build/output.txt", 
        "src/main.py"
    ]
    
    # Convert to absolute paths for testing
    abs_files = [os.path.join(cwd, f) for f in files]
    
    filtered = filter_files_with_gitignore(abs_files, matcher)
    expected = [os.path.join(cwd, "file1.txt"), os.path.join(cwd, "src/main.py")]
    
    assert set(filtered) == set(expected)


def test_negation_patterns():
    """Test negation patterns (!pattern)."""
    gitignore_content = """
    *.log
    !important.log
    temp/
    !temp/keep/
    """
    gitignore_path = create_temp_gitignore(gitignore_content)
    matcher = parse_gitignore(gitignore_path)
    
    # Using absolute paths for test
    cwd = os.getcwd()
    files = [
        "debug.log",
        "important.log",
        "temp/file.txt",
        "temp/keep/file.txt",
        "temp/other/file.txt"
    ]
    
    # Convert to absolute paths for testing
    abs_files = [os.path.join(cwd, f) for f in files]
    
    filtered = filter_files_with_gitignore(abs_files, matcher)
    expected = [
        os.path.join(cwd, "important.log"),
        os.path.join(cwd, "temp/keep/file.txt")
    ]
    
    assert set(filtered) == set(expected)


def test_platform_specific_paths():
    """Test handling of platform-specific paths."""
    gitignore_path = create_temp_gitignore("temp/")
    matcher = parse_gitignore(gitignore_path)
    
    # Using absolute paths for test
    cwd = os.getcwd()
    files = [
        "temp/file.txt",
        "temp\\debug.log",  # Windows-style path
        "my-temp/data.json"
    ]
    
    # Convert to absolute paths for testing
    abs_files = [os.path.join(cwd, f.replace('\\', os.sep)) for f in files]
    
    filtered = filter_files_with_gitignore(abs_files, matcher)
    expected = [os.path.join(cwd, "my-temp/data.json")]
    
    assert set(filtered) == set(expected)
