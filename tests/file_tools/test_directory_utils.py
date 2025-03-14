"""Tests for directory_utils module."""

import os
import shutil
from pathlib import Path

import pytest

# Import directly from src using absolute imports
from src.file_tools.directory_utils import list_files
from tests.conftest import TEST_CONTENT, TEST_DIR, TEST_FILE


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
    assert (
        str(TEST_DIR / "ignored_dir/ignored_file.txt").replace("\\", "/") not in files
    )
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
        str(TEST_DIR / "subdir" / "nested" / "nested_file.txt"),
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
        str(TEST_DIR / "ignored_dir" / "ignored_file.txt"),
    ]

    ignored_paths = [path.replace("\\", "/") for path in ignored_paths]

    for path in ignored_paths:
        assert path not in files, f"Did not expect {path} to be in the list"


def test_list_files_security():
    """Test security checks in list_files."""
    # Try to list files outside the project directory
    with pytest.raises(ValueError) as excinfo:
        list_files("../outside_project")

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)
