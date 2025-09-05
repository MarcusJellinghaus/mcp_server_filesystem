#!/usr/bin/env python
"""Test script to verify move_file works through the MCP server directly.

This script can be run after installation to verify the feature integration.
Run: python tests/integration_test_move.py
"""

import sys
import tempfile
from pathlib import Path


def test_mcp_server_move_file() -> bool:
    """Test move_file through the actual MCP server command."""

    print("Testing move_file functionality through MCP server...")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        print(f"Test directory: {test_dir}")

        # Create test files
        source_file = test_dir / "test_source.txt"
        source_file.write_text("Test content for move operation")

        print(f"Created test file: {source_file}")

        # Test 1: Simple rename
        print("\n1. Testing simple file rename...")
        dest_file = test_dir / "test_renamed.txt"

        # Build command to run server (simplified test)
        # Note: In real usage, this would be through MCP protocol
        # Here we're just verifying the functions are accessible

        # Import and test directly
        from mcp_server_filesystem.server import move_file, set_project_dir

        # Set up server
        set_project_dir(test_dir)

        # Test move operation
        result = move_file("test_source.txt", "test_renamed.txt")

        if result:
            print("✓ File rename successful")
            assert not source_file.exists(), "Source should be removed"
            assert dest_file.exists(), "Destination should exist"
            assert dest_file.read_text() == "Test content for move operation"
        else:
            print("✗ File rename failed")
            return False

        # Test 2: Move to subdirectory
        print("\n2. Testing move to subdirectory...")
        source_file2 = test_dir / "test_source2.txt"
        source_file2.write_text("Another test file")

        subdir = test_dir / "subdir"

        result = move_file("test_source2.txt", "subdir/moved.txt")

        if result:
            print("✓ Move to subdirectory successful")
            assert not source_file2.exists()
            assert (subdir / "moved.txt").exists()
            assert (subdir / "moved.txt").read_text() == "Another test file"
        else:
            print("✗ Move to subdirectory failed")
            return False

        # Test 3: Error handling
        print("\n3. Testing error handling...")
        try:
            move_file("nonexistent.txt", "dest.txt")
            print("✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError as e:
            if str(e) == "File not found":
                print("✓ Error handling works correctly")
            else:
                print(f"✗ Unexpected error message: {e}")
                return False

        print("\n✅ All MCP server move_file tests passed!")
        return True


if __name__ == "__main__":
    try:
        success = test_mcp_server_move_file()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
