"""Minimal tests for git staging operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_workspace.file_tools.git_operations.staging import (
    stage_all_changes,
    stage_specific_files,
)


@pytest.mark.git_integration
class TestStagingOperations:
    """Minimal tests for staging operations - one test per function."""

    def test_stage_all_changes(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test stage_all_changes stages all files."""
        repo, project_dir = git_repo_with_commit

        # Create multiple files
        file1 = project_dir / "file1.py"
        file1.write_text("# File 1")
        file2 = project_dir / "file2.py"
        file2.write_text("# File 2")

        # Stage all changes
        result = stage_all_changes(project_dir)

        assert result is True

        # Verify files are staged
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        assert "file1.py" in staged
        assert "file2.py" in staged

    def test_stage_specific_files(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test stage_specific_files stages only specified files."""
        repo, project_dir = git_repo_with_commit

        # Create multiple files
        file1 = project_dir / "file1.py"
        file1.write_text("# File 1")
        file2 = project_dir / "file2.py"
        file2.write_text("# File 2")
        file3 = project_dir / "file3.py"
        file3.write_text("# File 3")

        # Stage only specific files
        result = stage_specific_files([file1, file2], project_dir)

        assert result is True

        # Verify only specified files are staged
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        assert "file1.py" in staged
        assert "file2.py" in staged

        # file3.py should still be untracked
        assert "file3.py" in repo.untracked_files
