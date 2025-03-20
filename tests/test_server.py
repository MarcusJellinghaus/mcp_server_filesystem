"""Tests for the MCP server API endpoints."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.server import (
    append_file,
    list_directory,
    read_file,
    save_file,
    set_project_dir,
)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_api_file.txt"
TEST_CONTENT = "This is API test content."


@pytest.fixture(autouse=True)
def setup_server(project_dir):
    """Setup the server with the project directory."""
    set_project_dir(project_dir)
    yield


def setup_function():
    """Setup for each test function."""
    # Ensure the test directory exists
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function():
    """Teardown for each test function."""
    # Clean up any test files
    if TEST_FILE.exists():
        TEST_FILE.unlink()


def test_save_file(project_dir):
    """Test the save_file tool."""
    result = save_file(str(TEST_FILE), TEST_CONTENT)

    # Create absolute path for verification
    abs_file_path = project_dir / TEST_FILE

    assert result is True
    assert abs_file_path.exists()

    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_read_file(project_dir):
    """Test the read_file tool."""
    # Create absolute path for test file
    abs_file_path = project_dir / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    content = read_file(str(TEST_FILE))

    assert content == TEST_CONTENT


def test_read_file_not_found():
    """Test the read_file tool with a non-existent file."""
    non_existent_file = TEST_DIR / "non_existent.txt"

    # Ensure the file doesn't exist
    if Path(non_existent_file).exists():
        Path(non_existent_file).unlink()

    with pytest.raises(FileNotFoundError):
        read_file(str(non_existent_file))


def test_append_file(project_dir):
    """Test the append_file tool."""
    # Create absolute path for test file
    abs_file_path = project_dir / TEST_FILE

    # Create initial content
    initial_content = "Initial content.\n"
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content to the file
    append_content = "Appended content."
    result = append_file(str(TEST_FILE), append_content)

    # Verify the file was updated
    assert result is True
    assert abs_file_path.exists()

    # Verify the combined content
    expected_content = initial_content + append_content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == expected_content


def test_append_file_empty(project_dir):
    """Test appending to an empty file."""
    # Create the empty file
    empty_file = TEST_DIR / "empty_file.txt"
    abs_file_path = project_dir / empty_file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        pass  # Create an empty file

    # Append content to the empty file
    append_content = "Content added to empty file."
    result = append_file(str(empty_file), append_content)

    # Verify the file was updated
    assert result is True
    assert abs_file_path.exists()

    # Verify the content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == append_content


def test_append_file_not_found():
    """Test appending to a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent_append.txt"

    # Ensure the file doesn't exist
    if Path(non_existent_file).exists():
        Path(non_existent_file).unlink()

    # Test appending to a non-existent file
    with pytest.raises(FileNotFoundError):
        append_file(str(non_existent_file), "This should fail")


@patch("src.server.list_files_util")
def test_list_directory(mock_list_files, project_dir):
    """Test the list_directory tool."""
    # Create absolute path for test file
    abs_file_path = project_dir / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Mock the list_files function to return our test file
    mock_list_files.return_value = [str(TEST_FILE)]

    files = list_directory()

    # Verify the function was called with correct parameters
    mock_list_files.assert_called_once_with(
        ".", project_dir=project_dir, use_gitignore=True
    )

    assert str(TEST_FILE) in files


@patch("src.server.list_files_util")
def test_list_directory_directory_not_found(mock_list_files, project_dir):
    """Test the list_directory tool with a non-existent directory."""
    # Mock list_files to raise FileNotFoundError
    mock_list_files.side_effect = FileNotFoundError("Directory not found")

    with pytest.raises(FileNotFoundError):
        list_directory()


@patch("src.server.list_files_util")
def test_list_directory_with_gitignore(mock_list_files, project_dir):
    """Test the list_directory tool with gitignore filtering."""
    # Mock list_files to return filtered files
    mock_list_files.return_value = [
        str(TEST_DIR / "test_normal.txt"),
        str(TEST_DIR / ".gitignore"),
    ]

    files = list_directory()

    # Verify the function was called with gitignore=True
    mock_list_files.assert_called_once_with(
        ".", project_dir=project_dir, use_gitignore=True
    )

    assert str(TEST_DIR / "test_normal.txt") in files
    assert str(TEST_DIR / ".gitignore") in files


@patch("src.server.list_files_util")
def test_list_directory_error_handling(mock_list_files, project_dir):
    """Test error handling in the list_directory tool."""
    # Mock list_files to raise an exception
    mock_list_files.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        list_directory()
