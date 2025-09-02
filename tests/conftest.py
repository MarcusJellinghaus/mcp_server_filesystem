"""Test configuration and shared fixtures for file_tools tests."""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

# Python path is now configured via pytest configuration in pyproject.toml

# Set up the project directory for testing
PROJECT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_file.txt"
TEST_CONTENT = "This is test content."


def _is_temporary_test_file(item: Path) -> bool:
    """Check if a file should be considered a temporary test file.

    Args:
        item: Path to the file to check

    Returns:
        True if the file is a temporary test file
    """
    return (
        item.name.startswith("tmp")
        or item.name.endswith(".txt")
        or item.name.endswith(".log")
        or item.name.endswith(".py")
        or item.name.endswith(".md")
    )


@pytest.fixture
def project_dir() -> Path:
    """Fixture to provide the project directory for tests."""
    return PROJECT_DIR


@pytest.fixture(autouse=True)
def setup_and_cleanup() -> Generator[None, None, None]:
    """
    Fixture to set up and clean up test environment.

    This is automatically used for all tests.
    """
    # Setup: Ensure the test directory exists
    abs_test_dir = PROJECT_DIR / TEST_DIR
    abs_test_dir.mkdir(parents=True, exist_ok=True)

    # Run the test
    yield

    # Teardown: Clean up all created files
    try:
        # List of files and patterns to remove
        files_to_remove = [
            "test_file.txt",
            "normal.txt",
            "test.ignore",
            "test_api_file.txt",
            "test_edit_api_file.txt",
            "test_normal.txt",
            "file_to_delete.txt",
            ".gitignore",
            "test1.txt",
            "test2.txt",
            "test3.txt",
            "keep.txt",
            "ignore.log",
            "dont_ignore.log",
            "not_a_dir.txt",
            # New temporary test files
            "indentation_test_temp.py",
            "markdown_test_temp.md",
            "empty_file.txt",
            "large_file.txt",
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

        # Remove any leftover temporary files including Python files
        for item in abs_test_dir.iterdir():
            # Check if file should be removed
            is_temp_file = item.is_file() and _is_temporary_test_file(item)
            is_permanent_file = item.name in ["test_file.txt", "test_api_file.txt"]

            if is_temp_file and not is_permanent_file:
                item.unlink()
            elif item.is_dir() and item.name not in [".git", "ignored_dir", "subdir"]:
                shutil.rmtree(item)
    except Exception as e:
        print(f"Error during teardown: {e}")
