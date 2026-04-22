"""Tests for parent branch detection via merge-base."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_workspace.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)


class TestDetectParentBranchViaMergeBase:
    """Tests for git merge-base parent branch detection."""

    @pytest.fixture(autouse=True)
    def _patch_get_default_branch(self) -> Generator[MagicMock, None, None]:
        with patch(
            "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
            return_value=None,
        ) as mock_default:
            yield mock_default

    @pytest.fixture
    def mock_repo(self) -> Generator[MagicMock, None, None]:
        """Mock GitPython Repo for merge-base tests."""
        with (
            patch(
                "mcp_workspace.git_operations.parent_branch_detection.is_git_repository"
            ) as mock_is_repo,
            patch(
                "mcp_workspace.git_operations.parent_branch_detection.safe_repo_context"
            ) as mock_context,
        ):
            # is_git_repository returns True by default
            mock_is_repo.return_value = True

            repo_instance = MagicMock()

            # Setup default remote
            mock_origin = MagicMock()
            mock_origin.name = "origin"
            mock_origin.refs = []  # Default empty

            # GitPython's IterableList supports both iteration and attribute access
            # Mock remotes to support: [r for r in repo.remotes] and repo.remotes.origin
            mock_remotes = MagicMock()
            mock_remotes.__iter__ = MagicMock(return_value=iter([mock_origin]))
            mock_remotes.origin = mock_origin
            repo_instance.remotes = mock_remotes

            # Setup context manager to yield repo_instance
            mock_context.return_value.__enter__ = MagicMock(return_value=repo_instance)
            mock_context.return_value.__exit__ = MagicMock(return_value=False)

            yield repo_instance

    def _create_mock_branch(
        self, name: str, commit_hexsha: str = "abc123"
    ) -> MagicMock:
        """Helper to create a mock branch."""
        branch = MagicMock()
        branch.name = name
        branch.commit = MagicMock()
        branch.commit.hexsha = commit_hexsha
        return branch

    def _create_mock_remote_ref(
        self, name: str, commit_hexsha: str = "abc123"
    ) -> MagicMock:
        """Helper to create a mock remote reference."""
        ref = MagicMock()
        ref.name = f"origin/{name}"
        ref.commit = MagicMock()
        ref.commit.hexsha = commit_hexsha
        return ref

    def test_simple_branch_from_main(self, mock_repo: MagicMock) -> None:
        """Standard case: feature branch from main with distance=0."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_main = self._create_mock_branch("main", "main456")
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current, mock_main]))
        mock_heads.__getitem__ = lambda self, key: {
            current_branch: mock_current,
            "main": mock_main,
        }[key]
        mock_repo.heads = mock_heads

        # Setup merge-base
        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "main456"  # Same as main HEAD
        mock_repo.merge_base.return_value = [merge_base_commit]

        # Distance = 0 (main HEAD is the merge-base)
        mock_repo.iter_commits.return_value = []  # 0 commits

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "main"

    def test_branch_from_feature_branch(self, mock_repo: MagicMock) -> None:
        """feature-B branched from feature-A, main is further away."""
        project_dir = Path("/test/project")
        current_branch = "feature-B"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_feature_a = self._create_mock_branch("feature-A", "featureA456")
        mock_main = self._create_mock_branch("main", "main789")
        branch_dict = {
            current_branch: mock_current,
            "feature-A": mock_feature_a,
            "main": mock_main,
        }
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_feature_a, mock_main])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup merge-base - different for each branch
        merge_base_feature_a = MagicMock()
        merge_base_feature_a.hexsha = "featureA456"  # Same as feature-A HEAD
        merge_base_main = MagicMock()
        merge_base_main.hexsha = "oldmain000"

        def mock_merge_base(
            current_commit: MagicMock, target_commit: MagicMock
        ) -> list[MagicMock]:
            if target_commit.hexsha == "featureA456":
                return [merge_base_feature_a]
            return [merge_base_main]

        mock_repo.merge_base.side_effect = mock_merge_base

        # Setup distances: feature-A=0, main=15
        def mock_iter_commits(rev_range: str) -> list[MagicMock]:
            if "featureA456" in rev_range:
                return []  # 0 commits
            return [MagicMock() for _ in range(15)]  # 15 commits

        mock_repo.iter_commits.side_effect = mock_iter_commits

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "feature-A"

    def test_parent_moved_forward(self, mock_repo: MagicMock) -> None:
        """Parent branch got more commits after branching (within threshold)."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_feature_a = self._create_mock_branch("feature-A", "featureA456")
        branch_dict = {current_branch: mock_current, "feature-A": mock_feature_a}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_feature_a])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup merge-base
        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "mergebase000"
        mock_repo.merge_base.return_value = [merge_base_commit]

        # Distance = 5 (feature-A moved 5 commits ahead of merge-base)
        mock_repo.iter_commits.return_value = [MagicMock() for _ in range(5)]

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "feature-A"

    def test_parent_moved_too_far(self, mock_repo: MagicMock) -> None:
        """Parent moved beyond threshold, returns None."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_main = self._create_mock_branch("main", "main456")
        branch_dict = {current_branch: mock_current, "main": mock_main}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current, mock_main]))
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup merge-base
        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "mergebase000"
        mock_repo.merge_base.return_value = [merge_base_commit]

        # Distance = 25 (exceeds MERGE_BASE_DISTANCE_THRESHOLD of 20)
        mock_repo.iter_commits.return_value = [MagicMock() for _ in range(25)]

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result is None

    def test_multiple_candidates_pick_smallest(self, mock_repo: MagicMock) -> None:
        """Multiple branches pass threshold, pick smallest distance."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_feature_a = self._create_mock_branch("feature-A", "featureA456")
        mock_develop = self._create_mock_branch("develop", "develop789")
        branch_dict = {
            current_branch: mock_current,
            "feature-A": mock_feature_a,
            "develop": mock_develop,
        }
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_feature_a, mock_develop])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup merge-base for each
        merge_base_a = MagicMock()
        merge_base_a.hexsha = "mbA"
        merge_base_develop = MagicMock()
        merge_base_develop.hexsha = "mbDevelop"

        def mock_merge_base(
            current_commit: MagicMock, target_commit: MagicMock
        ) -> list[MagicMock]:
            if target_commit.hexsha == "featureA456":
                return [merge_base_a]
            return [merge_base_develop]

        mock_repo.merge_base.side_effect = mock_merge_base

        # Distances: feature-A=3, develop=8 (both within threshold)
        def mock_iter_commits(rev_range: str) -> list[MagicMock]:
            if "mbA" in rev_range:
                return [MagicMock() for _ in range(3)]  # 3 commits
            return [MagicMock() for _ in range(8)]  # 8 commits

        mock_repo.iter_commits.side_effect = mock_iter_commits

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "feature-A"  # Smallest distance wins

    def test_remote_branch_only(self, mock_repo: MagicMock) -> None:
        """Local branch deleted, only origin/feature-A exists."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup local branches (only current branch)
        mock_current = self._create_mock_branch(current_branch, "current123")
        branch_dict = {current_branch: mock_current}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current]))
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup remote branch
        mock_remote_feature_a = self._create_mock_remote_ref("feature-A", "remoteA456")
        mock_repo.remotes.origin.refs = [mock_remote_feature_a]

        # Setup merge-base
        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "remoteA456"  # Same as remote HEAD
        mock_repo.merge_base.return_value = [merge_base_commit]

        # Distance = 2
        mock_repo.iter_commits.return_value = [MagicMock() for _ in range(2)]

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "feature-A"  # Without origin/ prefix

    def test_skips_current_branch(self, mock_repo: MagicMock) -> None:
        """Ensure current branch is skipped in candidate list."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches including current
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_main = self._create_mock_branch("main", "main456")
        branch_dict = {current_branch: mock_current, "main": mock_main}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current, mock_main]))
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # Setup merge-base
        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "main456"
        mock_repo.merge_base.return_value = [merge_base_commit]

        # Distance = 0
        mock_repo.iter_commits.return_value = []

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        # Should return main, not current branch
        assert result == "main"

    def test_no_merge_base_found(self, mock_repo: MagicMock) -> None:
        """Returns None when no merge-base can be found."""
        project_dir = Path("/test/project")
        current_branch = "feature-123"

        # Setup branches
        mock_current = self._create_mock_branch(current_branch, "current123")
        mock_orphan = self._create_mock_branch("orphan", "orphan456")
        branch_dict = {current_branch: mock_current, "orphan": mock_orphan}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current, mock_orphan]))
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        # No merge-base (orphan branch)
        mock_repo.merge_base.return_value = []

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result is None

    def test_repo_not_git_repository(self) -> None:
        """Returns None when directory is not a git repository."""
        project_dir = Path("/test/project")

        with patch(
            "mcp_workspace.git_operations.parent_branch_detection.is_git_repository"
        ) as mock_is_repo:
            mock_is_repo.return_value = False

            result = detect_parent_branch_via_merge_base(project_dir, "feature-123")

        assert result is None

    @patch(
        "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
        return_value="main",
    )
    def test_selects_main_over_dormant_feature_branch(
        self, mock_get_default: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Regression: current from main, dormant feature-old far away."""
        project_dir = Path("/test/project")
        current_branch = "current"

        mock_current = self._create_mock_branch(current_branch, "cur1")
        mock_main = self._create_mock_branch("main", "main1")
        mock_old = self._create_mock_branch("feature-old", "old1")
        branch_dict = {
            current_branch: mock_current,
            "main": mock_main,
            "feature-old": mock_old,
        }
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_main, mock_old])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        mb_main = MagicMock()
        mb_main.hexsha = "mb_main"
        mb_old = MagicMock()
        mb_old.hexsha = "mb_old"

        def mock_merge_base(
            current_commit: MagicMock, target_commit: MagicMock
        ) -> list[MagicMock]:
            if target_commit.hexsha == "main1":
                return [mb_main]
            return [mb_old]

        mock_repo.merge_base.side_effect = mock_merge_base

        def mock_iter_commits(rev_range: str) -> list[MagicMock]:
            if "mb_main" in rev_range:
                return [MagicMock() for _ in range(2)]
            return [MagicMock() for _ in range(18)]

        mock_repo.iter_commits.side_effect = mock_iter_commits

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "main"

    @patch(
        "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
        return_value="main",
    )
    def test_prefers_default_branch_on_equal_distance(
        self, mock_get_default: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Default branch wins when two candidates have equal distance."""
        project_dir = Path("/test/project")
        current_branch = "current"

        mock_current = self._create_mock_branch(current_branch, "cur1")
        mock_develop = self._create_mock_branch("develop", "dev1")
        mock_main = self._create_mock_branch("main", "main1")
        branch_dict = {
            current_branch: mock_current,
            "develop": mock_develop,
            "main": mock_main,
        }
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_develop, mock_main])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        mb_main = MagicMock()
        mb_main.hexsha = "mb_main"
        mb_dev = MagicMock()
        mb_dev.hexsha = "mb_dev"

        def mock_merge_base(
            current_commit: MagicMock, target_commit: MagicMock
        ) -> list[MagicMock]:
            if target_commit.hexsha == "main1":
                return [mb_main]
            return [mb_dev]

        mock_repo.merge_base.side_effect = mock_merge_base

        def mock_iter_commits(rev_range: str) -> list[MagicMock]:
            return [MagicMock() for _ in range(3)]

        mock_repo.iter_commits.side_effect = mock_iter_commits

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "main"

    def test_includes_candidate_at_threshold(self, mock_repo: MagicMock) -> None:
        """Candidate at exactly the distance threshold is included."""
        project_dir = Path("/test/project")
        current_branch = "current"

        mock_current = self._create_mock_branch(current_branch, "cur1")
        mock_main = self._create_mock_branch("main", "main1")
        branch_dict = {current_branch: mock_current, "main": mock_main}
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(return_value=iter([mock_current, mock_main]))
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        merge_base_commit = MagicMock()
        merge_base_commit.hexsha = "mb1"
        mock_repo.merge_base.return_value = [merge_base_commit]

        mock_repo.iter_commits.return_value = [MagicMock() for _ in range(20)]

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "main"

    @patch(
        "mcp_workspace.git_operations.parent_branch_detection.get_default_branch_name",
        return_value="main",
    )
    def test_distance_zero_collects_all_candidates(
        self, mock_get_default: MagicMock, mock_repo: MagicMock
    ) -> None:
        """Both candidates at distance 0; tiebreaker picks default branch."""
        project_dir = Path("/test/project")
        current_branch = "current"

        mock_current = self._create_mock_branch(current_branch, "cur1")
        mock_develop = self._create_mock_branch("develop", "dev1")
        mock_main = self._create_mock_branch("main", "main1")
        branch_dict = {
            current_branch: mock_current,
            "develop": mock_develop,
            "main": mock_main,
        }
        mock_heads = MagicMock()
        mock_heads.__iter__ = MagicMock(
            return_value=iter([mock_current, mock_develop, mock_main])
        )
        mock_heads.__getitem__ = lambda self, key: branch_dict[key]
        mock_repo.heads = mock_heads

        mb_dev = MagicMock()
        mb_dev.hexsha = "mb_dev"
        mb_main = MagicMock()
        mb_main.hexsha = "mb_main"

        def mock_merge_base(
            current_commit: MagicMock, target_commit: MagicMock
        ) -> list[MagicMock]:
            if target_commit.hexsha == "dev1":
                return [mb_dev]
            return [mb_main]

        mock_repo.merge_base.side_effect = mock_merge_base

        mock_repo.iter_commits.return_value = []

        result = detect_parent_branch_via_merge_base(project_dir, current_branch)

        assert result == "main"

    def test_threshold_constant_value(self) -> None:
        """Verify MERGE_BASE_DISTANCE_THRESHOLD has expected value."""
        assert MERGE_BASE_DISTANCE_THRESHOLD == 20
