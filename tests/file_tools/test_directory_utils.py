"""Tests for directory_utils functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import functions directly from the module
from src.file_tools.directory_utils import (
    _discover_files,
    filter_with_gitignore,
    list_files,
)
from tests.conftest import TEST_DIR


def test_discover_files():
    """Test discovering files in a directory recursively."""
    # Create test directory structure
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR

    # Create a subdirectory for testing recursion
    subdir = test_dir / "subdir"
    subdir.mkdir(exist_ok=True)

    # Create test files
    test_files = [test_dir / "test1.txt", test_dir / "test2.txt", subdir / "test3.txt"]

    for file_path in test_files:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Content for {file_path.name}")

    # Test file discovery
    discovered_files = _discover_files(test_dir)

    # Convert to a set for easy comparison
    rel_paths = set(str(Path(f)) for f in discovered_files)
    expected_paths = {
        str(Path("testdata/test_file_tools/test1.txt")),
        str(Path("testdata/test_file_tools/test2.txt")),
        str(Path("testdata/test_file_tools/subdir/test3.txt")),
    }

    # Check if all expected files were discovered
    assert rel_paths.issuperset(expected_paths)


def test_filter_with_gitignore_no_gitignore():
    """Test filtering files when no .gitignore file exists."""
    # Create a list of file paths
    file_paths = [
        "testdata/test_file_tools/file1.txt",
        "testdata/test_file_tools/file2.txt",
    ]

    # Test with a directory that doesn't have a .gitignore file
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR

    # Ensure no .gitignore file exists
    gitignore_path = test_dir / ".gitignore"
    if gitignore_path.exists():
        gitignore_path.unlink()

    # Test the filter with no .gitignore
    filtered_files = filter_with_gitignore(file_paths, test_dir)

    # Without a .gitignore file, all files should be returned
    assert set(filtered_files) == set(file_paths)


def test_filter_with_gitignore_with_rules():
    """Test filtering files based on .gitignore rules."""
    # Create a list of file paths including files to be ignored
    file_paths = [
        "testdata/test_file_tools/normal.txt",
        "testdata/test_file_tools/test.ignore",
        "testdata/test_file_tools/ignored_dir/file.txt",
    ]

    # Create the files and directories
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR
    ignored_dir = test_dir / "ignored_dir"
    ignored_dir.mkdir(exist_ok=True)

    # Create the files
    (test_dir / "normal.txt").write_text("normal file")
    (test_dir / "test.ignore").write_text("should be ignored")
    (ignored_dir / "file.txt").write_text("in ignored directory")

    # Create a .gitignore file with rules
    gitignore_path = test_dir / ".gitignore"
    gitignore_content = """
# Ignore files with .ignore extension
*.ignore

# Ignore specific directory
/ignored_dir/
"""
    gitignore_path.write_text(gitignore_content)

    # Mock the gitignore matcher behavior
    # This is needed because the actual behavior of gitignore_parser might differ
    # depending on the implementation and platform
    with patch("src.file_tools.directory_utils.parse_gitignore") as mock_parser:
        # Configure the mock to properly filter files
        mock_matcher = MagicMock()
        # Configure the matcher to ignore files with .ignore extension and in ignored_dir
        mock_matcher.side_effect = (
            lambda path: ".ignore" in path or "ignored_dir" in path
        )
        mock_parser.return_value = mock_matcher

        # Test the filter with the mocked .gitignore rules
        filtered_files = filter_with_gitignore(file_paths, test_dir)

        # Only the normal.txt file should remain after filtering
        assert filtered_files == ["testdata/test_file_tools/normal.txt"]


def test_filter_with_gitignore_error_handling():
    """Test error handling in gitignore filtering."""
    # Create a list of file paths
    file_paths = [
        "testdata/test_file_tools/file1.txt",
        "testdata/test_file_tools/file2.txt",
    ]

    # Mock the parse_gitignore function to raise an exception
    with patch(
        "src.file_tools.directory_utils.parse_gitignore",
        side_effect=Exception("Test error"),
    ):
        # Test the filter with a simulated error
        filtered_files = filter_with_gitignore(file_paths)

        # On error, the function should return the original list of files
        assert filtered_files == file_paths


def test_list_files_basic():
    """Test listing files in a directory."""
    # Create test directory structure
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR

    # Create test files
    test_files = [test_dir / "test1.txt", test_dir / "test2.txt"]

    for file_path in test_files:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"Content for {file_path.name}")

    # Test listing files with a mock to handle platform-specific path separators
    with patch("src.file_tools.directory_utils._discover_files") as mock_discover:
        # Configure the mock to return our test files with consistent path separators
        mock_discover.return_value = [
            "testdata/test_file_tools/test1.txt",
            "testdata/test_file_tools/test2.txt",
        ]

        # When gitignore filtering is active, avoid calling the real filter
        with patch(
            "src.file_tools.directory_utils.filter_with_gitignore",
            side_effect=lambda files, *args, **kwargs: files,
        ):
            # Test listing files
            files = list_files(str(TEST_DIR))

            # Check if all expected files are in the list
            expected_files = {
                "testdata/test_file_tools/test1.txt",
                "testdata/test_file_tools/test2.txt",
            }
            actual_files = set(files)

            # The files should match exactly
            assert actual_files == expected_files


def test_list_files_with_gitignore():
    """Test listing files with gitignore filtering."""
    # Create test directory structure
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR

    # Create test files including ones to be ignored
    (test_dir / "keep.txt").write_text("keep this file")
    (test_dir / "ignore.log").write_text("ignore this file")

    # Create .gitignore file
    gitignore_path = test_dir / ".gitignore"
    gitignore_path.write_text("*.log")

    # Mock the discovery and filtering
    with patch("src.file_tools.directory_utils._discover_files") as mock_discover:
        # Configure the mock to return our test files
        mock_discover.return_value = [
            "testdata/test_file_tools/keep.txt",
            "testdata/test_file_tools/ignore.log",
        ]

        # Mock the filter to remove .log files
        with patch(
            "src.file_tools.directory_utils.filter_with_gitignore"
        ) as mock_filter:
            mock_filter.return_value = ["testdata/test_file_tools/keep.txt"]

            # Test listing files with gitignore filtering
            files = list_files(str(TEST_DIR), use_gitignore=True)

            # The .log file should be filtered out
            assert files == ["testdata/test_file_tools/keep.txt"]
            assert not any(f.endswith("ignore.log") for f in files)


def test_list_files_without_gitignore():
    """Test listing files without gitignore filtering."""
    # Create test directory structure
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_dir = project_dir / TEST_DIR

    # Create test files including ones normally ignored
    (test_dir / "keep.txt").write_text("keep this file")
    (test_dir / "dont_ignore.log").write_text("don't ignore this file")

    # Create .gitignore file
    gitignore_path = test_dir / ".gitignore"
    gitignore_path.write_text("*.log")

    # Mock the discovery
    with patch("src.file_tools.directory_utils._discover_files") as mock_discover:
        # Configure the mock to return both files
        mock_discover.return_value = [
            "testdata/test_file_tools/keep.txt",
            "testdata/test_file_tools/dont_ignore.log",
        ]

        # Test listing files without gitignore filtering
        files = list_files(str(TEST_DIR), use_gitignore=False)

        # Both files should be included
        assert set(files) == {
            "testdata/test_file_tools/keep.txt",
            "testdata/test_file_tools/dont_ignore.log",
        }


def test_list_files_directory_not_found():
    """Test listing files in a non-existent directory."""
    non_existent_dir = "testdata/non_existent_dir"

    # Test with a non-existent directory
    with pytest.raises(FileNotFoundError) as excinfo:
        list_files(non_existent_dir)

    # Verify the error message
    assert f"Directory '{non_existent_dir}' does not exist" in str(excinfo.value)


def test_list_files_not_a_directory():
    """Test listing files on a path that is not a directory."""
    # Create a file
    project_dir = Path(os.environ["MCP_PROJECT_DIR"])
    test_file = project_dir / TEST_DIR / "not_a_dir.txt"
    test_file.write_text("This is not a directory")

    # Test with a file path instead of a directory
    with pytest.raises(NotADirectoryError) as excinfo:
        list_files(str(TEST_DIR / "not_a_dir.txt"))

    # Verify the error message
    assert "is not a directory" in str(excinfo.value)


def test_list_files_with_exception():
    """Test handling of unexpected exceptions in list_files."""
    # Mock _discover_files to raise an exception
    with patch(
        "src.file_tools.directory_utils._discover_files",
        side_effect=Exception("Test error"),
    ):
        # Test with a mocked exception
        with pytest.raises(Exception) as excinfo:
            list_files(str(TEST_DIR))

        # Verify that the exception is propagated
        assert "Test error" in str(excinfo.value)
