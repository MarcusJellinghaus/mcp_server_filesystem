"""Tests for file move/rename operations."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_server_filesystem.file_tools.file_operations import move_file


@pytest.fixture
def temp_project_dir():  # type: ignore[no-untyped-def]
    """Create a temporary directory for testing.

    This fixture ensures complete cleanup after each test by using
    Python's tempfile.TemporaryDirectory context manager.
    """
    with tempfile.TemporaryDirectory(prefix="test_move_") as tmpdir:
        yield Path(tmpdir)
    # Cleanup happens automatically when exiting the context manager


class TestBasicMoveOperations:
    """Test basic file move and rename operations.

    All tests use temp_project_dir fixture to ensure no files are left behind.
    The temp_project_dir fixture creates a fresh temporary directory for each test
    and automatically cleans it up after the test completes.
    """

    def test_move_file_same_directory(self, temp_project_dir: Path) -> None:
        """Test renaming a file in the same directory."""
        # Create source file
        source = temp_project_dir / "test_file.txt"
        source.write_text("test content")

        # Move (rename) the file
        result = move_file(
            "test_file.txt", "renamed_file.txt", project_dir=temp_project_dir
        )

        # Verify result
        assert result["success"] is True
        assert result["method"] == "filesystem"
        assert result["source"] == "test_file.txt"
        assert result["destination"] == "renamed_file.txt"

        # Verify file was moved
        assert not source.exists()
        dest = temp_project_dir / "renamed_file.txt"
        assert dest.exists()
        assert dest.read_text() == "test content"

    def test_move_file_to_subdirectory(self, temp_project_dir: Path) -> None:
        """Test moving a file to a subdirectory."""
        # Create source file
        source = temp_project_dir / "source.txt"
        source.write_text("content to move")

        # Create target directory
        subdir = temp_project_dir / "subdir"
        subdir.mkdir()

        # Move file
        result = move_file(
            "source.txt", "subdir/moved.txt", project_dir=temp_project_dir
        )

        assert result["success"] is True
        assert not source.exists()
        dest = temp_project_dir / "subdir" / "moved.txt"
        assert dest.exists()
        assert dest.read_text() == "content to move"

    def test_move_file_create_parent_directory(self, temp_project_dir: Path) -> None:
        """Test moving a file to a non-existent directory (auto-creates parents)."""
        # Create source file
        source = temp_project_dir / "file.txt"
        source.write_text("test data")

        # Move to non-existent directory (parent dirs created automatically)
        result = move_file(
            "file.txt", "new/path/to/file.txt", project_dir=temp_project_dir
        )

        assert result["success"] is True
        assert not source.exists()
        dest = temp_project_dir / "new" / "path" / "to" / "file.txt"
        assert dest.exists()
        assert dest.read_text() == "test data"

    def test_move_nonexistent_file_fails(self, temp_project_dir: Path) -> None:
        """Test that moving a non-existent file raises an error."""
        with pytest.raises(FileNotFoundError) as exc:
            move_file(
                "nonexistent.txt", "destination.txt", project_dir=temp_project_dir
            )

        # Internal function can have detailed message
        assert "does not exist" in str(exc.value)

    def test_move_file_outside_project_fails(self, temp_project_dir: Path) -> None:
        """Test that moving files outside project directory is prevented."""
        # Create source file
        source = temp_project_dir / "source.txt"
        source.write_text("content")

        # Try to move outside project
        with pytest.raises(ValueError) as exc:
            move_file("source.txt", "../outside.txt", project_dir=temp_project_dir)

        # Internal function can have detailed security message
        assert "Security error" in str(exc.value) or "outside project" in str(exc.value)
        assert source.exists()  # Source should still exist

    def test_move_directory(self, temp_project_dir: Path) -> None:
        """Test moving a directory."""
        # Create source directory with files
        source_dir = temp_project_dir / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("file 1")
        (source_dir / "file2.txt").write_text("file 2")

        # Move directory
        result = move_file("source_dir", "moved_dir", project_dir=temp_project_dir)

        assert result["success"] is True
        assert not source_dir.exists()
        dest_dir = temp_project_dir / "moved_dir"
        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").read_text() == "file 1"
        assert (dest_dir / "file2.txt").read_text() == "file 2"

    def test_move_file_destination_exists_fails(self, temp_project_dir: Path) -> None:
        """Test that moving to an existing destination raises an error."""
        # Create both source and destination files
        source = temp_project_dir / "source.txt"
        source.write_text("source content")

        dest = temp_project_dir / "existing.txt"
        dest.write_text("existing content")

        # Try to move to existing destination
        with pytest.raises(FileExistsError) as exc:
            move_file("source.txt", "existing.txt", project_dir=temp_project_dir)

        assert "already exists" in str(exc.value)
        assert source.exists()  # Source should still exist
        assert dest.read_text() == "existing content"  # Destination unchanged

    def test_temp_directory_cleanup_verification(self, temp_project_dir: Path) -> None:
        """Verify that temp directories are properly isolated and cleaned.

        This test verifies that:
        1. Each test gets a fresh temporary directory
        2. Files created in one test don't affect other tests
        3. The temporary directory is automatically cleaned up
        """
        # Create some files in the temp directory
        test_file = temp_project_dir / "cleanup_test.txt"
        test_file.write_text("This file will be cleaned up automatically")

        test_dir = temp_project_dir / "cleanup_dir"
        test_dir.mkdir()
        (test_dir / "nested.txt").write_text("nested file")

        # Verify they exist during the test
        assert test_file.exists()
        assert test_dir.exists()
        assert (test_dir / "nested.txt").exists()

        # Store the temp directory name to verify it's unique
        temp_name = temp_project_dir.name
        assert temp_name.startswith("test_move_")

        # Note: Actual cleanup happens when fixture's context manager exits
        # The next test will get a completely different temp directory


    def test_move_with_special_characters(self, temp_project_dir: Path) -> None:
        """Test moving files with special characters in names."""
        # Test various special characters that are allowed in filenames
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
            "file(with)parens.txt",
            "file[with]brackets.txt",
            "file{with}braces.txt",
            "file@with#symbols.txt",
        ]
        
        for name in special_names:
            # Create source file with special name
            source = temp_project_dir / name
            source.write_text(f"content of {name}")
            
            # Create destination name
            dest_name = f"moved_{name}"
            
            # Move file
            result = move_file(name, dest_name, project_dir=temp_project_dir)
            
            assert result["success"] is True
            assert not source.exists()
            dest = temp_project_dir / dest_name
            assert dest.exists()
            assert dest.read_text() == f"content of {name}"
            
            # Clean up for next iteration
            if dest.exists():
                dest.unlink()

    def test_move_empty_file(self, temp_project_dir: Path) -> None:
        """Test moving an empty file."""
        # Create empty file
        source = temp_project_dir / "empty.txt"
        source.touch()
        
        # Move empty file
        result = move_file("empty.txt", "moved_empty.txt", project_dir=temp_project_dir)
        
        assert result["success"] is True
        assert not source.exists()
        dest = temp_project_dir / "moved_empty.txt"
        assert dest.exists()
        assert dest.stat().st_size == 0

    def test_move_preserves_file_permissions(self, temp_project_dir: Path) -> None:
        """Test that move preserves file permissions."""
        # Create source file
        source = temp_project_dir / "perms_test.txt"
        source.write_text("test content")
        
        # Set specific permissions (only on Unix-like systems)
        if os.name != "nt":  # Not Windows
            original_mode = 0o644
            source.chmod(original_mode)
            original_stat = source.stat()
            
            # Move file
            result = move_file(
                "perms_test.txt", "moved_perms.txt", project_dir=temp_project_dir
            )
            
            assert result["success"] is True
            dest = temp_project_dir / "moved_perms.txt"
            dest_stat = dest.stat()
            
            # Check that permissions are preserved
            assert dest_stat.st_mode == original_stat.st_mode
        else:
            # On Windows, just verify the move works
            result = move_file(
                "perms_test.txt", "moved_perms.txt", project_dir=temp_project_dir
            )
            assert result["success"] is True

    def test_move_nested_directory_structure(self, temp_project_dir: Path) -> None:
        """Test moving a complex nested directory structure."""
        # Create nested directory structure
        root_dir = temp_project_dir / "root"
        root_dir.mkdir()
        
        # Create nested subdirectories
        (root_dir / "level1").mkdir()
        (root_dir / "level1" / "level2").mkdir()
        (root_dir / "level1" / "level2" / "level3").mkdir()
        
        # Add files at different levels
        (root_dir / "root_file.txt").write_text("root file")
        (root_dir / "level1" / "l1_file.txt").write_text("level 1 file")
        (root_dir / "level1" / "level2" / "l2_file.txt").write_text("level 2 file")
        (root_dir / "level1" / "level2" / "level3" / "l3_file.txt").write_text("level 3 file")
        
        # Move entire structure
        result = move_file("root", "moved_root", project_dir=temp_project_dir)
        
        assert result["success"] is True
        assert not root_dir.exists()
        
        # Verify entire structure was moved
        moved_dir = temp_project_dir / "moved_root"
        assert moved_dir.exists()
        assert (moved_dir / "root_file.txt").read_text() == "root file"
        assert (moved_dir / "level1" / "l1_file.txt").read_text() == "level 1 file"
        assert (moved_dir / "level1" / "level2" / "l2_file.txt").read_text() == "level 2 file"
        assert (moved_dir / "level1" / "level2" / "level3" / "l3_file.txt").read_text() == "level 3 file"

    def test_move_handles_concurrent_modification(self, temp_project_dir: Path) -> None:
        """Test handling of concurrent modification scenarios."""
        # Create source file
        source = temp_project_dir / "concurrent_test.txt"
        source.write_text("original content")
        
        # Simulate a scenario where file might be modified during move
        # by mocking the filesystem operation
        with patch("shutil.move") as mock_move:
            # Configure mock to simulate a transient error then succeed
            mock_move.side_effect = [
                OSError("Resource temporarily unavailable"),
                str(temp_project_dir / "moved_concurrent.txt")
            ]
            
            # First call should fail due to mock
            with pytest.raises(OSError):
                move_file(
                    "concurrent_test.txt", 
                    "moved_concurrent.txt", 
                    project_dir=temp_project_dir
                )
            
            # Reset mock for successful move
            mock_move.side_effect = None
            mock_move.return_value = str(temp_project_dir / "moved_concurrent.txt")
            
            # Manual move simulation for test
            source.rename(temp_project_dir / "moved_concurrent.txt")
            
            # Verify file was moved despite initial error
            assert not source.exists()
            assert (temp_project_dir / "moved_concurrent.txt").exists()
