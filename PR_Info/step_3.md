# Step 3: Integrate Git Support for Tracked Files

## Objective
Enhance the move functionality to use `git mv` for git-tracked files, preserving version history while maintaining fallback to filesystem operations.

## Prerequisites
- Step 1 completed (git detection functions)
- Step 2 completed (basic move functionality)
- GitPython installed (optional, for full functionality)

## Test-Driven Development Approach
Write tests for git integration, then enhance the move function to support git operations.

## Implementation Tasks

### 1. Create Tests for Git Integration
Create `tests/file_tools/test_move_git_integration.py`:

```python
"""Tests for git integration in move operations."""
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

from mcp_server_filesystem.file_tools.file_operations import move_file
from mcp_server_filesystem.file_tools.git_operations import HAS_GITPYTHON


class TestGitMoveIntegration:
    """Test git integration in move operations."""
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_move_tracked_file_uses_git(self, tmp_path):
        """Test that tracked files are moved using git mv."""
        from git import Repo
        
        # Create a git repository
        repo = Repo.init(tmp_path)
        
        # Create and commit a file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("tracked content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Move the tracked file
        result = move_file(
            "tracked.txt",
            "moved_tracked.txt",
            project_dir=tmp_path,
            use_git_if_available=True
        )
        
        # Verify git was used
        assert result["success"] is True
        assert result["method"] == "git"
        assert "git mv" in result["message"].lower()
        
        # Verify file was moved
        assert not tracked_file.exists()
        moved_file = tmp_path / "moved_tracked.txt"
        assert moved_file.exists()
        assert moved_file.read_text() == "tracked content"
        
        # Verify git status shows the rename
        status = repo.git.status("--short")
        assert "R" in status  # R indicates renamed
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_move_untracked_file_uses_filesystem(self, tmp_path):
        """Test that untracked files use filesystem operations even in git repo."""
        from git import Repo
        
        # Create a git repository
        Repo.init(tmp_path)
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked content")
        
        # Move the untracked file
        result = move_file(
            "untracked.txt",
            "moved_untracked.txt",
            project_dir=tmp_path,
            use_git_if_available=True
        )
        
        # Verify filesystem was used
        assert result["success"] is True
        assert result["method"] == "filesystem"
        
        # Verify file was moved
        assert not untracked_file.exists()
        moved_file = tmp_path / "moved_untracked.txt"
        assert moved_file.exists()
    
    def test_move_with_git_disabled(self, tmp_path):
        """Test that git can be explicitly disabled."""
        # Mock git detection to return True
        with patch('mcp_server_filesystem.file_tools.file_operations.is_git_repository') as mock_is_repo:
            with patch('mcp_server_filesystem.file_tools.file_operations.is_file_tracked') as mock_is_tracked:
                mock_is_repo.return_value = True
                mock_is_tracked.return_value = True
                
                # Create a file
                source = tmp_path / "file.txt"
                source.write_text("content")
                
                # Move with git disabled
                result = move_file(
                    "file.txt",
                    "moved.txt",
                    project_dir=tmp_path,
                    use_git_if_available=False  # Explicitly disable git
                )
                
                # Verify filesystem was used despite git being available
                assert result["method"] == "filesystem"
                mock_is_repo.assert_not_called()
                mock_is_tracked.assert_not_called()
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_git_move_fallback_on_error(self, tmp_path):
        """Test fallback to filesystem when git mv fails."""
        from git import Repo
        
        # Create a git repository
        repo = Repo.init(tmp_path)
        
        # Create and commit a file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Mock git.mv to raise an error
        with patch.object(repo.git, 'mv', side_effect=Exception("Git error")):
            # Temporarily replace the repo in our function
            with patch('mcp_server_filesystem.file_tools.file_operations.Repo') as MockRepo:
                MockRepo.return_value = repo
                
                result = move_file(
                    "tracked.txt",
                    "moved.txt",
                    project_dir=tmp_path,
                    use_git_if_available=True
                )
                
                # Should fall back to filesystem
                assert result["success"] is True
                assert result["method"] == "filesystem"
                assert "fallback" in result["message"].lower()
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_move_tracked_file_to_new_directory(self, tmp_path):
        """Test moving a tracked file to a new directory with git."""
        from git import Repo
        
        # Create a git repository
        repo = Repo.init(tmp_path)
        
        # Create and commit a file
        tracked_file = tmp_path / "original.txt"
        tracked_file.write_text("content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Move to new directory
        result = move_file(
            "original.txt",
            "newdir/moved.txt",
            project_dir=tmp_path,
            create_parents=True,
            use_git_if_available=True
        )
        
        assert result["success"] is True
        assert result["method"] == "git"
        
        # Verify file was moved
        assert not tracked_file.exists()
        moved_file = tmp_path / "newdir" / "moved.txt"
        assert moved_file.exists()
        assert moved_file.read_text() == "content"
```

### 2. Enhanced Move Function with Git Support
Update the `move_file` function in `src/mcp_server_filesystem/file_tools/file_operations.py`:

```python
# Add GitPython imports at the top (after the existing imports)
try:
    from git import Repo
    from git.exc import GitCommandError
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False
    GitCommandError = Exception  # Dummy for type checking

def move_file(
    source_path: str,
    destination_path: str,
    project_dir: Path,
    create_parents: bool = True,
    use_git_if_available: bool = True
) -> Dict[str, Any]:
    """
    Move or rename a file or directory.
    
    This function will use git mv if the file is tracked by git,
    otherwise it will use standard filesystem operations.
    
    Args:
        source_path: Source file/directory path (relative to project_dir)
        destination_path: Destination path (relative to project_dir)
        project_dir: Project directory path
        create_parents: Whether to create parent directories if they don't exist
        use_git_if_available: Whether to use git mv for tracked files
        
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
    
    # Determine if we should use git
    should_use_git = False
    if use_git_if_available and HAS_GITPYTHON:
        if is_git_repository(project_dir):
            # For directories, check if any file inside is tracked
            if src_abs.is_dir():
                # Check if any file in the directory is tracked
                for file_path in src_abs.rglob('*'):
                    if file_path.is_file() and is_file_tracked(file_path, project_dir):
                        should_use_git = True
                        break
            else:
                # For files, check if the file itself is tracked
                should_use_git = is_file_tracked(src_abs, project_dir)
    
    # Try git move if applicable
    if should_use_git:
        try:
            logger.debug(f"Moving {src_rel} to {dest_rel} using git mv")
            
            repo = Repo(project_dir, search_parent_directories=False)
            
            # Convert paths to posix format for git (even on Windows)
            git_src = src_rel.replace('\\', '/')
            git_dest = dest_rel.replace('\\', '/')
            
            # Execute git mv
            repo.git.mv(git_src, git_dest)
            
            logger.info(f"Successfully moved using git: {src_rel} -> {dest_rel}")
            
            return {
                "success": True,
                "method": "git",
                "source": src_rel,
                "destination": dest_rel,
                "message": "File moved using git mv (preserving history)"
            }
            
        except (GitCommandError, Exception) as e:
            logger.warning(f"Git move failed, falling back to filesystem: {e}")
            # Fall through to filesystem move
            should_use_git = False
    
    # Use filesystem operations (either as primary method or fallback)
    try:
        logger.debug(f"Moving {src_rel} to {dest_rel} using filesystem operations")
        
        # Use shutil.move for both files and directories
        shutil.move(str(src_abs), str(dest_abs))
        
        message = "File moved using filesystem operations"
        if should_use_git:
            message += " (fallback from git)"
        
        logger.info(f"Successfully moved: {src_rel} -> {dest_rel}")
        
        return {
            "success": True,
            "method": "filesystem",
            "source": src_rel,
            "destination": dest_rel,
            "message": message
        }
        
    except PermissionError as e:
        logger.error(f"Permission denied moving {src_rel} to {dest_rel}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error moving {src_rel} to {dest_rel}: {e}")
        raise
```

## Verification Commands

```bash
# Install GitPython for testing
pip install GitPython

# Run git integration tests
pytest tests/file_tools/test_move_git_integration.py -v

# Run all move tests
pytest tests/file_tools/test_move_operations.py tests/file_tools/test_move_git_integration.py -v

# Test without GitPython
pip uninstall GitPython
pytest tests/file_tools/test_move_operations.py -v

# Reinstall GitPython
pip install GitPython

# Check coverage
pytest tests/file_tools/ --cov=mcp_server_filesystem.file_tools --cov-report=term-missing
```

## Success Criteria
- [ ] Git-tracked files are moved using `git mv`
- [ ] Untracked files use filesystem operations
- [ ] Git can be explicitly disabled with `use_git_if_available=False`
- [ ] Graceful fallback when git operations fail
- [ ] Works without GitPython installed
- [ ] Directories with tracked files are handled correctly
- [ ] Clear logging indicates which method was used
- [ ] All existing tests still pass

## Notes
- GitPython remains optional - system degrades gracefully without it
- Fallback mechanism ensures reliability
- Clear feedback about which method was used
- Maintains backwards compatibility
