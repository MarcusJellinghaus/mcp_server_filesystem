"""Tests for path_utils functionality."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Import functions directly from the module
from mcp_workspace.file_tools.path_utils import normalize_line_endings, normalize_path
from tests.conftest import TEST_DIR


def test_normalize_line_endings_crlf() -> None:
    """Test normalizing CRLF line endings."""
    text_with_crlf = "line1\r\nline2\r\nline3"
    normalized = normalize_line_endings(text_with_crlf)
    assert normalized == "line1\nline2\nline3"


def test_normalize_line_endings_standalone_cr() -> None:
    """Test normalizing standalone CR line endings."""
    text_with_cr = "line1\rline2\rline3"
    normalized = normalize_line_endings(text_with_cr)
    assert normalized == "line1\nline2\nline3"


def test_normalize_line_endings_mixed() -> None:
    """Test normalizing mixed line endings."""
    text_mixed = "a\r\nb\rc\n"
    normalized = normalize_line_endings(text_mixed)
    assert normalized == "a\nb\nc\n"


def test_normalize_path_relative() -> None:
    """Test normalizing a relative path."""
    # Define the project directory for testing
    project_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    relative_path = str(TEST_DIR / "test_file.txt")

    abs_path, rel_path = normalize_path(relative_path, project_dir)

    # Check that the absolute path is correct
    assert abs_path == project_dir / relative_path

    # Check that the relative path is correct
    assert rel_path == relative_path


def test_normalize_path_absolute() -> None:
    """Test normalizing an absolute path."""
    # Define the project directory for testing
    project_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    test_file = TEST_DIR / "test_file.txt"
    absolute_path = str(project_dir / test_file)

    abs_path, rel_path = normalize_path(absolute_path, project_dir)

    # Check that the absolute path is correct
    assert abs_path == Path(absolute_path)

    # Check that the relative path is correct
    assert rel_path == str(test_file)


def test_normalize_path_security_error_absolute() -> None:
    """Test security check with an absolute path outside the project directory."""
    # Define the project directory for testing
    project_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

    # Try to access a path outside the project directory
    with pytest.raises(ValueError) as excinfo:
        normalize_path("/tmp/outside_project.txt", project_dir)

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)


def test_normalize_path_oserror_with_traversal_rejected() -> None:
    """When resolve() raises OSError, paths with '..' are rejected."""
    project_dir = Path("/fake/project")
    with patch.object(Path, "resolve", side_effect=OSError("mocked")):
        with pytest.raises(ValueError) as excinfo:
            normalize_path("../etc/passwd", project_dir)
        assert "Security error" in str(excinfo.value)
        assert "traversal" in str(excinfo.value)


def test_normalize_path_oserror_clean_path_passes() -> None:
    """When resolve() raises OSError, clean relative paths pass through."""
    project_dir = Path("/fake/project")
    with patch.object(Path, "resolve", side_effect=OSError("mocked")):
        abs_path, rel_path = normalize_path("subdir/file.txt", project_dir)
    assert abs_path == project_dir / "subdir/file.txt"
    assert Path(rel_path) == Path("subdir/file.txt")


def test_normalize_path_security_error_relative() -> None:
    """Test security check with a relative path that tries to escape."""
    # Define the project directory for testing
    project_dir = Path(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

    # Try to access a path outside the project directory using path traversal
    with pytest.raises(ValueError) as excinfo:
        normalize_path("../outside_project.txt", project_dir)

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)
