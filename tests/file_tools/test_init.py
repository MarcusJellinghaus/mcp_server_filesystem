"""Tests for the file_tools package initialization."""

# Import all public functions directly from the main package
from src.file_tools import (
    delete_file,
    get_project_dir,
    list_files,
    normalize_path,
    read_file,
    write_file,
)


def test_imports():
    """Test that all functions are properly imported from the package."""
    # This test simply verifies that all functions can be imported from the main package
    # No need to call them, just ensure they exist
    assert callable(get_project_dir)
    assert callable(normalize_path)
    assert callable(read_file)
    assert callable(write_file)
    assert callable(delete_file)
    assert callable(list_files)
