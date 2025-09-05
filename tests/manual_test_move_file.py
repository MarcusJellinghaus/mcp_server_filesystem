"""Manual test for move_file functionality.

This script tests the move_file feature end-to-end.
Run this after installation to verify the feature works.
"""

import os
import sys
import tempfile
from pathlib import Path

from mcp_server_filesystem.server import move_file, set_project_dir

# Add src to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))



def test_move_file_feature() -> bool:
    """Test the move_file feature with various scenarios."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        print(f"Testing in temporary directory: {project_dir}")

        # Set up the server
        set_project_dir(project_dir)

        # Test 1: Simple file move
        print("\nTest 1: Simple file move")
        source = project_dir / "test1.txt"
        source.write_text("Test content 1")

        result = move_file("test1.txt", "moved1.txt")
        assert result is True, "Move should succeed"
        assert not source.exists(), "Source should not exist"
        assert (project_dir / "moved1.txt").exists(), "Destination should exist"
        assert (project_dir / "moved1.txt").read_text() == "Test content 1"
        print("✓ Simple file move works")

        # Test 2: Move with directory creation
        print("\nTest 2: Move with automatic directory creation")
        source = project_dir / "test2.txt"
        source.write_text("Test content 2")

        result = move_file("test2.txt", "new_dir/sub_dir/moved2.txt")
        assert result is True, "Move should succeed"
        assert not source.exists(), "Source should not exist"
        assert (project_dir / "new_dir/sub_dir/moved2.txt").exists()
        print("✓ Move with directory creation works")

        # Test 3: Directory move
        print("\nTest 3: Directory move")
        dir_source = project_dir / "test_dir"
        dir_source.mkdir()
        (dir_source / "file.txt").write_text("Dir content")

        result = move_file("test_dir", "renamed_dir")
        assert result is True, "Move should succeed"
        assert not dir_source.exists(), "Source dir should not exist"
        assert (project_dir / "renamed_dir").exists()
        assert (project_dir / "renamed_dir/file.txt").read_text() == "Dir content"
        print("✓ Directory move works")

        # Test 4: Error handling - file not found
        print("\nTest 4: Error handling - file not found")
        try:
            move_file("nonexistent.txt", "dest.txt")
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError as e:
            assert str(e) == "File not found"
            print("✓ File not found error handled correctly")

        # Test 5: Error handling - destination exists
        print("\nTest 5: Error handling - destination exists")
        source = project_dir / "test5.txt"
        dest = project_dir / "existing5.txt"
        source.write_text("Source")
        dest.write_text("Existing")

        try:
            move_file("test5.txt", "existing5.txt")
            assert False, "Should raise FileExistsError"
        except FileExistsError as e:
            assert str(e) == "Destination already exists"
            print("✓ Destination exists error handled correctly")

        print("\n✅ All tests passed! The move_file feature is working correctly.")
        return True


if __name__ == "__main__":
    try:
        test_move_file_feature()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
