# Step 1: Create Git Operations Module with Detection Functions

## Objective
Create a new module `git_operations.py` that provides functions to detect if a directory is a git repository and if a file is tracked by git.

## Test-Driven Development Approach
Write tests first, then implement the functionality to make tests pass.

## Implementation Tasks

### 1. Update Dependencies
Add GitPython as a required dependency in `pyproject.toml`:

```toml
dependencies = [
    "pathspec>=0.12.1",
    "igittigitt>=2.1.5",
    "mcp>=1.3.0",
    "mcp[server]>=1.3.0",
    "mcp[cli]>=1.3.0",
    "structlog>=25.2.0",
    "python-json-logger>=3.3.0",
    "GitPython>=3.1.0",  # Add this line
]
```

### 2. Create Test File
Create `tests/file_tools/test_git_operations.py` with the following tests:

```python
"""Tests for git operations functionality."""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError

from mcp_server_filesystem.file_tools.git_operations import (
    is_git_repository,
    is_file_tracked,
)


class TestGitDetection:
    """Test git repository and file tracking detection."""
    
    def test_is_git_repository_with_actual_repo(self, tmp_path):
        """Test git repository detection using GitPython."""
        # Create actual git repo
        repo = Repo.init(tmp_path)
        assert is_git_repository(tmp_path) is True
        
        # Non-git directory
        non_git = tmp_path / "subdir"
        non_git.mkdir()
        assert is_git_repository(non_git) is False
    
    def test_is_git_repository_with_invalid_repo(self, tmp_path):
        """Test detection when .git exists but is invalid."""
        # Create a .git directory that's not a valid repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Should return False for invalid git repository
        assert is_git_repository(tmp_path) is False
    
    def test_is_file_tracked_without_git(self, tmp_path):
        """Test file tracking when not in a git repository."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        assert is_file_tracked(test_file, tmp_path) is False
    
    def test_is_file_tracked_with_git(self, tmp_path):
        """Test file tracking detection in git repository."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and add a file
        tracked_file = tmp_path / "tracked.txt"
        tracked_file.write_text("tracked content")
        repo.index.add([str(tracked_file)])
        repo.index.commit("Initial commit")
        
        # Create untracked file
        untracked_file = tmp_path / "untracked.txt"
        untracked_file.write_text("untracked content")
        
        assert is_file_tracked(tracked_file, tmp_path) is True
        assert is_file_tracked(untracked_file, tmp_path) is False
    
    def test_is_file_tracked_outside_repo(self, tmp_path):
        """Test file tracking for file outside repository."""
        # Create git repo in a subdirectory
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        repo = Repo.init(repo_dir)
        
        # Create file outside the repo
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("outside content")
        
        # Should return False for file outside repo
        assert is_file_tracked(outside_file, repo_dir) is False
    
    def test_is_file_tracked_with_staged_file(self, tmp_path):
        """Test detection of staged but uncommitted files."""
        # Create git repo
        repo = Repo.init(tmp_path)
        
        # Create and stage a file (but don't commit)
        staged_file = tmp_path / "staged.txt"
        staged_file.write_text("staged content")
        repo.index.add([str(staged_file)])
        
        # Staged files should be considered tracked
        assert is_file_tracked(staged_file, tmp_path) is True
    
    @patch('mcp_server_filesystem.file_tools.git_operations.Repo')
    def test_is_git_repository_with_exception(self, mock_repo, tmp_path):
        """Test handling of unexpected exceptions."""
        mock_repo.side_effect = Exception("Unexpected error")
        
        # Should return False and log warning
        assert is_git_repository(tmp_path) is False
    
    @patch('mcp_server_filesystem.file_tools.git_operations.Repo')
    def test_is_file_tracked_with_git_error(self, mock_repo, tmp_path):
        """Test handling of git command errors."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.ls_files.side_effect = GitCommandError("ls-files", 128)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return False on git errors
        assert is_file_tracked(test_file, tmp_path) is False
```

### 3. Create Git Operations Module
Create `src/mcp_server_filesystem/file_tools/git_operations.py`:

```python
"""Git operations utilities for file system operations."""

import logging
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError

# Use same logging pattern as existing modules (see file_operations.py)
logger = logging.getLogger(__name__)


def is_git_repository(project_dir: Path) -> bool:
    """
    Check if the project directory is a git repository.
    
    Args:
        project_dir: Path to check for git repository
        
    Returns:
        True if the directory is a git repository, False otherwise
    """
    logger.debug(f"Checking if {project_dir} is a git repository")
    
    try:
        Repo(project_dir, search_parent_directories=False)
        logger.debug(f"Detected as git repository: {project_dir}")
        return True
    except InvalidGitRepositoryError:
        logger.debug(f"Not a git repository: {project_dir}")
        return False
    except Exception as e:
        logger.warning(f"Error checking if directory is git repository: {e}")
        return False


def is_file_tracked(file_path: Path, project_dir: Path) -> bool:
    """
    Check if a file is tracked by git.
    
    Args:
        file_path: Path to the file to check
        project_dir: Project directory containing the git repository
        
    Returns:
        True if the file is tracked by git, False otherwise
    """
    if not is_git_repository(project_dir):
        return False
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Get relative path from project directory
        try:
            relative_path = file_path.relative_to(project_dir)
        except ValueError:
            # File is outside project directory
            logger.debug(f"File {file_path} is outside project directory {project_dir}")
            return False
        
        # Convert to posix path for git (even on Windows)
        git_path = str(relative_path).replace('\\', '/')
        
        # Check if file is in the index (staged) or committed
        # This is more accurate than just using ls-files
        try:
            # Try to get the file from the index
            _ = repo.odb.stream(repo.index.entries[(git_path, 0)].binsha)
            return True
        except (KeyError, AttributeError):
            # File not in index, check if it's in committed files
            pass
        
        # Get list of tracked files using ls-files
        tracked_files = repo.git.ls_files().split('\n') if repo.git.ls_files() else []
        
        return git_path in tracked_files
        
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug(f"Git error checking if file is tracked: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking if file is tracked: {e}")
        return False


def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool:
    """
    Move a file using git mv command.
    
    Args:
        source_path: Source file path
        dest_path: Destination file path
        project_dir: Project directory containing the git repository
        
    Returns:
        True if the file was moved successfully using git, False otherwise
        
    Raises:
        GitCommandError: If git mv command fails
    """
    if not is_git_repository(project_dir):
        return False
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Get relative paths from project directory
        try:
            source_relative = source_path.relative_to(project_dir)
            dest_relative = dest_path.relative_to(project_dir)
        except ValueError as e:
            logger.error(f"Paths must be within project directory: {e}")
            return False
        
        # Convert to posix paths for git
        source_git = str(source_relative).replace('\\', '/')
        dest_git = str(dest_relative).replace('\\', '/')
        
        # Execute git mv command
        logger.info(f"Executing git mv from {source_git} to {dest_git}")
        repo.git.mv(source_git, dest_git)
        
        logger.info(f"Successfully moved file using git from {source_git} to {dest_git}")
        return True
        
    except GitCommandError as e:
        logger.error(f"Git move failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during git move: {e}")
        return False
```

### 4. Update __init__.py
Add to `src/mcp_server_filesystem/file_tools/__init__.py`:

```python
# Add these imports to the existing file
from mcp_server_filesystem.file_tools.git_operations import (
    is_git_repository,
    is_file_tracked,
    git_move,
)

# Update __all__ to include new exports
__all__ = [
    # ... existing exports ...
    "is_git_repository",
    "is_file_tracked", 
    "git_move",
]
```

## Verification Commands

Run tests to verify implementation:
```bash
# Install GitPython first
pip install GitPython>=3.1.0

# Run the new git operations tests
pytest tests/file_tools/test_git_operations.py -v

# Run all tests to ensure no regression
pytest tests/ -v

# Check for any import errors
python -c "from mcp_server_filesystem.file_tools.git_operations import is_git_repository, is_file_tracked, git_move; print('Import successful')"
```

## Success Criteria
- [ ] GitPython is listed as a required dependency in pyproject.toml
- [ ] Tests pass with GitPython installed
- [ ] Functions correctly detect git repositories
- [ ] Functions correctly identify tracked vs untracked files
- [ ] Automatic error handling via `@log_function_call` decorator
- [ ] No breaking changes to existing code

## Notes
- This step focuses only on detection and basic git move capabilities
- GitPython is a required dependency
- All error handling happens automatically via existing decorators
- git_move function added for use in later steps
