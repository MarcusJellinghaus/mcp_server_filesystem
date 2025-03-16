"""Tests for the edit_file MCP tool."""

import os
import sys
from pathlib import Path

import pytest

from src.server import edit_file, save_file, set_project_dir

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test constants
TEST_DIR = Path("testdata/test_file_tools")
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
    await save_file(str(TEST_FILE), TEST_CONTENT)

    # Define the edit operation
    edits = [
        {"oldText": "Line 4 to be edited.", "newText": "Line 4 has been modified."}
    ]

    # Apply the edit - using absolute path here
    result = await edit_file(absolute_path, edits)

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
    await save_file(str(TEST_FILE), TEST_CONTENT)

    # Define the edit operation
    edits = [
        {"oldText": "Line 4 to be edited.", "newText": "Line 4 has been modified."}
    ]

    # Apply the edit in dry run mode
    result = await edit_file(absolute_path, edits, dry_run=True)

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
async def test_edit_file_fuzzy_match(project_dir):
    """Test the edit_file tool with fuzzy matching."""
    # First create the test file
    absolute_path = str(project_dir / TEST_FILE)
    await save_file(str(TEST_FILE), TEST_CONTENT)

    # Define the edit operation with slightly different text
    edits = [
        {
            "oldText": "Line 2 with content.",  # Slightly different from actual text
            "newText": "Line 2 has been modified with fuzzy matching.",
        }
    ]

    # Apply the edit with fuzzy matching enabled
    result = await edit_file(absolute_path, edits, options={"partialMatch": True})

    # Check success
    assert result["success"] is True

    # Verify the file was changed
    with open(project_dir / TEST_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Line 2 has been modified with fuzzy matching." in content


@pytest.mark.asyncio
async def test_edit_file_multiple_edits(project_dir):
    """Test the edit_file tool with multiple edits."""
    # First create the test file
    absolute_path = str(project_dir / TEST_FILE)
    await save_file(str(TEST_FILE), TEST_CONTENT)

    # Define multiple edit operations
    edits = [
        {
            "oldText": "Line 2 with some content.",
            "newText": "Line 2 has been modified.",
        },
        {
            "oldText": "Line 4 to be edited.",
            "newText": "Line 4 has also been modified.",
        },
    ]

    # Apply the edits
    result = await edit_file(absolute_path, edits)

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
    await save_file(str(TEST_FILE), TEST_CONTENT)

    # Define an edit operation with text that doesn't exist
    edits = [
        {
            "oldText": "This text does not exist in the file.",
            "newText": "This should not be applied.",
        }
    ]

    # The edit should fail
    result = await edit_file(
        absolute_path, edits, options={"partialMatch": False}  # Disable fuzzy matching
    )

    # Check failure
    assert result["success"] is False
    assert "error" in result
