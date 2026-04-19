"""Integration tests for read-only git operations.

All tests use real git repos via the ``git_repo_with_commit`` fixture.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import Repo

from mcp_workspace.git_operations.read_operations import (
    git_diff,
    git_log,
    git_merge_base,
    git_status,
)


@pytest.mark.git_integration
class TestGitLog:
    """Tests for git_log()."""

    def test_basic_log_returns_commits(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        result = git_log(project_dir)
        assert "Initial commit" in result

    def test_log_with_oneline(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        result = git_log(project_dir, args=["--oneline"])
        # Oneline format: short hash + message on one line
        lines = result.strip().splitlines()
        assert len(lines) >= 1
        assert "Initial commit" in lines[0]

    def test_log_with_pathspec(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        repo, project_dir = git_repo_with_commit
        # Create a second file with its own commit
        (project_dir / "other.txt").write_text("other")
        repo.index.add(["other.txt"])
        repo.index.commit("Add other file")

        result = git_log(project_dir, pathspec=["README.md"])
        assert "Initial commit" in result
        assert "Add other file" not in result

    def test_log_search_filters_output(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        (project_dir / "marker.txt").write_text("UNIQUE_MARKER")
        repo.index.add(["marker.txt"])
        repo.index.commit("Second commit with UNIQUE_MARKER")

        result = git_log(project_dir, search="UNIQUE_MARKER")
        assert "UNIQUE_MARKER" in result
        assert "Initial commit" not in result

    def test_log_max_lines_truncates(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        # Create several commits to generate multi-line output
        for i in range(10):
            (project_dir / f"file_{i}.txt").write_text(f"content {i}")
            repo.index.add([f"file_{i}.txt"])
            repo.index.commit(f"Commit number {i}")

        result = git_log(project_dir, max_lines=3)
        assert "[truncated" in result

    def test_log_empty_repo_message(self, git_repo: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo
        result = git_log(project_dir)
        assert result == "No commits found"

    def test_log_rejected_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_log(project_dir, args=["--exec=evil"])

    def test_log_hardcodes_safety_flags(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with patch(
            "mcp_workspace.git_operations.read_operations._safe_repo_context"
        ) as mock_ctx:
            mock_repo = MagicMock()
            mock_repo.git.log.return_value = "mocked"
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_repo)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            git_log(project_dir, args=["--oneline"])

            call_args = mock_repo.git.log.call_args[0]
            assert "--no-ext-diff" in call_args
            assert "--no-textconv" in call_args


@pytest.mark.git_integration
class TestGitDiff:
    """Tests for git_diff()."""

    def test_basic_diff_returns_changes(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# Changed")
        result = git_diff(project_dir, compact=False)
        assert "Changed" in result

    def test_diff_staged(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        repo, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# Staged change")
        repo.index.add(["README.md"])
        result = git_diff(project_dir, args=["--staged"], compact=False)
        assert "Staged change" in result

    def test_diff_between_refs(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        repo, project_dir = git_repo_with_commit
        first_sha = repo.head.commit.hexsha
        (project_dir / "README.md").write_text("# Updated")
        repo.index.add(["README.md"])
        repo.index.commit("Update readme")

        result = git_diff(project_dir, args=[first_sha, "HEAD"], compact=False)
        assert "Updated" in result

    def test_diff_with_pathspec(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# Changed readme")
        (project_dir / "other.txt").write_text("other change")
        result = git_diff(project_dir, pathspec=["README.md"], compact=False)
        assert "Changed readme" in result
        assert "other change" not in result

    def test_diff_compact_default(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# Changed for compact")
        # compact=True is default
        result = git_diff(project_dir)
        assert "Changed for compact" in result

    def test_diff_compact_false_raw(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# Raw diff")
        result = git_diff(project_dir, compact=False)
        # Raw diff should contain standard diff markers
        assert "diff --git" in result

    def test_diff_search_filters(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "README.md").write_text("# SEARCHABLE_TOKEN here")
        result = git_diff(project_dir, search="SEARCHABLE_TOKEN", compact=False)
        assert "SEARCHABLE_TOKEN" in result

    def test_diff_max_lines_truncates(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        # Create a large tracked change
        content = "\n".join(f"line {i}" for i in range(200))
        (project_dir / "README.md").write_text(content)
        result = git_diff(project_dir, max_lines=5, compact=False)
        assert "[truncated" in result

    def test_diff_no_changes_message(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        result = git_diff(project_dir)
        assert result == "No changes found"

    def test_diff_rejected_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_diff(project_dir, args=["--output=evil"])

    def test_diff_hardcodes_safety_flags(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with patch(
            "mcp_workspace.git_operations.read_operations._safe_repo_context"
        ) as mock_ctx:
            mock_repo = MagicMock()
            mock_repo.git.diff.return_value = ""
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_repo)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            git_diff(project_dir, compact=False)

            call_args = mock_repo.git.diff.call_args[0]
            assert "--no-ext-diff" in call_args
            assert "--no-textconv" in call_args


@pytest.mark.git_integration
class TestGitStatus:
    """Tests for git_status()."""

    def test_status_clean_repo(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        result = git_status(project_dir)
        # A clean repo should mention "nothing to commit" or similar
        assert "nothing to commit" in result or "clean" in result.lower()

    def test_status_with_changes(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "new_file.txt").write_text("new content")
        result = git_status(project_dir)
        assert "new_file.txt" in result

    def test_status_short_flag(self, git_repo_with_commit: tuple[Repo, Path]) -> None:
        _, project_dir = git_repo_with_commit
        (project_dir / "new_file.txt").write_text("content")
        result = git_status(project_dir, args=["--short"])
        assert "new_file.txt" in result
        # Short format uses ?? for untracked
        assert "??" in result

    def test_status_max_lines_truncates(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        # Create many untracked files
        for i in range(50):
            (project_dir / f"file_{i}.txt").write_text(f"content {i}")
        result = git_status(project_dir, max_lines=3)
        assert "[truncated" in result

    def test_status_rejected_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_status(project_dir, args=["--exec=evil"])


@pytest.mark.git_integration
class TestGitMergeBase:
    """Tests for git_merge_base()."""

    def test_merge_base_two_branches(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        # Rename to main for consistency
        repo.git.branch("-M", "main")
        # Create a feature branch with a new commit
        repo.git.checkout("-b", "feature")
        (project_dir / "feature.txt").write_text("feature")
        repo.index.add(["feature.txt"])
        repo.index.commit("Feature commit")
        repo.git.checkout("main")

        result = git_merge_base(project_dir, args=["main", "feature"])
        # Should return the initial commit SHA
        assert len(result.strip()) >= 7

    def test_merge_base_is_ancestor(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        repo.git.branch("-M", "main")
        initial_sha = repo.head.commit.hexsha
        (project_dir / "second.txt").write_text("second")
        repo.index.add(["second.txt"])
        repo.index.commit("Second commit")

        result = git_merge_base(
            project_dir, args=["--is-ancestor", initial_sha, "HEAD"]
        )
        assert result == "true"

    def test_merge_base_not_ancestor(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        repo, project_dir = git_repo_with_commit
        repo.git.branch("-M", "main")
        (project_dir / "second.txt").write_text("second")
        repo.index.add(["second.txt"])
        repo.index.commit("Second commit")
        head_sha = repo.head.commit.hexsha

        # HEAD is not an ancestor of the initial commit
        initial_sha = repo.head.commit.parents[0].hexsha
        result = git_merge_base(
            project_dir, args=["--is-ancestor", head_sha, initial_sha]
        )
        assert result == "false"

    def test_merge_base_rejected_flag_raises(
        self, git_repo_with_commit: tuple[Repo, Path]
    ) -> None:
        _, project_dir = git_repo_with_commit
        with pytest.raises(ValueError, match="not in the security allowlist"):
            git_merge_base(project_dir, args=["--exec=evil"])
