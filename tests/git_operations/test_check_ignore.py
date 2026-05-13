"""Integration tests for git_check_ignore()."""

from pathlib import Path

import pytest
from git import Repo

from mcp_workspace.git_operations.read_operations import git, git_check_ignore


@pytest.mark.git_integration
class TestGitCheckIgnore:
    """Tests for git_check_ignore()."""

    def _setup_ignored(self, project_dir: Path, repo: Repo) -> None:
        (project_dir / ".gitignore").write_text("*.txt\n")
        repo.index.add([".gitignore"])
        repo.index.commit("Add gitignore")

    def test_ignored_path_returns_path(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(project_dir, pathspec=["foo.txt"])
        assert "foo.txt" in result

    def test_ignored_path_verbose_returns_rule_source(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(project_dir, args=["-v"], pathspec=["foo.txt"])
        assert ".gitignore" in result
        assert "*.txt" in result
        assert "foo.txt" in result

    def test_verbose_non_matching_mixed_output(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git_check_ignore(
            project_dir, args=["-v", "-n"], pathspec=["foo.txt", "bar.md"]
        )
        assert "foo.txt" in result
        assert "bar.md" in result

    def test_none_ignored_returns_message(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        result = git_check_ignore(project_dir, pathspec=["bar.md"])
        assert result == "No paths are ignored."

    def test_empty_pathspec_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="'pathspec'"):
            git_check_ignore(project_dir, pathspec=[])

    def test_none_pathspec_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="'pathspec'"):
            git_check_ignore(project_dir, pathspec=None)

    def test_disallowed_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_check_ignore(project_dir, args=["--stdin"], pathspec=["foo.txt"])

    def test_dispatcher_routes_to_check_ignore(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        self._setup_ignored(project_dir, repo)
        result = git(
            command="check_ignore",
            project_dir=project_dir,
            pathspec=["foo.txt"],
        )
        assert "foo.txt" in result
