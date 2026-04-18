"""Tests for branch query operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_workspace.git_operations.branch_queries import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    remote_branch_exists,
    validate_branch_name,
)


class TestBranchValidation:
    """Tests for branch name validation."""

    def test_valid_names(self) -> None:
        """Test valid branch names return True."""
        assert validate_branch_name("main") is True
        assert validate_branch_name("feature/xyz") is True
        assert validate_branch_name("123-fix-bug") is True

    def test_invalid_empty(self) -> None:
        """Test empty branch names return False."""
        assert validate_branch_name("") is False
        assert validate_branch_name("   ") is False  # whitespace-only

    def test_invalid_characters(self) -> None:
        """Test branch names with invalid characters return False."""
        # Test one representative invalid character
        assert validate_branch_name("branch~1") is False
        assert validate_branch_name("feature^branch") is False
        assert validate_branch_name("fix:bug") is False
        assert validate_branch_name("branch?name") is False
        assert validate_branch_name("feature*branch") is False
        assert validate_branch_name("branch[name]") is False


class TestBranchNameExtraction:
    """Tests for extracting issue numbers from branch names."""

    def test_extract_issue_number_from_branch_valid(self) -> None:
        """Tests extraction from valid branch names."""
        assert extract_issue_number_from_branch("123-feature-name") == 123
        assert extract_issue_number_from_branch("1-fix") == 1
        assert extract_issue_number_from_branch("999-long-branch-name-here") == 999

    def test_extract_issue_number_from_branch_invalid(self) -> None:
        """Tests extraction from invalid branch names returns None."""
        assert extract_issue_number_from_branch("feature-branch") is None
        assert extract_issue_number_from_branch("main") is None
        assert (
            extract_issue_number_from_branch("feature-123-name") is None
        )  # Number not at start

    def test_extract_issue_number_from_branch_edge_cases(self) -> None:
        """Tests edge cases for issue number extraction."""
        assert extract_issue_number_from_branch("") is None
        assert extract_issue_number_from_branch("123") is None  # No hyphen after number
        assert (
            extract_issue_number_from_branch("-feature") is None
        )  # No number before hyphen


@pytest.mark.git_integration
class TestBranchExistence:
    """Tests for branch existence checks."""

    def test_branch_exists(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        """Test branch_exists detects local branches."""
        repo, project_dir = git_repo_with_commit

        # Get current branch name
        current_branch = repo.active_branch.name

        # Current branch should exist
        assert branch_exists(project_dir, current_branch) is True

        # Non-existent branch should not exist
        assert branch_exists(project_dir, "nonexistent-branch") is False

    def test_remote_branch_exists_returns_true(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns True for existing remote branch."""
        repo, project_dir, _ = git_repo_with_remote
        # Get actual branch name (could be master or main depending on git config)
        current_branch = repo.active_branch.name
        # Push current branch to remote
        repo.git.push("-u", "origin", current_branch)
        assert remote_branch_exists(project_dir, current_branch) is True

    def test_remote_branch_exists_returns_false_for_nonexistent(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns False for non-existing remote branch."""
        _, project_dir, _ = git_repo_with_remote
        assert remote_branch_exists(project_dir, "nonexistent-branch") is False

    def test_remote_branch_exists_returns_false_no_origin(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test remote_branch_exists returns False when no origin remote."""
        _, project_dir = git_repo_with_commit
        assert remote_branch_exists(project_dir, "master") is False

    def test_remote_branch_exists_invalid_inputs(self, tmp_path: Path) -> None:
        """Test remote_branch_exists returns False for invalid inputs."""
        assert remote_branch_exists(tmp_path, "master") is False  # Not a repo

    def test_remote_branch_exists_empty_branch_name(
        self, git_repo_with_remote: tuple[Repo, Path, Path]
    ) -> None:
        """Test remote_branch_exists returns False for empty branch name."""
        _, project_dir, _ = git_repo_with_remote
        assert remote_branch_exists(project_dir, "") is False


@pytest.mark.git_integration
class TestBranchNameReaders:
    """Tests for branch name reader functions."""

    def test_get_current_branch_name(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_current_branch_name returns current branch."""
        repo, project_dir = git_repo_with_commit

        # Get actual branch name
        expected_branch = repo.active_branch.name

        # Should return the current branch
        assert get_current_branch_name(project_dir) == expected_branch

    def test_get_default_branch_name(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        """Test get_default_branch_name returns main or master."""
        _repo, project_dir = git_repo_with_commit

        default_branch = get_default_branch_name(project_dir)
        assert default_branch in ["main", "master"]
