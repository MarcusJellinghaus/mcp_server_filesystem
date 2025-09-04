# Step 2: Implement Basic Move Functionality

## Objective
Implement basic file move/rename functionality using standard filesystem operations, without git integration yet. This establishes the foundation for the move operation.

## Prerequisites
- Step 1 completed (git_operations.py module exists)
- GitPython installed as a required dependency

## Test-Driven Development Approach
Write tests for basic move functionality, then implement the feature.

## Implementation Tasks

### 1. Create Test File for Move Operations
Create `tests/file_tools/test_move_operations.py`:

```python
"""Tests for file move/rename operations."""
import os
from pathlib import Path
import pytest
from unittest.mock import patch, Mock

from mcp_server_filesystem.file_tools.file_operations import move_file


class TestBasicMoveOperations:
    """Test basic file move and rename operations."""
    
    def test_move_file_same_directory(self, project_dir):
        """Test renaming a file in the same directory."""
        # Create source file
        source = project_dir / "test_file.txt"
        source.write_text("test content")
        
        # Move (rename) the file
        result = move_file(
            "test_file.txt",
            "renamed_file.txt",
            project_dir=project_dir
        )
        
        # Verify result
        assert result["success"] is True
        assert result["method"] == "filesystem"
        assert result["source"] == "test_file.txt"
        assert result["destination"] == "renamed_file.txt"
        
        # Verify file was moved
        assert not source.exists()
        dest = project_dir / "renamed_file.txt"
        assert dest.exists()
        assert dest.read_text() == "test content"
    
    def test_move_file_to_subdirectory(self, project_dir):
        """Test moving a file to a subdirectory."""
        # Create source file
        source = project_dir / "source.txt"
        source.write_text("content to move")
        
        # Create target directory
        subdir = project_dir / "subdir"
        subdir.mkdir()
        
        # Move file
        result = move_file(
            "source.txt",
            "subdir/moved.txt",
            project_dir=project_dir
        )
        
        assert result["success"] is True
        assert not source.exists()
        dest = project_dir / "subdir" / "moved.txt"
        assert dest.exists()
        assert dest.read_text() == "content to move"
    
    def test_move_file_create_parent_directory(self, project_dir):
        """Test moving a file to a non-existent directory (auto-creates parents)."""
        # Create source file
        source = project_dir / "file.txt"
        source.write_text("test data")
        
        # Move to non-existent directory (parent dirs created automatically)
        result = move_file(
            "file.txt",
            "new/path/to/file.txt",
            project_dir=project_dir
        )
        
        assert result["success"] is True
        assert not source.exists()
        dest = project_dir / "new" / "path" / "to" / "file.txt"
        assert dest.exists()
        assert dest.read_text() == "test data"
    
    # Test removed - parent directories are always created automatically
    
    def test_move_nonexistent_file_fails(self, project_dir):
        """Test that moving a non-existent file raises an error."""
        with pytest.raises(FileNotFoundError) as exc:
            move_file(
                "nonexistent.txt",
                "destination.txt",
                project_dir=project_dir
            )
        
        assert "does not exist" in str(exc.value)
    
    def test_move_file_outside_project_fails(self, project_dir):
        """Test that moving files outside project directory is prevented."""
        # Create source file
        source = project_dir / "source.txt"
        source.write_text("content")
        
        # Try to move outside project
        with pytest.raises(ValueError) as exc:
            move_file(
                "source.txt",
                "../outside.txt",
                project_dir=project_dir
            )
        
        assert "Security error" in str(exc.value)
        assert source.exists()  # Source should still exist
    
    def test_move_directory(self, project_dir):
        """Test moving a directory."""
        # Create source directory with files
        source_dir = project_dir / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("file 1")
        (source_dir / "file2.txt").write_text("file 2")
        
        # Move directory
        result = move_file(
            "source_dir",
            "moved_dir",
            project_dir=project_dir
        )
        
        assert result["success"] is True
        assert not source_dir.exists()
        dest_dir = project_dir / "moved_dir"
        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").read_text() == "file 1"
        assert (dest_dir / "file2.txt").read_text() == "file 2"
```

### 2. Add Move Function to file_operations.py
Add to `src/mcp_server_filesystem/file_tools/file_operations.py`:

```python
# Add these imports at the top
import shutil
from typing import Dict, Any
from mcp_server_filesystem.log_utils import log_function_call  # Use existing decorator

@log_function_call  # Automatic logging of parameters, timing, and exceptions
def move_file(
    source_path: str,
    destination_path: str,
    project_dir: Path
) -> Dict[str, Any]:
    """
    Move or rename a file or directory.
    
    Automatically creates parent directories if needed.
    Git integration will be added in Step 3.
    
    Args:
        source_path: Source file/directory path (relative to project_dir)
        destination_path: Destination path (relative to project_dir)
        project_dir: Project directory path
        
    Returns:
        Dict containing:
            - success: bool indicating if the move succeeded
            - method: 'git' or 'filesystem' indicating method used
            - source: normalized source path
            - destination: normalized destination path
            - message: optional status message
            
    Raises:
        FileNotFoundError: If source doesn't exist or parent dir doesn't exist
        ValueError: If paths are invalid or outside project directory
        PermissionError: If lacking permissions for the operation
    """
    # Validate inputs
    if not source_path or not isinstance(source_path, str):
        raise ValueError(f"Source path must be a non-empty string, got {type(source_path)}")
    
    if not destination_path or not isinstance(destination_path, str):
        raise ValueError(f"Destination path must be a non-empty string, got {type(destination_path)}")
    
    if project_dir is None:
        raise ValueError("Project directory cannot be None")
    
    # Normalize paths (this also validates they're within project_dir)
    src_abs, src_rel = normalize_path(source_path, project_dir)
    dest_abs, dest_rel = normalize_path(destination_path, project_dir)
    
    # Check if source exists
    if not src_abs.exists():
        raise FileNotFoundError(f"Source file '{source_path}' does not exist")
    
    # Check if destination already exists
    if dest_abs.exists():
        raise FileExistsError(f"Destination '{destination_path}' already exists")
    
    # Always create parent directories if needed
    dest_parent = dest_abs.parent
    if not dest_parent.exists():
        logger.info(f"Creating parent directory: {dest_parent.relative_to(project_dir)}")
        dest_parent.mkdir(parents=True, exist_ok=True)
    
    # For now, we'll implement only filesystem move
    # Git integration will be added in Step 3
    try:
        logger.info(f"Moving file: {src_rel} -> {dest_rel}")
        logger.debug(f"Moving {src_rel} to {dest_rel} using filesystem operations")
        
        # Use shutil.move for both files and directories
        shutil.move(str(src_abs), str(dest_abs))
        
        logger.info(f"Successfully moved: {src_rel} -> {dest_rel}")
        
        return {
            "success": True,
            "method": "filesystem",
            "source": src_rel,
            "destination": dest_rel,
            "message": "File moved using filesystem operations"
        }
        
    except PermissionError as e:
        logger.error(f"Permission denied moving {src_rel} to {dest_rel}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error moving {src_rel} to {dest_rel}: {e}")
        raise
```

### 3. Update __init__.py
Add to `src/mcp_server_filesystem/file_tools/__init__.py`:

```python
# Add move_file to imports
from mcp_server_filesystem.file_tools.file_operations import (
    # ... existing imports ...
    move_file,
)

# Update __all__ list
__all__ = [
    # ... existing exports ...
    "move_file",
]
```

## Verification Commands

```bash
# Run the move operation tests
pytest tests/file_tools/test_move_operations.py -v

# Run all file operation tests to ensure nothing broke
pytest tests/file_tools/test_file_operations.py -v

# Check test coverage
pytest tests/file_tools/test_move_operations.py --cov=mcp_server_filesystem.file_tools --cov-report=term-missing
```

## Success Criteria
- [ ] Basic file rename (same directory) works
- [ ] Moving files to different directories works
- [ ] Moving directories works
- [ ] Parent directories are created when create_parents=True
- [ ] Proper error when parent doesn't exist and create_parents=False
- [ ] Security validation prevents moves outside project directory
- [ ] All existing tests still pass
- [ ] Proper logging of operations

## Notes
- This step implements only filesystem operations (no git yet)
- Git integration will be added in Step 3
- Focus on robustness and error handling
- Maintain consistency with existing code patterns
