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

        # Remove subdir if it exists (for recursive tests)
        subdir = abs_test_dir / "subdir"
        if subdir.exists():
            shutil.rmtree(subdir)

        # Remove any leftover temporary files
        for item in abs_test_dir.iterdir():
            if item.is_file() and (
                item.name.startswith("tmp") or item.name.endswith(".txt")
            ):
                item.unlink()
            elif item.is_dir() and item.name not in [".git", "ignored_dir", "subdir"]:
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
    abs_non_existent = Path(os.environ["MCP_PROJECT_DIR"]) / non_existent_file
    if abs_non_existent.exists():
        abs_non_existent.unlink()

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
    expected_file_path = str(TEST_DIR / TEST_FILE.name).replace("\\", "/")
    files = [path.replace("\\", "/") for path in files]
    assert expected_file_path in files


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
    files = [path.replace("\\", "/") for path in files]

    # The .gitignore should exclude *.ignore files, the ignored_dir/, and .git/
    assert str(TEST_DIR / "normal.txt").replace("\\", "/") in files
    assert str(TEST_DIR / ".gitignore").replace("\\", "/") in files
    assert str(TEST_DIR / "test.ignore").replace("\\", "/") not in files
    assert str(TEST_DIR / "ignored_dir/ignored_file.txt").replace("\\", "/") not in files
    assert str(TEST_DIR / ".git/HEAD").replace("\\", "/") not in files


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
    files = [path.replace("\\", "/") for path in files]

    # When gitignore is disabled, all files should be included
    assert str(TEST_DIR / "normal.txt").replace("\\", "/") in files
    assert str(TEST_DIR / ".gitignore").replace("\\", "/") in files
    assert str(TEST_DIR / "test.ignore").replace("\\", "/") in files
    assert str(TEST_DIR / "ignored_dir/ignored_file.txt").replace("\\", "/") in files
    assert str(TEST_DIR / ".git/HEAD").replace("\\", "/") in files


def test_list_files_directory_not_found():
    """Test listing files in a directory that doesn't exist."""
    non_existent_dir = TEST_DIR / "non_existent_dir"

    # Ensure the directory doesn't exist
    abs_non_existent = Path(os.environ["MCP_PROJECT_DIR"]) / non_existent_dir
    if abs_non_existent.exists():
        if abs_non_existent.is_dir():
            shutil.rmtree(abs_non_existent)
        else:
            abs_non_existent.unlink()

    # Test listing files in a non-existent directory
    with pytest.raises(FileNotFoundError):
        list_files(str(non_existent_dir))


def test_list_files_recursive():
    """Test listing files recursively in a directory structure."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    abs_test_file = abs_test_dir / TEST_FILE.name

    # Ensure the test directory exists
    abs_test_dir.mkdir(parents=True, exist_ok=True)

    # Create a test file
    with open(abs_test_file, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Create subdirectories and files
    sub_dir = abs_test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)
    sub_file = sub_dir / "subfile.txt"
    with open(sub_file, "w", encoding="utf-8") as f:
        f.write("Subfile content")

    nested_dir = sub_dir / "nested"
    nested_dir.mkdir(exist_ok=True)
    nested_file = nested_dir / "nested_file.txt"
    with open(nested_file, "w", encoding="utf-8") as f:
        f.write("Nested file content")

    # Create a .gitignore to ignore some patterns
    with open(abs_test_dir / ".gitignore", "w", encoding="utf-8") as f:
        f.write("*.ignore\nignored_dir/\n")

    # Create an ignored file and directory
    (abs_test_dir / "test.ignore").touch()
    ignored_dir = abs_test_dir / "ignored_dir"
    ignored_dir.mkdir(exist_ok=True)
    (ignored_dir / "ignored_file.txt").touch()

    # Test listing files
    files = list_files(str(TEST_DIR))

    # Verify expected paths are in the list
    expected_paths = [
        str(TEST_DIR / TEST_FILE.name),
        str(TEST_DIR / ".gitignore"),
        str(TEST_DIR / "subdir" / "subfile.txt"),
        str(TEST_DIR / "subdir" / "nested" / "nested_file.txt")
    ]

    # Replace backslashes with forward slashes for consistent path comparison
    files = [path.replace("\\", "/") for path in files]
    expected_paths = [path.replace("\\", "/") for path in expected_paths]

    # Check that all expected paths are in the list
    for path in expected_paths:
        assert path in files, f"Expected {path} to be in the list"

    # Check that ignored paths are not in the list
    ignored_paths = [
        str(TEST_DIR / "test.ignore"),
        str(TEST_DIR / "ignored_dir" / "ignored_file.txt")
    ]
    
    ignored_paths = [path.replace("\\", "/") for path in ignored_paths]

    for path in ignored_paths:
        assert path not in files, f"Did not expect {path} to be in the list"
