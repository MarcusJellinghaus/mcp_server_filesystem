"""Tests for the MCP server API endpoints."""

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_filesystem.server import (
    append_file,
    list_directory,
    read_file,
    save_file,
    set_project_dir,
)

# Python path is now configured via pytest configuration in pyproject.toml

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_api_file.txt"
TEST_CONTENT = "This is API test content."


@pytest.fixture(autouse=True)
def setup_server(project_dir: Path) -> Generator[None, None, None]:
    """Setup the server with the project directory."""
    set_project_dir(project_dir)
    yield


def setup_function() -> None:
    """Setup for each test function."""
    # Ensure the test directory exists
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function() -> None:
    """Teardown for each test function."""
    # Clean up any test files
    if TEST_FILE.exists():
        TEST_FILE.unlink()


def test_save_file(project_dir: Path) -> None:
    """Test the save_file tool."""
    result = save_file(str(TEST_FILE), TEST_CONTENT)

    # Create absolute path for verification
    abs_file_path = project_dir / TEST_FILE

    assert result is True
    assert abs_file_path.exists()

    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_read_file(project_dir: Path) -> None:
    """Test the read_file tool."""
    # Create absolute path for test file
    abs_file_path = project_dir / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    content = read_file(str(TEST_FILE))

    assert content == TEST_CONTENT


def test_read_file_not_found() -> None:
    """Test the read_file tool with a non-existent file."""
    non_existent_file = TEST_DIR / "non_existent.txt"

    # Ensure the file doesn't exist
    if Path(non_existent_file).exists():
        Path(non_existent_file).unlink()

    with pytest.raises(FileNotFoundError):
        read_file(str(non_existent_file))


def test_append_file(project_dir: Path) -> None:
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


def test_append_file_empty(project_dir: Path) -> None:
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


def test_append_file_not_found() -> None:
    """Test appending to a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent_append.txt"

    # Ensure the file doesn't exist
    if Path(non_existent_file).exists():
        Path(non_existent_file).unlink()

    # Test appending to a non-existent file
    with pytest.raises(FileNotFoundError):
        append_file(str(non_existent_file), "This should fail")


@patch("mcp_server_filesystem.server.list_files_util")
def test_list_directory(mock_list_files: MagicMock, project_dir: Path) -> None:
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


@patch("mcp_server_filesystem.server.list_files_util")
def test_list_directory_directory_not_found(
    mock_list_files: MagicMock, project_dir: Path
) -> None:
    """Test the list_directory tool with a non-existent directory."""
    # Mock list_files to raise FileNotFoundError
    mock_list_files.side_effect = FileNotFoundError("Directory not found")

    with pytest.raises(FileNotFoundError):
        list_directory()


@patch("mcp_server_filesystem.server.list_files_util")
def test_list_directory_with_gitignore(
    mock_list_files: MagicMock, project_dir: Path
) -> None:
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


@patch("mcp_server_filesystem.server.list_files_util")
def test_list_directory_error_handling(
    mock_list_files: MagicMock, project_dir: Path
) -> None:
    """Test error handling in the list_directory tool."""
    # Mock list_files to raise an exception
    mock_list_files.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        list_directory()


def test_move_file(project_dir: Path) -> None:
    """Test the move_file tool."""
    # Import move_file here to avoid issues if not yet implemented
    from mcp_server_filesystem.server import move_file

    # Create source file
    source_file = TEST_DIR / "source.txt"
    dest_file = TEST_DIR / "dest.txt"
    abs_source = project_dir / source_file
    abs_dest = project_dir / dest_file

    # Create source file
    abs_source.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_source, "w", encoding="utf-8") as f:
        f.write("Test content")

    # Clean up destination if exists
    if abs_dest.exists():
        abs_dest.unlink()

    # Move the file
    result = move_file(str(source_file), str(dest_file))

    assert result is True
    assert not abs_source.exists()
    assert abs_dest.exists()
    with open(abs_dest, "r", encoding="utf-8") as f:
        assert f.read() == "Test content"

    # Clean up
    if abs_dest.exists():
        abs_dest.unlink()


def test_move_file_simplified_errors(project_dir: Path) -> None:
    """Test that server endpoint returns simplified error messages."""
    # Import move_file here to avoid issues if not yet implemented
    from mcp_server_filesystem.server import move_file

    # Test file not found
    with pytest.raises(FileNotFoundError) as exc_info:
        move_file("nonexistent.txt", "dest.txt")
    assert str(exc_info.value) == "File not found"  # Simple message

    # Test destination exists
    source_file = TEST_DIR / "source_exists.txt"
    dest_file = TEST_DIR / "existing.txt"
    abs_source = project_dir / source_file
    abs_dest = project_dir / dest_file

    # Create both files
    abs_source.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_source, "w", encoding="utf-8") as f:
        f.write("Source")
    with open(abs_dest, "w", encoding="utf-8") as f:
        f.write("Existing")

    with pytest.raises(FileExistsError) as exc_info2:
        move_file(str(source_file), str(dest_file))
    assert str(exc_info2.value) == "Destination already exists"  # Simple message

    # Clean up
    if abs_source.exists():
        abs_source.unlink()
    if abs_dest.exists():
        abs_dest.unlink()


@patch("mcp_server_filesystem.server.move_file_util")
def test_move_file_permission_error(mock_move: MagicMock, project_dir: Path) -> None:
    """Test permission error handling in move_file."""
    # Import move_file here to avoid issues if not yet implemented
    from mcp_server_filesystem.server import move_file

    # Mock move_file_util to raise PermissionError
    mock_move.side_effect = PermissionError("Access denied to file: /some/path")

    with pytest.raises(PermissionError) as exc:
        move_file("readonly.txt", "dest.txt")
    assert str(exc.value) == "Permission denied"  # Simple message


@patch("mcp_server_filesystem.server.move_file_util")
def test_move_file_security_error(mock_move: MagicMock, project_dir: Path) -> None:
    """Test security error handling in move_file."""
    # Import move_file here to avoid issues if not yet implemented
    from mcp_server_filesystem.server import move_file

    # Mock move_file_util to raise ValueError with security message
    mock_move.side_effect = ValueError("Security: Path outside project directory")

    with pytest.raises(ValueError) as exc:
        move_file("../outside.txt", "dest.txt")
    assert str(exc.value) == "Invalid path"  # Simple message


@patch("mcp_server_filesystem.server.move_file_util")
def test_move_file_generic_error(mock_move: MagicMock, project_dir: Path) -> None:
    """Test generic error handling in move_file."""
    # Import move_file here to avoid issues if not yet implemented
    from mcp_server_filesystem.server import move_file

    # Mock move_file_util to raise a generic exception
    mock_move.side_effect = RuntimeError("Some complex internal error")

    with pytest.raises(RuntimeError) as exc:
        move_file("source.txt", "dest.txt")
    assert str(exc.value) == "Move operation failed"  # Simple message
