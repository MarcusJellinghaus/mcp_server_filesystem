"""Tests for the MCP server API endpoints."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.server import list_directory, read_file, write_file

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up the project directory for testing
os.environ["MCP_PROJECT_DIR"] = os.path.abspath(os.path.dirname(__file__))


# Test constants
TEST_DIR = Path("testdata/test_file_tools")
TEST_FILE = TEST_DIR / "test_api_file.txt"
TEST_CONTENT = "This is API test content."


def setup_function():
    """Setup for each test function."""
    # Ensure the test directory exists
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def teardown_function():
    """Teardown for each test function."""
    # Clean up any test files
    if TEST_FILE.exists():
        TEST_FILE.unlink()


@pytest.mark.asyncio
async def test_write_file():
    """Test the write_file tool."""
    result = await write_file(str(TEST_FILE), TEST_CONTENT)

    # Create absolute path for verification
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    assert result is True
    assert abs_file_path.exists()

    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == TEST_CONTENT


@pytest.mark.asyncio
async def test_read_file():
    """Test the read_file tool."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    content = await read_file(str(TEST_FILE))

    assert content == TEST_CONTENT


@pytest.mark.asyncio
@patch("src.server.list_files_util")
async def test_list_directory(mock_list_files):
    """Test the list_directory tool."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Mock the list_files function to return our test file
    mock_list_files.return_value = [str(TEST_FILE)]

    files = await list_directory()

    # Verify the function was called with correct parameters
    mock_list_files.assert_called_once_with(".", use_gitignore=True)

    assert str(TEST_FILE) in files


@pytest.mark.asyncio
async def test_read_file_not_found():
    """Test the read_file tool with a non-existent file."""
    non_existent_file = TEST_DIR / "non_existent.txt"

    # Ensure the file doesn't exist
    if non_existent_file.exists():
        non_existent_file.unlink()

    with pytest.raises(FileNotFoundError):
        await read_file(str(non_existent_file))


@pytest.mark.asyncio
@patch("src.server.list_files_util")
async def test_list_directory_directory_not_found(mock_list_files):
    """Test the list_directory tool with a non-existent directory."""
    # Mock list_files to raise FileNotFoundError
    mock_list_files.side_effect = FileNotFoundError("Directory not found")

    with pytest.raises(FileNotFoundError):
        await list_directory()


@pytest.mark.asyncio
@patch("src.server.list_files_util")
async def test_list_directory_with_gitignore(mock_list_files):
    """Test the list_directory tool with gitignore filtering."""
    # Mock list_files to return filtered files
    mock_list_files.return_value = [
        str(TEST_DIR / "test_normal.txt"),
        str(TEST_DIR / ".gitignore"),
    ]

    files = await list_directory()

    # Verify the function was called with gitignore=True
    mock_list_files.assert_called_once_with(".", use_gitignore=True)

    assert str(TEST_DIR / "test_normal.txt") in files
    assert str(TEST_DIR / ".gitignore") in files


@pytest.mark.asyncio
@patch("src.server.list_files_util")
async def test_list_directory_error_handling(mock_list_files):
    """Test error handling in the list_directory tool."""
    # Mock list_files to raise an exception
    mock_list_files.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        await list_directory()
