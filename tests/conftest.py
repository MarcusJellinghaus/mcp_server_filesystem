"""Test configuration and shared fixtures for file_tools tests."""

import os
import shutil
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up the project directory for testing
PROJECT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_file.txt"
TEST_CONTENT = "This is test content."


@pytest.fixture
def project_dir():
    """Fixture to provide the project directory for tests."""
    return PROJECT_DIR


@pytest.fixture(autouse=True)
def setup_and_cleanup():
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
                item.name.startswith("tmp")
                or item.name.endswith(".txt")
                or item.name.endswith(".log")
            ):
                item.unlink()
            elif item.is_dir() and item.name not in [".git", "ignored_dir", "subdir"]:
                shutil.rmtree(item)
    except Exception as e:
        print(f"Error during teardown: {e}")
