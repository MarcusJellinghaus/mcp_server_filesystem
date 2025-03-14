"""Tests for path_utils functionality."""

import os
from pathlib import Path

import pytest

# Import functions directly from the module
from src.file_tools.path_utils import get_project_dir, normalize_path
from tests.conftest import TEST_DIR


def test_get_project_dir():
    """Test getting the project directory."""
    # The project dir is set to the tests directory in conftest.py
    expected_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    result = get_project_dir()

    assert result == expected_dir


def test_normalize_path_relative():
    """Test normalizing a relative path."""
    relative_path = str(TEST_DIR / "test_file.txt")

    abs_path, rel_path = normalize_path(relative_path)

    # Check that the absolute path is correct
    assert abs_path == Path(os.environ["MCP_PROJECT_DIR"]) / relative_path

    # Check that the relative path is correct
    assert rel_path == relative_path


def test_normalize_path_absolute():
    """Test normalizing an absolute path."""
    project_dir = get_project_dir()
    test_file = TEST_DIR / "test_file.txt"
    absolute_path = str(project_dir / test_file)

    abs_path, rel_path = normalize_path(absolute_path)

    # Check that the absolute path is correct
    assert abs_path == Path(absolute_path)

    # Check that the relative path is correct
    assert rel_path == str(test_file)


def test_normalize_path_security_error_absolute():
    """Test security check with an absolute path outside the project directory."""
    # Try to access a path outside the project directory
    with pytest.raises(ValueError) as excinfo:
        normalize_path("/tmp/outside_project.txt")

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)


def test_normalize_path_security_error_relative():
    """Test security check with a relative path that tries to escape."""
    # Try to access a path outside the project directory using path traversal
    with pytest.raises(ValueError) as excinfo:
        normalize_path("../outside_project.txt")

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)
