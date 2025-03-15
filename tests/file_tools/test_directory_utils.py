"""Tests for directory_utils module."""

import os
import shutil
from pathlib import Path

import pytest
from gitignore_parser import parse_gitignore

# Import directly from src using absolute imports
from src.file_tools.directory_utils import (
    _discover_files,
    _get_gitignore_matcher,
    filter_files_with_gitignore,
    list_files,
    fixed_parse_gitignore,
)
from src.file_tools.path_utils import get_project_dir
from tests.conftest import TEST_CONTENT, TEST_DIR, TEST_FILE


def create_test_directory_structure(base_dir: Path):
    """Helper function to create a consistent test directory structure."""
    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create test file structure
    (base_dir / "file1.txt").touch()
    (base_dir / "file2.log").touch()
    subdir = base_dir / "subdir"
    subdir.mkdir(parents=True)
    (subdir / "subfile1.txt").touch()
    (subdir / "subfile2.log").touch()
    nested_dir = subdir / "nested"
    nested_dir.mkdir(parents=True)
    (nested_dir / "nestedfile.txt").touch()
    return base_dir


def test_discover_files(tmp_path):
    """Test file discovery without filtering."""
    # Create test directory structure
    test_dir = create_test_directory_structure(tmp_path / "test_discover")

    # Use project directory for relative path calculation
    project_dir = get_project_dir()

    # Create a unique test project directory
    test_project_dir = project_dir / "tests" / "test_discover_temp"

    try:
        # Copy the test directory to within the project directory
        test_project_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(test_dir, test_project_dir, dirs_exist_ok=True)

        # Discover files using absolute path within project directory
        discovered = _discover_files(test_project_dir)

        # Verify file discovery
        assert len(discovered) == 5
        assert all(isinstance(path, str) for path in discovered)

    finally:
        # Clean up: remove the temporary test directory
        if test_project_dir.exists():
            shutil.rmtree(test_project_dir)


def test_gitignore_matcher(tmp_path):
    """Test creation of gitignore matcher."""
    # Create a test .gitignore file
    gitignore_path = tmp_path / ".gitignore"
    gitignore_content = """
    *.log
    build/
    temp/
    """
    gitignore_path.write_text(gitignore_content)

    # Create spec
    matcher = fixed_parse_gitignore(gitignore_path)

    # Validate matcher
    assert matcher is not None

    # Test matching
    assert matcher(str(tmp_path / "app.log"))
    assert matcher(str(tmp_path / "build"))
    assert matcher(str(tmp_path / "build/file.txt"))
    assert matcher(str(tmp_path / "temp/somefile.txt"))

    # These should not match
    assert not matcher(str(tmp_path / "app.txt"))
    assert not matcher(str(tmp_path / "logs"))


def test_list_files_with_gitignore(tmp_path):
    """Test listing files with a gitignore scenario."""
    # Create test directory
    test_dir = tmp_path / "test_gitignore"
    test_dir.mkdir(parents=True)

    # Create .gitignore
    gitignore_path = test_dir / ".gitignore"
    gitignore_path.write_text(
        """
    *.log
    build/
    temp/
    """
    )

    # Create test files and directories
    (test_dir / "file1.txt").touch()
    (test_dir / "file2.log").touch()

    build_dir = test_dir / "build"
    build_dir.mkdir()
    (build_dir / "build_file.txt").touch()

    temp_dir = test_dir / "temp"
    temp_dir.mkdir()
    (temp_dir / "temp_file.txt").touch()

    # Create a test directory within the project tests directory
    project_test_dir = get_project_dir() / "tests" / "temp_test_dir"

    try:
        project_test_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(test_dir, project_test_dir, dirs_exist_ok=True)

        # Use list_files on the project test directory
        discovered = list_files(str(project_test_dir), use_gitignore=True)
        discovered = [path.replace("\\", "/") for path in discovered]

        # Expected files
        expected_files = [
            "tests/temp_test_dir/file1.txt",
            "tests/temp_test_dir/.gitignore",
        ]

        # Verify
        assert set(discovered) == set(expected_files)

    finally:
        # Clean up: remove the temporary test directory
        if project_test_dir.exists():
            shutil.rmtree(project_test_dir)


def test_list_files_without_gitignore(tmp_path):
    """Test listing files without gitignore filtering."""
    # Create test directory
    test_dir = tmp_path / "test_no_gitignore"
    test_dir.mkdir(parents=True)

    # Create .gitignore
    gitignore_path = test_dir / ".gitignore"
    gitignore_path.write_text(
        """
    *.log
    build/
    temp/
    """
    )

    # Create test files and directories
    (test_dir / "file1.txt").touch()
    (test_dir / "file2.log").touch()

    build_dir = test_dir / "build"
    build_dir.mkdir()
    (build_dir / "build_file.txt").touch()

    temp_dir = test_dir / "temp"
    temp_dir.mkdir()
    (temp_dir / "temp_file.txt").touch()

    # Create a test directory within the project tests directory
    project_test_dir = get_project_dir() / "tests" / "temp_test_dir_no_gitignore"

    try:
        project_test_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(test_dir, project_test_dir, dirs_exist_ok=True)

        # Use list_files without gitignore filtering
        discovered = list_files(str(project_test_dir), use_gitignore=False)
        discovered = [path.replace("\\", "/") for path in discovered]

        # Expected files (all files)
        expected_files = [
            "tests/temp_test_dir_no_gitignore/file1.txt",
            "tests/temp_test_dir_no_gitignore/file2.log",
            "tests/temp_test_dir_no_gitignore/build/build_file.txt",
            "tests/temp_test_dir_no_gitignore/temp/temp_file.txt",
            "tests/temp_test_dir_no_gitignore/.gitignore",
        ]

        # Verify
        assert set(discovered) == set(expected_files)

    finally:
        # Clean up: remove the temporary test directory
        if project_test_dir.exists():
            shutil.rmtree(project_test_dir)


def test_filter_files_with_gitignore(tmp_path):
    """Test filtering files with gitignore patterns."""
    # Create a .gitignore file for testing
    gitignore_path = tmp_path / ".gitignore"
    gitignore_content = """
    *.log
    build/
    temp/
    """
    gitignore_path.write_text(gitignore_content)
    matcher = fixed_parse_gitignore(gitignore_path)
    
    # Test case 1: No gitignore matcher
    files = ["file1.txt", "file2.log", "build/file.txt"]
    filtered = filter_files_with_gitignore(files, None)
    assert filtered == files

    # Test case 2: With gitignore matcher
    project_dir = get_project_dir()
    files = [
        str(project_dir / "file1.txt"),
        str(project_dir / "file2.log"),
        str(project_dir / "build/file.txt"),
        str(project_dir / "temp/somefile.txt"),
        str(project_dir / "nested/file.log"),
    ]
    filtered = filter_files_with_gitignore(files, matcher)

    # Expected results (only paths not matching gitignore)
    expected = [str(project_dir / "file1.txt")]
    assert set(filtered) == set(expected)


def test_filter_files_with_negation_patterns(tmp_path):
    """Test filtering files with negation patterns."""
    # Create a .gitignore file with negation patterns
    gitignore_path = tmp_path / ".gitignore"
    gitignore_content = """
    *.log
    !important.log
    build/
    !build/keep/
    """
    gitignore_path.write_text(gitignore_content)
    matcher = fixed_parse_gitignore(gitignore_path)
    
    project_dir = get_project_dir()
    files = [
        str(project_dir / "debug.log"),
        str(project_dir / "important.log"),
        str(project_dir / "build/file.txt"),
        str(project_dir / "build/keep/important.txt"),
    ]
    
    filtered = filter_files_with_gitignore(files, matcher)
    
    # Expected results with negation patterns properly handled
    expected = [
        str(project_dir / "important.log"),
        str(project_dir / "build/keep/important.txt"),
    ]
    
    assert set(filtered) == set(expected)


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


def test_list_files_security():
    """Test security checks in list_files."""
    # Try to list files outside the project directory
    with pytest.raises(ValueError) as excinfo:
        list_files("../outside_project")

    # Verify the security error message
    assert "Security error" in str(excinfo.value)
    assert "outside the project directory" in str(excinfo.value)


def test_list_files_existing_functionality():
    """Verify that existing functionality remains the same."""
    # Create absolute paths for test operations
    abs_test_dir = Path(os.environ["MCP_PROJECT_DIR"]) / TEST_DIR
    abs_test_file = abs_test_dir / TEST_FILE.name

    # Create a test file
    abs_test_dir.mkdir(parents=True, exist_ok=True)
    with open(abs_test_file, "w", encoding="utf-8") as f:
        f.write(TEST_CONTENT)

    # Test listing files
    files = list_files(str(TEST_DIR))

    # Verify the file is in the list
    expected_file_path = str(TEST_DIR / TEST_FILE.name).replace("\\", "/")
    files = [path.replace("\\", "/") for path in files]
    assert expected_file_path in files