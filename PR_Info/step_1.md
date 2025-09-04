# Step 1: Create Git Operations Module with Detection Functions

## Objective
Create a new module `git_operations.py` that provides functions to detect if a directory is a git repository and if a file is tracked by git.

## Test-Driven Development Approach
Write tests first, then implement the functionality to make tests pass.

## Implementation Tasks

### 1. Create Test File
Create `tests/file_tools/test_git_operations.py` with the following tests:

```python
"""Tests for git operations functionality."""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from mcp_server_filesystem.file_tools.git_operations import (
    is_git_repository,
    is_file_tracked,
    HAS_GITPYTHON
)


class TestGitDetection:
    """Test git repository and file tracking detection."""
    
    def test_is_git_repository_with_git_dir(self, tmp_path):
        """Test detection of git repository by .git directory."""
        # Create a .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Without GitPython, should detect by .git directory
        with patch('mcp_server_filesystem.file_tools.git_operations.HAS_GITPYTHON', False):
            assert is_git_repository(tmp_path) is True
            
        # Non-git directory
        non_git = tmp_path / "subdir"
        non_git.mkdir()
        assert is_git_repository(non_git) is False
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_is_git_repository_with_gitpython(self, tmp_path):
        """Test git repository detection using GitPython."""
        from git import Repo
        
        # Create actual git repo
        repo = Repo.init(tmp_path)
        assert is_git_repository(tmp_path) is True
        
        # Non-git directory
        non_git = tmp_path / "subdir"
        non_git.mkdir()
        assert is_git_repository(non_git) is False
    
    def test_is_file_tracked_without_git(self, tmp_path):
        """Test file tracking when not in a git repository."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        assert is_file_tracked(test_file, tmp_path) is False
    
    @pytest.mark.skipif(not HAS_GITPYTHON, reason="GitPython not installed")
    def test_is_file_tracked_with_git(self, tmp_path):
        """Test file tracking detection in git repository."""
        from git import Repo
        
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
```

### 2. Create Git Operations Module
Create `src/mcp_server_filesystem/file_tools/git_operations.py`:

```python
"""Git operations utilities for file system operations."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import GitPython, but make it optional
try:
    from git import Repo
    from git.exc import InvalidGitRepositoryError, GitCommandError
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False
    # Define dummy exceptions for type checking
    class InvalidGitRepositoryError(Exception):
        pass
    class GitCommandError(Exception):
        pass
    logger.info("GitPython not installed, git operations will use fallback methods")


def is_git_repository(project_dir: Path) -> bool:
    """
    Check if the project directory is a git repository.
    
    Args:
        project_dir: Path to check for git repository
        
    Returns:
        True if the directory is a git repository, False otherwise
    """
    if not HAS_GITPYTHON:
        # Fallback: check if .git directory exists
        git_dir = project_dir / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    try:
        Repo(project_dir, search_parent_directories=False)
        return True
    except InvalidGitRepositoryError:
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
    if not HAS_GITPYTHON:
        return False
        
    if not is_git_repository(project_dir):
        return False
    
    try:
        repo = Repo(project_dir, search_parent_directories=False)
        
        # Get relative path from project directory
        try:
            relative_path = file_path.relative_to(project_dir)
        except ValueError:
            # File is outside project directory
            return False
        
        # Convert to posix path for git (even on Windows)
        git_path = str(relative_path).replace('\\', '/')
        
        # Get list of tracked files
        tracked_files = repo.git.ls_files().split('\n') if repo.git.ls_files() else []
        
        return git_path in tracked_files
        
    except (InvalidGitRepositoryError, GitCommandError) as e:
        logger.debug(f"Git error checking if file is tracked: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking if file is tracked: {e}")
        return False
```

### 3. Update __init__.py
Add to `src/mcp_server_filesystem/file_tools/__init__.py`:

```python
# Add these imports to the existing file
from mcp_server_filesystem.file_tools.git_operations import (
    is_git_repository,
    is_file_tracked,
    HAS_GITPYTHON
)

# Update __all__ to include new exports
__all__ = [
    # ... existing exports ...
    "is_git_repository",
    "is_file_tracked",
    "HAS_GITPYTHON",
]
```

## Verification Commands

Run tests to verify implementation:
```bash
# Run the new git operations tests
pytest tests/file_tools/test_git_operations.py -v

# Check if tests pass without GitPython
pip uninstall GitPython
pytest tests/file_tools/test_git_operations.py -v

# Install GitPython and test again
pip install GitPython
pytest tests/file_tools/test_git_operations.py -v
```

## Success Criteria
- [ ] Tests pass without GitPython installed (fallback mode)
- [ ] Tests pass with GitPython installed
- [ ] Functions correctly detect git repositories
- [ ] Functions correctly identify tracked vs untracked files
- [ ] Proper error handling and logging
- [ ] No breaking changes to existing code

## Notes
- This step focuses only on detection capabilities
- No actual file operations are performed yet
- GitPython is treated as an optional dependency
- Graceful fallback when GitPython is not available
