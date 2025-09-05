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
    
    def test_is_git_repository_with_actual_repo(self, tmp_path: Path) -> None:
        """Test git repository detection using GitPython."""
        # Create actual git repo
        repo = Repo.init(tmp_path)
        assert is_git_repository(tmp_path) is True
        
        # Non-git directory
        non_git = tmp_path / "subdir"
        non_git.mkdir()
        assert is_git_repository(non_git) is False
    
    def test_is_git_repository_with_invalid_repo(self, tmp_path: Path) -> None:
        """Test detection when .git exists but is invalid."""
        # Create a .git directory that's not a valid repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Should return False for invalid git repository
        assert is_git_repository(tmp_path) is False
    
    def test_is_file_tracked_without_git(self, tmp_path: Path) -> None:
        """Test file tracking when not in a git repository."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        assert is_file_tracked(test_file, tmp_path) is False
    
    def test_is_file_tracked_with_git(self, tmp_path: Path) -> None:
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
    
    def test_is_file_tracked_outside_repo(self, tmp_path: Path) -> None:
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
    
    def test_is_file_tracked_with_staged_file(self, tmp_path: Path) -> None:
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
    def test_is_git_repository_with_exception(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of unexpected exceptions."""
        mock_repo.side_effect = Exception("Unexpected error")
        
        # Should return False and log warning
        assert is_git_repository(tmp_path) is False
    
    @patch('mcp_server_filesystem.file_tools.git_operations.Repo')
    def test_is_file_tracked_with_git_error(self, mock_repo: Mock, tmp_path: Path) -> None:
        """Test handling of git command errors."""
        mock_instance = Mock()
        mock_repo.return_value = mock_instance
        mock_instance.git.ls_files.side_effect = GitCommandError("ls-files", 128)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Should return False on git errors
        assert is_file_tracked(test_file, tmp_path) is False
