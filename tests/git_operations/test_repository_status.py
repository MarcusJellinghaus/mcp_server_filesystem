"""Tests for repository status operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_workspace.git_operations.repository_status import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
)


@pytest.mark.git_integration
class TestRepositoryReaders:
    """Tests for repository status reader functions."""

    def test_is_git_repository(
        self, git_repo: tuple[Repo, Path], tmp_path: Path
    ) -> None:
        """Test is_git_repository detects git repos."""
        _repo, project_dir = git_repo

        # Should detect git repo
        assert is_git_repository(project_dir) is True

        # Should not detect non-git directory
        non_git_dir = tmp_path / "not_a_repo"
        non_git_dir.mkdir()
        assert is_git_repository(non_git_dir) is False

    def test_is_working_directory_clean(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test is_working_directory_clean detects changes."""
        _repo, project_dir = git_repo_with_commit

        # Clean working directory
        assert is_working_directory_clean(project_dir) is True

        # Add untracked file
        new_file = project_dir / "new.py"
        new_file.write_text("# New file")
        assert is_working_directory_clean(project_dir) is False

    def test_get_staged_changes(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test get_staged_changes returns staged files."""
        repo, project_dir = git_repo_with_commit

        # No staged changes initially
        staged = get_staged_changes(project_dir)
        assert staged == []

        # Stage a file
        new_file = project_dir / "staged.py"
        new_file.write_text("# Staged file")
        repo.index.add(["staged.py"])

        # Should detect staged file
        staged = get_staged_changes(project_dir)
        assert len(staged) == 1
        assert "staged.py" in staged[0]

    def test_get_unstaged_changes(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_unstaged_changes returns modified files."""
        _repo, project_dir = git_repo_with_commit

        # No unstaged changes initially
        unstaged = get_unstaged_changes(project_dir)
        assert unstaged == {"modified": [], "untracked": []}

        # Modify tracked file
        readme = project_dir / "README.md"
        readme.write_text("# Modified")

        # Should detect unstaged change
        unstaged = get_unstaged_changes(project_dir)
        assert len(unstaged["modified"]) == 1
        assert "README.md" in unstaged["modified"][0]

    def test_get_full_status(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test get_full_status returns complete status."""
        repo, project_dir = git_repo_with_commit

        # Create staged, modified, and untracked files
        staged_file = project_dir / "staged.py"
        staged_file.write_text("# Staged")
        repo.index.add(["staged.py"])

        modified_file = project_dir / "README.md"
        modified_file.write_text("# Modified")

        untracked_file = project_dir / "untracked.py"
        untracked_file.write_text("# Untracked")

        # Get full status
        status = get_full_status(project_dir)

        assert "staged" in status
        assert "modified" in status
        assert "untracked" in status
        assert any("staged.py" in f for f in status["staged"])
        assert any("README.md" in f for f in status["modified"])
        assert any("untracked.py" in f for f in status["untracked"])

    def test_is_working_directory_clean_ignore_files_none(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files=None preserves existing behavior."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file
        new_file = project_dir / "new.txt"
        new_file.write_text("new content")

        # Should return False - untracked file detected
        assert is_working_directory_clean(project_dir, ignore_files=None) is False

    def test_is_working_directory_clean_ignore_files_empty_list(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files=[] behaves same as None (backward compatibility)."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file
        new_file = project_dir / "new.txt"
        new_file.write_text("new content")

        # Should return False - empty list should not filter anything
        assert is_working_directory_clean(project_dir, ignore_files=[]) is False

    def test_is_working_directory_clean_ignore_files_matches_untracked(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files filters matching untracked file."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file that should be ignored
        uv_lock = project_dir / "uv.lock"
        uv_lock.write_text("lock content")

        # Should return True - uv.lock is ignored, directory is clean
        assert is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is True

    def test_is_working_directory_clean_ignore_files_other_untracked(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files does not filter non-matching files."""
        _repo, project_dir = git_repo_with_commit

        # Create untracked file that does NOT match ignore_files
        other_file = project_dir / "other.txt"
        other_file.write_text("other content")

        # Should return False - other.txt is not ignored
        assert (
            is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is False
        )

    def test_is_working_directory_clean_ignore_files_with_other_changes(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test ignore_files with matching file AND other changes."""
        _repo, project_dir = git_repo_with_commit

        # Create ignored file AND another untracked file
        uv_lock = project_dir / "uv.lock"
        uv_lock.write_text("lock content")

        real_change = project_dir / "real_change.txt"
        real_change.write_text("real change content")

        # Should return False - real_change.txt is still detected
        assert (
            is_working_directory_clean(project_dir, ignore_files=["uv.lock"]) is False
        )
