"""Tests for file operations functionality."""

import os
import shutil
from pathlib import Path

import pytest

# Import functions directly from the module
from src.file_tools.file_operations import delete_file, read_file, save_file
from tests.conftest import TEST_CONTENT, TEST_DIR, TEST_FILE


def test_save_file(project_dir):
    """Test writing to a file."""
    # Test writing to a file
    result = save_file(str(TEST_FILE), TEST_CONTENT, project_dir=project_dir)

    # Create path for verification
    abs_file_path = project_dir / TEST_FILE

    # Verify the file was written
    assert result is True
    assert abs_file_path.exists()

    # Verify the file content
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == TEST_CONTENT


def test_save_file_atomic_overwrite(project_dir):
    """Test atomically overwriting an existing file."""
    # Create absolute path for test file
    abs_file_path = project_dir / TEST_FILE

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
    result = save_file(str(TEST_FILE), new_content, project_dir=project_dir)

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


def test_save_file_security(project_dir):
    """Test security checks in save_file."""
    # Try to write a file outside the project directory
    with pytest.raises(ValueError) as excinfo:
        save_file(
            "../outside_project.txt",
            "This should not be written",
            project_dir=project_dir,
        )

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)


def test_read_file(project_dir):
    """Test reading from a file."""
    # Create an absolute path for test file creation
    abs_file_path = project_dir / TEST_FILE

    # Create a test file
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Test reading the file
    content = read_file(str(TEST_FILE), project_dir=project_dir)

    # Verify the content
    assert content == TEST_CONTENT


def test_read_file_not_found(project_dir):
    """Test reading a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent.txt"

    # Ensure the file doesn't exist
    abs_non_existent = project_dir / non_existent_file
    if abs_non_existent.exists():
        abs_non_existent.unlink()

    # Test reading a non-existent file
    with pytest.raises(FileNotFoundError):
        read_file(str(non_existent_file), project_dir=project_dir)


def test_read_file_security(project_dir):
    """Test security checks in read_file."""
    # Try to read a file outside the project directory
    with pytest.raises(ValueError) as excinfo:
        read_file("../outside_project.txt", project_dir=project_dir)

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)


def test_delete_file(project_dir):
    """Test deleting a file."""
    # Create a file to delete
    file_to_delete = TEST_DIR / "file_to_delete.txt"
    abs_file_path = project_dir / file_to_delete

    # Ensure the file exists
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write("This file will be deleted.")

    # Verify the file exists
    assert abs_file_path.exists()

    # Test deleting the file
    result = delete_file(str(file_to_delete), project_dir=project_dir)

    # Verify the file was deleted
    assert result is True
    assert not abs_file_path.exists()


def test_delete_file_not_found(project_dir):
    """Test deleting a file that doesn't exist."""
    non_existent_file = TEST_DIR / "non_existent_file.txt"

    # Ensure the file doesn't exist
    abs_non_existent = project_dir / non_existent_file
    if abs_non_existent.exists():
        abs_non_existent.unlink()

    # Test deleting a non-existent file
    with pytest.raises(FileNotFoundError):
        delete_file(str(non_existent_file), project_dir=project_dir)


def test_delete_file_is_directory(project_dir):
    """Test attempting to delete a directory."""
    # Create a directory
    dir_path = TEST_DIR / "test_directory"
    abs_dir_path = project_dir / dir_path

    # Ensure the directory exists
    abs_dir_path.mkdir(exist_ok=True)

    # Verify the directory exists
    assert abs_dir_path.exists()
    assert abs_dir_path.is_dir()

    # Test attempting to delete a directory
    with pytest.raises(IsADirectoryError):
        delete_file(str(dir_path), project_dir=project_dir)

    # Verify the directory still exists
    assert abs_dir_path.exists()

    # Clean up
    shutil.rmtree(abs_dir_path)


def test_delete_file_security(project_dir):
    """Test security checks in delete_file."""
    # Try to delete a file outside the project directory
    with pytest.raises(ValueError) as excinfo:
        delete_file("../outside_project.txt", project_dir=project_dir)

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)
