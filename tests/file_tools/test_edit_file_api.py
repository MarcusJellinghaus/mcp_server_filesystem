"""Tests for the edit_file MCP tool."""

import os
import sys
from pathlib import Path

import pytest

from src.server import edit_file, save_file, set_project_dir

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test constants
TEST_DIR = Path("test_file_tools")
TEST_FILE = TEST_DIR / "test_edit_api_file.txt"
TEST_CONTENT = """This is a test file for the edit_file API.
Line 2 with some content.
Line 3 with different content.
Line 4 to be edited.
Line 5 stays the same."""


@pytest.fixture(autouse=True)
def setup_test_file(project_dir):
    """Setup and teardown for each test."""
    # Setup: Ensure the test directory exists and create the test file
    test_dir_path = project_dir / TEST_DIR
    test_dir_path.mkdir(parents=True, exist_ok=True)

    # Set the project directory
    set_project_dir(project_dir)

    # Run the test
    yield

    # Teardown: Clean up the test file
    test_file_path = project_dir / TEST_FILE
    if test_file_path.exists():
        test_file_path.unlink()


@pytest.mark.asyncio
async def test_edit_file_exact_match(project_dir):
    """Test the edit_file tool with exact matching."""
    # First create the test file - use absolute path for reliability
    absolute_path = str(project_dir / TEST_FILE)
    save_file(str(TEST_FILE), TEST_CONTENT)

    # Define the edit operation
    edits = [
        {"old_text": "Line 4 to be edited.", "new_text": "Line 4 has been modified."}
    ]

    # Apply the edit - using absolute path here
    result = edit_file(absolute_path, edits)

    # Check success
    assert result["success"] is True

    # Check that a diff was created
    assert "diff" in result
    assert "+Line 4 has been modified." in result["diff"]

    # Verify the file was actually changed
    with open(project_dir / TEST_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 4 has been modified." in content
    assert "Line 4 to be edited." not in content


@pytest.mark.asyncio
async def test_edit_file_dry_run(project_dir):
    """Test the edit_file tool in dry run mode."""
    # First create the test file
    absolute_path = str(project_dir / TEST_FILE)
    save_file(str(TEST_FILE), TEST_CONTENT)

    # Define the edit operation
    edits = [
        {"old_text": "Line 4 to be edited.", "new_text": "Line 4 has been modified."}
    ]

    # Apply the edit in dry run mode
    result = edit_file(absolute_path, edits, dry_run=True)

    # Check success
    assert result["success"] is True
    assert result["dry_run"] is True

    # Check that a diff was created
    assert "diff" in result
    assert "+Line 4 has been modified." in result["diff"]

    # Verify the file was NOT actually changed
    with open(project_dir / TEST_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 4 to be edited." in content  # Original text should remain
    assert "Line 4 has been modified." not in content


@pytest.mark.asyncio
async def test_edit_file_multiple_edits(project_dir):
    """Test the edit_file tool with multiple edits."""
    # First create the test file
    absolute_path = str(project_dir / TEST_FILE)
    save_file(str(TEST_FILE), TEST_CONTENT)

    # Define multiple edit operations
    edits = [
        {
            "old_text": "Line 2 with some content.",
            "new_text": "Line 2 has been modified.",
        },
        {
            "old_text": "Line 4 to be edited.",
            "new_text": "Line 4 has also been modified.",
        },
    ]

    # Apply the edits
    result = edit_file(absolute_path, edits)

    # Check success
    assert result["success"] is True

    # Verify the file was changed with both edits
    with open(project_dir / TEST_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 2 has been modified." in content
    assert "Line 4 has also been modified." in content


@pytest.mark.asyncio
async def test_edit_file_error_handling(project_dir):
    """Test error handling in the edit_file tool."""
    # First create the test file
    absolute_path = str(project_dir / TEST_FILE)
    save_file(str(TEST_FILE), TEST_CONTENT)

    # Define an edit operation with text that doesn't exist
    edits = [
        {
            "old_text": "This text does not exist in the file.",
            "new_text": "This should not be applied.",
        }
    ]

    # The edit should fail
    result = edit_file(absolute_path, edits)

    # Check failure
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_edit_file_indentation(project_dir):
    """Test that the edit_file API handles indentation correctly."""
    # Create a test file with indentation
    indented_content = """def example_function():
    # This is indented with 4 spaces
    if condition:
        # This is indented with 8 spaces
        print("Indented text")
        for item in items:
            # This is indented with 12 spaces
            process(item)
"""

    test_file_path = str(TEST_DIR / "indentation_test.py")
    absolute_path = str(project_dir / TEST_DIR / "indentation_test.py")
    save_file(test_file_path, indented_content)

    # Define an edit that would normally lose indentation
    edits = [
        {
            "old_text": '    if condition:\n        # This is indented with 8 spaces\n        print("Indented text")',
            "new_text": '    if new_condition:\n        # Modified comment\n        print("Changed text")',
        }
    ]

    # Apply the edit with options parameter using snake_case notation
    options = {"preserve_indentation": True}
    result = edit_file(absolute_path, edits, options=options)

    # Check success
    assert result["success"] is True

    # Verify the file was modified with correctly preserved indentation
    with open(
        project_dir / TEST_DIR / "indentation_test.py", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    # The indentation should be preserved
    assert "    if new_condition:" in content
    assert "        # Modified comment" in content
    assert '        print("Changed text")' in content
