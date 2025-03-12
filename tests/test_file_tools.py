"""Tests for file_tools module."""

import os
import shutil
import sys
from pathlib import Path

import pytest

from src.file_tools import list_files, read_file, write_file

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up the project directory for testing
os.environ["MCP_PROJECT_DIR"] = os.path.abspath(os.path.dirname(__file__))


# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_file.txt"
TEST_CONTENT = "This is test content."


def setup_function():
    """Setup for each test function."""
    # Ensure the test directory exists
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    abs_test_dir.mkdir(parents=True, exist_ok=True)


def teardown_function():
    """Teardown for each test function."""
    # Clean up all created files
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR

    try:
        # List of files and patterns to remove
        files_to_remove = [
            "test_file.txt",
            "normal.txt",
            "test.ignore",
            "test_api_file.txt",
            "test_normal.txt",
        ]

        # Remove specific files
        for filename in files_to_remove:
            file_path = abs_test_dir / filename
            if file_path.exists():
                file_path.unlink()

        # Remove .git directory
        git_dir = abs_test_dir / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        # Remove ignored_dir if it exists
        ignored_dir = abs_test_dir / "ignored_dir"
        if ignored_dir.exists():
            shutil.rmtree(ignored_dir)

        # Remove any leftover temporary files
        for item in abs_test_dir.iterdir():
            if item.is_file() and (
                item.name.startswith("tmp") or item.name.endswith(".txt")
            ):
                item.unlink()
            elif item.is_dir() and item.name not in [".git", "ignored_dir"]:
                shutil.rmtree(item)
    except Exception as e:
        print(f"Error during teardown: {e}")


def test_write_file():
    """Test writing to a file."""
    # Test writing to a file
    result = write_file(str(TEST_FILE), TEST_CONTENT)

    # Create path for verification
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    # Verify the file was written
    assert result is True
    assert abs_file_path.exists()

    # Verify the file content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_write_file_atomic_overwrite():
    """Test atomically overwriting an existing file."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    # Create initial content
    initial_content = "This is the initial content."
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Verify initial content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == initial_content

    # Overwrite with new content
    new_content = "This is the new content that replaces the old content."
    result = write_file(str(TEST_FILE), new_content)

    # Verify the file was written
    assert result is True
    assert abs_file_path.exists()

    # Verify the new content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == new_content

    # Verify no temporary files were left behind
    parent_dir = abs_file_path.parent
    temp_files = [
        f
        for f in parent_dir.iterdir()
        if f.name.startswith("tmp") and f != abs_file_path
    ]
    assert len(temp_files) == 0


def test_read_file():
    """Test reading from a file."""
    # Create an absolute path for test file creation
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Test reading the file
    content = read_file(str(TEST_FILE))

    # Verify the content
    assert content == TEST_CONTENT


def test_read_file_not_found():
    """Test reading a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent.txt"

    # Ensure the file doesn't exist
    if non_existent_file.exists():
        non_existent_file.unlink()

    # Test reading a non-existent file
    with pytest.raises(FileNotFoundError):
        read_file(str(non_existent_file))


def test_list_files():
    """Test listing files in a directory."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    abs_test_file = abs_test_dir / TEST_FILE.name

    # Create a test file
    with open(abs_test_file, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Test listing files
    files = list_files(str(TEST_DIR))

    # Verify the file is in the list
    assert TEST_FILE.name in files


def test_list_files_with_gitignore():
    """Test listing files with gitignore filtering."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR

    # Ensure test directory exists
    abs_test_dir.mkdir(parents=True, exist_ok=True)

    # Create a .git directory that should be ignored
    git_dir = abs_test_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (git_dir / "HEAD").touch()

    # Create some test files
    (abs_test_dir / "normal.txt").touch()
    (abs_test_dir / "test.ignore").touch()
    ignored_dir = abs_test_dir / "ignored_dir"
    ignored_dir.mkdir(exist_ok=True)
    (ignored_dir / "ignored_file.txt").touch()

    # Create a gitignore file
    with open(abs_test_dir / ".gitignore", "w", encoding="utf-8") as f:
        f.write("*.ignore\nignored_dir/\n")

    # Test listing files with gitignore filtering
    files = list_files(str(TEST_DIR))

    # The .gitignore should exclude *.ignore files, the ignored_dir/, and .git/
    assert "normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" not in files
    assert "ignored_dir" not in files
    assert ".git" not in files


def test_list_files_without_gitignore():
    """Test listing files without gitignore filtering."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR

    # Ensure test directory exists
    abs_test_dir.mkdir(parents=True, exist_ok=True)

    # Create a .git directory that should be included when gitignore is disabled
    git_dir = abs_test_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (git_dir / "HEAD").touch()

    # Create some test files
    (abs_test_dir / "normal.txt").touch()
    (abs_test_dir / "test.ignore").touch()
    ignored_dir = abs_test_dir / "ignored_dir"
    ignored_dir.mkdir(exist_ok=True)
    (ignored_dir / "ignored_file.txt").touch()

    # Create a gitignore file
    with open(abs_test_dir / ".gitignore", "w", encoding="utf-8") as f:
        f.write("*.ignore\nignored_dir/\n")

    # Test listing files without gitignore filtering
    files = list_files(str(TEST_DIR), use_gitignore=False)

    # When gitignore is disabled, all files should be included
    assert "normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" in files
    assert "ignored_dir" in files
    assert ".git" in files


def test_list_files_directory_not_found():
    """Test listing files in a directory that doesn't exist."""
    non_existent_dir = TEST_DIR / "non_existent_dir"

    # Ensure the directory doesn't exist
    if non_existent_dir.exists():
        if non_existent_dir.is_dir():
            os.rmdir(non_existent_dir)
        else:
            non_existent_dir.unlink()

    # Test listing files in a non-existent directory
    with pytest.raises(FileNotFoundError):
        list_files(str(non_existent_dir))
