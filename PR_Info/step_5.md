# Step 5: Handle Edge Cases and Improve Robustness

## Objective
Handle edge cases such as case-sensitive renames on case-insensitive filesystems, existing destination handling, and improve error messages.

## Prerequisites
- Steps 1-4 completed
- Basic move functionality working with git integration

## Test-Driven Development Approach
Write tests for edge cases, then enhance the implementation to handle them.

## Implementation Tasks

### 1. Create Edge Case Tests
Create `tests/file_tools/test_move_edge_cases.py`:

```python
"""Tests for edge cases in move operations."""
import os
import platform
from pathlib import Path
import pytest
from unittest.mock import patch

from mcp_server_filesystem.file_tools.file_operations import move_file


class TestMoveEdgeCases:
    """Test edge cases and special scenarios in move operations."""
    
    def test_case_sensitive_rename_same_directory(self, project_dir):
        """Test renaming file with only case changes."""
        # Create file with lowercase name
        source = project_dir / "testfile.txt"
        source.write_text("content")
        
        # Rename with case change
        result = move_file(
            "testfile.txt",
            "TestFile.txt",
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        
        # Check that the file exists with new case
        # This is tricky on case-insensitive systems
        files = os.listdir(project_dir)
        if platform.system() in ['Windows', 'Darwin']:  # Case-insensitive
            # Check that at least one variant exists
            assert any(f.lower() == "testfile.txt" for f in files)
        else:  # Linux - case-sensitive
            assert "TestFile.txt" in files
            assert "testfile.txt" not in files
    
    def test_move_with_force_overwrite(self, project_dir):
        """Test move with force flag to overwrite existing destination."""
        # Create source and destination files
        source = project_dir / "source.txt"
        source.write_text("source content")
        
        dest = project_dir / "dest.txt"
        dest.write_text("will be overwritten")
        
        # Currently should fail without force
        with pytest.raises(FileExistsError):
            move_file(
                "source.txt",
                "dest.txt",
                project_dir=project_dir,
                use_git_if_available=False
            )
        
        # Both files should still exist
        assert source.exists()
        assert dest.exists()
    
    def test_move_empty_directory(self, project_dir):
        """Test moving an empty directory."""
        # Create empty directory
        empty_dir = project_dir / "empty_dir"
        empty_dir.mkdir()
        
        # Move empty directory
        result = move_file(
            "empty_dir",
            "moved_empty_dir",
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        assert not empty_dir.exists()
        moved_dir = project_dir / "moved_empty_dir"
        assert moved_dir.exists()
        assert moved_dir.is_dir()
        assert len(list(moved_dir.iterdir())) == 0
    
    def test_move_nested_directory_structure(self, project_dir):
        """Test moving complex nested directory structure."""
        # Create nested structure
        root = project_dir / "root_dir"
        root.mkdir()
        (root / "sub1").mkdir()
        (root / "sub1" / "file1.txt").write_text("file1")
        (root / "sub2").mkdir()
        (root / "sub2" / "deep").mkdir()
        (root / "sub2" / "deep" / "file2.txt").write_text("file2")
        
        # Move entire structure
        result = move_file(
            "root_dir",
            "moved_root",
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        assert not root.exists()
        
        # Verify structure preserved
        moved = project_dir / "moved_root"
        assert moved.exists()
        assert (moved / "sub1" / "file1.txt").read_text() == "file1"
        assert (moved / "sub2" / "deep" / "file2.txt").read_text() == "file2"
    
    def test_move_with_symlinks(self, project_dir):
        """Test moving files with symbolic links."""
        if platform.system() == 'Windows':
            pytest.skip("Symbolic link test skipped on Windows")
        
        # Create a file and a symlink to it
        real_file = project_dir / "real.txt"
        real_file.write_text("real content")
        
        symlink = project_dir / "link.txt"
        symlink.symlink_to(real_file)
        
        # Move the symlink
        result = move_file(
            "link.txt",
            "moved_link.txt",
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        moved_link = project_dir / "moved_link.txt"
        assert moved_link.exists()
        assert moved_link.is_symlink()
        # Symlink should still point to the same target
        assert moved_link.read_text() == "real content"
    
    def test_move_with_special_characters(self, project_dir):
        """Test moving files with special characters in names."""
        # Create file with special characters
        special_name = "file with spaces & special-chars!.txt"
        source = project_dir / special_name
        source.write_text("special content")
        
        # Move to another name with special characters
        new_name = "moved (file) with @special #chars.txt"
        result = move_file(
            special_name,
            new_name,
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        assert not source.exists()
        dest = project_dir / new_name
        assert dest.exists()
        assert dest.read_text() == "special content"
    
    def test_move_very_long_path(self, project_dir):
        """Test moving files with very long paths."""
        # Create deeply nested structure
        path = project_dir
        for i in range(10):
            path = path / f"level_{i}"
            path.mkdir(exist_ok=True)
        
        # Create file in deep directory
        deep_file = path / "deep_file.txt"
        deep_file.write_text("deep content")
        
        # Calculate relative path
        rel_source = str(deep_file.relative_to(project_dir))
        rel_dest = rel_source.replace("deep_file.txt", "moved_deep.txt")
        
        # Move the deeply nested file
        result = move_file(
            rel_source,
            rel_dest,
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        assert not deep_file.exists()
        assert (path / "moved_deep.txt").exists()
    
    def test_move_handles_unicode_names(self, project_dir):
        """Test moving files with unicode characters in names."""
        # Create file with unicode name
        unicode_name = "文件_файл_ملف.txt"
        source = project_dir / unicode_name
        source.write_text("unicode content", encoding='utf-8')
        
        # Move to another unicode name
        new_unicode = "移動_перемещен_منقول.txt"
        result = move_file(
            unicode_name,
            new_unicode,
            project_dir=project_dir,
            use_git_if_available=False
        )
        
        assert result["success"] is True
        assert not source.exists()
        dest = project_dir / new_unicode
        assert dest.exists()
        assert dest.read_text(encoding='utf-8') == "unicode content"
```

### 2. Enhance Move Function for Edge Cases
Update `move_file` in `src/mcp_server_filesystem/file_tools/file_operations.py`:

```python
@log_function_call  # Keep decorator for all edge case handling
def move_file(
    source_path: str,
    destination_path: str,
    project_dir: Path,
    create_parents: bool = True,
    use_git_if_available: bool = True
) -> Dict[str, Any]:
    """
    Move or rename a file or directory with enhanced edge case handling.
    
    [Previous docstring content...]
    """
    # [Previous validation code remains the same...]
    
    # Normalize paths (this also validates they're within project_dir)
    src_abs, src_rel = normalize_path(source_path, project_dir)
    dest_abs, dest_rel = normalize_path(destination_path, project_dir)
    
    # Check if source exists
    if not src_abs.exists():
        raise FileNotFoundError(f"Source file '{source_path}' does not exist")
    
    # Special handling for case-only renames on case-insensitive systems
    is_case_only_rename = (
        src_abs.parent == dest_abs.parent and
        src_abs.name.lower() == dest_abs.name.lower() and
        src_abs.name != dest_abs.name
    )
    
    if is_case_only_rename:
        logger.debug(f"Detected case-only rename: {src_abs.name} -> {dest_abs.name}")
    
    # Check if destination already exists (skip for case-only renames)
    if not is_case_only_rename and dest_abs.exists():
        raise FileExistsError(f"Destination '{destination_path}' already exists")
    
    # Create parent directories if needed
    dest_parent = dest_abs.parent
    if not dest_parent.exists():
        if create_parents:
            logger.info(f"Creating parent directory: {dest_parent.relative_to(project_dir)}")
            dest_parent.mkdir(parents=True, exist_ok=True)
        else:
            raise FileNotFoundError(
                f"Parent directory '{dest_parent.relative_to(project_dir)}' does not exist. "
                f"Set create_parents=True to create it automatically."
            )
    
    # Handle case-only renames specially on case-insensitive systems
    if is_case_only_rename and platform.system() in ['Windows', 'Darwin']:
        logger.debug(f"Performing case-only rename: {src_rel} -> {dest_rel}")
        return _handle_case_rename(src_abs, dest_abs, src_rel, dest_rel, project_dir, use_git_if_available)
    
    # [Rest of the function remains the same...]


@log_function_call  # Log this helper function too
def _handle_case_rename(
    src_abs: Path,
    dest_abs: Path,
    src_rel: str,
    dest_rel: str,
    project_dir: Path,
    use_git: bool
) -> Dict[str, Any]:
    """
    Handle case-only renames on case-insensitive filesystems.
    
    This requires a two-step rename through a temporary name.
    """
    logger.info(f"Handling case-sensitive rename: {src_rel} -> {dest_rel}")
    import tempfile
    import uuid
    
    # Generate temporary name
    temp_name = f"{src_abs.stem}_temp_{uuid.uuid4().hex[:8]}{src_abs.suffix}"
    temp_path = src_abs.parent / temp_name
    
    try:
        # Check if we should use git
        should_use_git = (
            use_git and
            is_git_repository(project_dir) and
            is_file_tracked(src_abs, project_dir)
        )
        
        if should_use_git:
            try:
                repo = Repo(project_dir, search_parent_directories=False)
                
                # Two-step git move
                git_src = src_rel.replace('\\', '/')
                git_temp = str(temp_path.relative_to(project_dir)).replace('\\', '/')
                git_dest = dest_rel.replace('\\', '/')
                
                repo.git.mv(git_src, git_temp)
                repo.git.mv(git_temp, git_dest)
                
                return {
                    "success": True,
                    "method": "git",
                    "source": src_rel,
                    "destination": dest_rel,
                    "message": "File renamed using git mv (case-sensitive rename)"
                }
                
            except Exception as e:
                logger.warning(f"Git case rename failed, falling back to filesystem: {e}")
                # Fall through to filesystem method
        
        # Filesystem two-step rename
        logger.debug(f"Two-step rename: {src_abs} -> {temp_path} -> {dest_abs}")
        shutil.move(str(src_abs), str(temp_path))
        shutil.move(str(temp_path), str(dest_abs))
        
        return {
            "success": True,
            "method": "filesystem",
            "source": src_rel,
            "destination": dest_rel,
            "message": "File renamed using filesystem operations (case-sensitive rename)"
        }
        
    except Exception as e:
        # Try to restore original if temp exists
        if temp_path.exists() and not src_abs.exists():
            try:
                shutil.move(str(temp_path), str(src_abs))
            except:
                pass
        
        logger.error(f"Case rename failed: {e}")
        raise
```

### 3. Add Platform Detection Import
Add at the top of `file_operations.py`:

```python
import platform
import uuid
```

## Verification Commands

```bash
# Run edge case tests
pytest tests/file_tools/test_move_edge_cases.py -v

# Run on different platforms if possible
# On Windows
python -m pytest tests/file_tools/test_move_edge_cases.py -v

# On macOS
python -m pytest tests/file_tools/test_move_edge_cases.py -v

# On Linux
python -m pytest tests/file_tools/test_move_edge_cases.py -v

# Run all move-related tests
pytest tests/file_tools/test_move*.py -v

# Check coverage for edge cases
pytest tests/file_tools/test_move*.py --cov=mcp_server_filesystem.file_tools.file_operations --cov-report=term-missing

# Test with special filesystem scenarios
# Create files with special characters and test manually
python -c "from pathlib import Path; Path('test file with spaces.txt').write_text('test')"
python -m mcp_server_filesystem.main --project-dir . --log-level DEBUG
```

## Success Criteria
- [ ] Case-sensitive renames work on all platforms
- [ ] Empty directories can be moved
- [ ] Complex nested structures are preserved
- [ ] Symbolic links are handled correctly (Unix/Linux)
- [ ] Special characters in filenames work
- [ ] Unicode filenames are supported
- [ ] Very long paths are handled
- [ ] Proper error recovery on failure
- [ ] Two-step rename for case changes works

## Notes
- Platform-specific behavior is properly handled
- Case-insensitive filesystems (Windows/macOS) need special handling
- Symbolic links may not work on all Windows configurations
- Unicode support depends on filesystem encoding
- Error recovery ensures no data loss on failure
