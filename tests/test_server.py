"""Tests for the MCP server API endpoints."""
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from src.models import ListFilesRequest, ReadFileRequest, WriteFileRequest
from src.server import app

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up the project directory for testing
os.environ["MCP_PROJECT_DIR"] = os.path.abspath(os.path.dirname(__file__))


# Create a test client
client = TestClient(app)

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


def test_write_file_endpoint():
    """Test the write_file endpoint."""
    request = WriteFileRequest(
        file_path=str(TEST_FILE),
        content=TEST_CONTENT
    )
    
    response = client.post("/write_file", json=request.model_dump())
    
    # Create absolute path for verification
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE
    
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert abs_file_path.exists()
    
    with open(abs_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_read_file_endpoint():
    """Test the read_file endpoint."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE
    
    # Create a test file
    with open(abs_file_path, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    request = ReadFileRequest(file_path=str(TEST_FILE))
    
    response = client.post("/read_file", json=request.model_dump())
    
    assert response.status_code == 200
    assert response.json() == {"content": TEST_CONTENT}


def test_list_files_endpoint():
    """Test the list_files endpoint."""
    # Create absolute path for test file
    abs_file_path = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_FILE
    
    # Create a test file
    with open(abs_file_path, 'w', encoding='utf-8') as f:
        f.write(TEST_CONTENT)
    
    request = ListFilesRequest(directory=str(TEST_DIR))
    
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
    assert TEST_FILE.name in files


def test_read_file_not_found():
    """Test the read_file endpoint with a non-existent file."""
    non_existent_file = TEST_DIR / "non_existent.txt"
    
    # Ensure the file doesn't exist
    if non_existent_file.exists():
        non_existent_file.unlink()
    
    request = ReadFileRequest(file_path=str(non_existent_file))
    
    response = client.post("/read_file", json=request.model_dump())
    
    assert response.status_code == 404
    response_data = response.json()
    # Check that response includes the error type
    assert "FileNotFoundError" in response_data["detail"]


def test_list_files_directory_not_found():
    """Test the list_files endpoint with a non-existent directory."""
    non_existent_dir = TEST_DIR / "non_existent_dir"
    
    # Ensure the directory doesn't exist
    if non_existent_dir.exists() and non_existent_dir.is_dir():
        non_existent_dir.rmdir()
    
    request = ListFilesRequest(directory=str(non_existent_dir))
    
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 404
    response_data = response.json()
    assert "FileNotFoundError" in response_data["detail"]


def test_list_files_endpoint_with_gitignore():
    """Test the list_files endpoint with gitignore filtering."""
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
    request = ListFilesRequest(directory=str(TEST_DIR))
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
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


def test_list_files_endpoint_without_gitignore():
    """Test the list_files endpoint without gitignore filtering."""
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
    request = ListFilesRequest(directory=str(TEST_DIR), use_gitignore=False)
    response = client.post("/list_files", json=request.model_dump())
    
    assert response.status_code == 200
    files = response.json()["files"]
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
