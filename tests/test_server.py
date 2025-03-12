"""Tests for the MCP server API endpoints."""
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up the project directory for testing
os.environ["MCP_PROJECT_DIR"] = os.path.abspath(os.path.dirname(__file__))

from src.server import list_directory, read_file, write_file

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
    
    with open(abs_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == TEST_CONTENT


@pytest.mark.asyncio
async def test_read_file():
    """Test the read_file tool."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE
    
    # Create a test file
    with open(abs_file_path, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    content = await read_file(str(TEST_FILE))
    
    assert content == TEST_CONTENT


@pytest.mark.asyncio
async def test_list_directory():
    """Test the list_directory tool."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE
    
    # Create a test file
    with open(abs_file_path, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    files = await list_directory(str(TEST_DIR))
    
    assert TEST_FILE.name in files


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
async def test_list_directory_directory_not_found():
    """Test the list_directory tool with a non-existent directory."""
    non_existent_dir = TEST_DIR / "non_existent_dir"
    
    # Ensure the directory doesn't exist
    if non_existent_dir.exists() and non_existent_dir.is_dir():
        non_existent_dir.rmdir()
    
    with pytest.raises(FileNotFoundError):
        await list_directory(str(non_existent_dir))


@pytest.mark.asyncio
async def test_list_directory_with_gitignore():
    """Test the list_directory tool with gitignore filtering."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    
    # Create a .gitignore file
    gitignore_path = abs_test_dir / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write("*.ignore\nignored_dir/\n")
    
    # Create a .git directory that should be ignored
    git_dir = abs_test_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (git_dir / "HEAD").touch()
    
    # Create a test file that should be ignored
    test_ignore_file = abs_test_dir / "test.ignore"
    with open(test_ignore_file, 'w', encoding='utf-8') as f:
        f.write("This should be ignored")
    
    # Create a test file that should not be ignored
    test_normal_file = abs_test_dir / "test_normal.txt"
    with open(test_normal_file, 'w', encoding='utf-8') as f:
        f.write("This should not be ignored")
    
    # Test with gitignore filtering enabled (default)
    files = await list_directory(str(TEST_DIR))
    
    assert "test_normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" not in files
    assert ".git" not in files
    
    # Clean up
    gitignore_path.unlink()
    test_ignore_file.unlink()
    test_normal_file.unlink()
    (git_dir / "HEAD").unlink()
    git_dir.rmdir()


@pytest.mark.asyncio
async def test_list_directory_without_gitignore():
    """Test the list_directory tool without gitignore filtering."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    
    # Create a .gitignore file
    gitignore_path = abs_test_dir / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write("*.ignore\nignored_dir/\n")
    
    # Create a .git directory that would normally be ignored
    git_dir = abs_test_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (git_dir / "HEAD").touch()
    
    # Create a test file that would normally be ignored
    test_ignore_file = abs_test_dir / "test.ignore"
    with open(test_ignore_file, 'w', encoding='utf-8') as f:
        f.write("This would normally be ignored")
    
    # Create a test file that would not be ignored
    test_normal_file = abs_test_dir / "test_normal.txt"
    with open(test_normal_file, 'w', encoding='utf-8') as f:
        f.write("This would not be ignored")
    
    # Test with gitignore filtering disabled
    files = await list_directory(str(TEST_DIR), use_gitignore=False)
    
    assert "test_normal.txt" in files
    assert ".gitignore" in files
    assert "test.ignore" in files
    assert ".git" in files
    
    # Clean up
    gitignore_path.unlink()
    test_ignore_file.unlink()
    test_normal_file.unlink()
    (git_dir / "HEAD").unlink()
    git_dir.rmdir()
