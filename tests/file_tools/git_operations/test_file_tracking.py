"""Minimal tests for git file tracking operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_workspace.file_tools.git_operations.file_tracking import (
    git_move,
    is_file_tracked,
)
from mcp_workspace.file_tools.git_operations.workflows import commit_all_changes


@pytest.mark.git_integration
class TestFileTrackingOperations:
    """Minimal tests for file tracking operations - one test per function."""

    def test_is_file_tracked(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test is_file_tracked detects tracked files."""
        _repo, project_dir = git_repo_with_commit

        # README.md is tracked (from initial commit)
        readme = project_dir / "README.md"
        assert is_file_tracked(readme, project_dir) is True

        # New file is not tracked
        new_file = project_dir / "new.py"
        new_file.write_text("# New file")
        assert is_file_tracked(new_file, project_dir) is False

        # After committing, file is tracked
        commit_all_changes("Add new file", project_dir)
        assert is_file_tracked(new_file, project_dir) is True

    def test_git_move(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test git_move renames/moves tracked files."""
        _repo, project_dir = git_repo_with_commit

        # Move README.md to docs/README.md
        docs_dir = project_dir / "docs"
        docs_dir.mkdir()

        source = project_dir / "README.md"
        dest = project_dir / "docs" / "README.md"
        result = git_move(source, dest, project_dir)

        assert result is True

        # Old path should not exist
        assert not source.exists()

        # New path should exist
        assert dest.exists()

        # New file should be tracked
        assert is_file_tracked(dest, project_dir) is True
