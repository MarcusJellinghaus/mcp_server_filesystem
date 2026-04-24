"""Tests for branch_status check module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_workspace.checks.branch_status import (
    BranchStatusReport,
    CIStatus,
    _apply_pr_merge_override,
    _collect_ci_status,
    _collect_github_label,
    _collect_pr_info,
    _collect_rebase_status,
    _collect_task_status,
    _generate_recommendations,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
)
from mcp_workspace.github_operations.issues import IssueData
from mcp_workspace.workflows.task_tracker import TaskTrackerStatus


class TestCIStatus:
    """Tests for CIStatus enum."""

    def test_values(self) -> None:
        assert CIStatus.PASSED.value == "PASSED"
        assert CIStatus.FAILED.value == "FAILED"
        assert CIStatus.NOT_CONFIGURED.value == "NOT_CONFIGURED"
        assert CIStatus.PENDING.value == "PENDING"


class TestBranchStatusReport:
    """Tests for BranchStatusReport dataclass."""

    def test_create_report(self) -> None:
        report = BranchStatusReport(
            branch_name="123-feature",
            base_branch="main",
            ci_status=CIStatus.PASSED,
            ci_details=None,
            rebase_needed=False,
            rebase_reason="up-to-date",
            tasks_status=TaskTrackerStatus.COMPLETE,
            tasks_reason="All 5 tasks complete",
            tasks_is_blocking=False,
            current_github_label="status-04:in-progress",
            recommendations=[],
            pr_number=45,
            pr_url="https://github.com/owner/repo/pull/45",
            pr_found=True,
        )
        assert report.branch_name == "123-feature"
        assert report.ci_status == CIStatus.PASSED
        assert report.pr_number == 45

    def test_format_for_human(self) -> None:
        report = BranchStatusReport(
            branch_name="123-feature",
            base_branch="main",
            ci_status=CIStatus.PASSED,
            ci_details=None,
            rebase_needed=False,
            rebase_reason="up-to-date",
            tasks_status=TaskTrackerStatus.COMPLETE,
            tasks_reason="All 5 tasks complete",
            tasks_is_blocking=False,
            current_github_label="status-04:in-progress",
            recommendations=["Do something"],
            pr_number=45,
            pr_url="https://github.com/owner/repo/pull/45",
            pr_found=True,
        )
        output = report.format_for_human()
        assert "Branch Status Report" in output
        assert "Branch: 123-feature" in output
        assert "Base Branch: main" in output
        assert "CI Status:" in output
        assert "PASSED" in output
        assert "Rebase Status:" in output
        assert "UP TO DATE" in output
        assert "Task Tracker:" in output
        assert "GitHub Status:" in output
        assert "PR:" in output
        assert "#45" in output
        assert "- Do something" in output
        assert "Recommendations:" in output

    def test_format_for_llm(self) -> None:
        report = BranchStatusReport(
            branch_name="123-feature",
            base_branch="main",
            ci_status=CIStatus.FAILED,
            ci_details="Error in test step",
            rebase_needed=True,
            rebase_reason="3 commits behind",
            tasks_status=TaskTrackerStatus.INCOMPLETE,
            tasks_reason="3 of 5 tasks complete",
            tasks_is_blocking=True,
            current_github_label="status-04:in-progress",
            recommendations=["Fix CI", "Rebase"],
            pr_number=45,
            pr_url="https://github.com/owner/repo/pull/45",
            pr_found=True,
        )
        output = report.format_for_llm()
        assert "Branch: 123-feature | Base: main" in output
        assert "Branch Status: CI=FAILED" in output
        assert "Rebase=BEHIND" in output
        assert "Recommendations:" in output
        assert "CI Errors:" in output
        assert "GitHub Label:" in output
        assert "Summary:" in output

    def test_format_for_llm_no_pr(self) -> None:
        report = BranchStatusReport(
            branch_name="feature",
            base_branch="main",
            ci_status=CIStatus.NOT_CONFIGURED,
            ci_details=None,
            rebase_needed=False,
            rebase_reason="up-to-date",
            tasks_status=TaskTrackerStatus.N_A,
            tasks_reason="No tasks found",
            tasks_is_blocking=False,
            current_github_label="",
            recommendations=[],
        )
        output = report.format_for_llm()
        assert "PR=" not in output
        # Recommendations line is always present (may be empty)
        assert "Recommendations:" in output


class TestCreateEmptyReport:
    """Tests for create_empty_report."""

    def test_returns_defaults(self) -> None:
        report = create_empty_report()
        assert report.branch_name == "unknown"
        assert report.base_branch == "unknown"
        assert report.ci_status == CIStatus.NOT_CONFIGURED
        assert report.tasks_status == TaskTrackerStatus.N_A
        assert report.recommendations == []
        assert report.current_github_label == "unknown"
        assert report.rebase_reason == "Unknown"
        assert report.tasks_reason == "Unknown"


class TestGetFailedJobsSummary:
    """Tests for get_failed_jobs_summary."""

    def test_no_failed_jobs(self) -> None:
        jobs = [{"name": "test", "conclusion": "success", "steps": []}]
        result = get_failed_jobs_summary(jobs, {})
        assert result["job_name"] == ""
        assert result["step_name"] == ""
        assert result["step_number"] == 0
        assert result["log_excerpt"] == ""
        assert result["other_failed_jobs"] == []

    def test_with_failed_jobs(self) -> None:
        jobs = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"name": "Setup", "conclusion": "success"},
                    {"name": "Run tests", "conclusion": "failure", "number": 2},
                ],
            }
        ]
        result = get_failed_jobs_summary(jobs, {})
        assert result["job_name"] == "test"
        assert result["step_name"] == "Run tests"
        assert result["step_number"] == 2
        assert result["other_failed_jobs"] == []

    def test_multiple_failed_jobs(self) -> None:
        jobs: list[dict[str, object]] = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"name": "Run tests", "conclusion": "failure", "number": 1},
                ],
            },
            {
                "name": "lint",
                "conclusion": "failure",
                "steps": [],
            },
        ]
        result = get_failed_jobs_summary(jobs, {})
        assert result["job_name"] == "test"
        assert result["other_failed_jobs"] == ["lint"]

    def test_with_log_content(self) -> None:
        jobs = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"name": "Run tests", "conclusion": "failure", "number": 1},
                ],
            },
        ]
        log_text = (
            "##[group]Run tests\n"
            "FAILED test_example.py\n"
            "##[error]Process completed with exit code 1\n"
            "##[endgroup]\n"
        )
        logs = {"0_test.txt": log_text}
        result = get_failed_jobs_summary(jobs, logs)
        assert result["job_name"] == "test"
        assert result["log_excerpt"] is not None
        assert "FAILED" in result["log_excerpt"]


class TestCollectCIStatus:
    """Tests for _collect_ci_status."""

    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_passed(self, mock_ci_cls: MagicMock) -> None:
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {
            "run": {"conclusion": "success", "status": "completed"},
            "jobs": [],
        }
        mock_ci_cls.return_value = mock_ci
        status, details = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.PASSED
        assert details is None

    @patch("mcp_workspace.checks.branch_status.build_ci_error_details")
    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_failed(self, mock_ci_cls: MagicMock, mock_build: MagicMock) -> None:
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {
            "run": {"conclusion": "failure", "status": "completed"},
            "jobs": [],
        }
        mock_ci_cls.return_value = mock_ci
        mock_build.return_value = "error details"
        status, details = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.FAILED
        assert details == "error details"

    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_pending(self, mock_ci_cls: MagicMock) -> None:
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {
            "run": {"conclusion": None, "status": "in_progress"},
            "jobs": [],
        }
        mock_ci_cls.return_value = mock_ci
        status, details = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.PENDING

    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_not_configured(self, mock_ci_cls: MagicMock) -> None:
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
        mock_ci_cls.return_value = mock_ci
        status, _ = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.NOT_CONFIGURED

    @patch("mcp_workspace.checks.branch_status.build_ci_error_details")
    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_failed_with_details_exception(
        self, mock_ci_cls: MagicMock, mock_build: MagicMock
    ) -> None:
        """build_ci_error_details raising still returns FAILED, not NOT_CONFIGURED."""
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {
            "run": {"conclusion": "failure", "status": "completed"},
            "jobs": [],
        }
        mock_ci_cls.return_value = mock_ci
        mock_build.side_effect = Exception("log fetch failed")
        status, details = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.FAILED
        assert details is None

    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_pending_via_status_fallback(self, mock_ci_cls: MagicMock) -> None:
        """conclusion=None, status='in_progress' should return PENDING."""
        mock_ci = MagicMock()
        mock_ci.get_latest_ci_status.return_value = {
            "run": {"conclusion": None, "status": "in_progress"},
            "jobs": [],
        }
        mock_ci_cls.return_value = mock_ci
        status, details = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.PENDING
        assert details is None

    @patch("mcp_workspace.checks.branch_status.CIResultsManager")
    def test_exception_returns_not_configured(self, mock_ci_cls: MagicMock) -> None:
        mock_ci_cls.side_effect = Exception("fail")
        status, _ = _collect_ci_status(Path("/tmp"), "main", 300)
        assert status == CIStatus.NOT_CONFIGURED


class TestCollectRebaseStatus:
    """Tests for _collect_rebase_status."""

    @patch("mcp_workspace.checks.branch_status.needs_rebase")
    def test_up_to_date(self, mock_rebase: MagicMock) -> None:
        mock_rebase.return_value = (False, "up-to-date")
        needed, reason = _collect_rebase_status(Path("/tmp"), "main")
        assert not needed
        assert reason == "up-to-date"

    @patch("mcp_workspace.checks.branch_status.needs_rebase")
    def test_needs_rebase(self, mock_rebase: MagicMock) -> None:
        mock_rebase.return_value = (True, "3 commits behind")
        needed, reason = _collect_rebase_status(Path("/tmp"), "main")
        assert needed
        assert "3 commits" in reason

    @patch("mcp_workspace.checks.branch_status.needs_rebase")
    def test_exception(self, mock_rebase: MagicMock) -> None:
        mock_rebase.side_effect = Exception("fail")
        needed, reason = _collect_rebase_status(Path("/tmp"), "main")
        assert not needed
        assert "Error checking rebase status" in reason
        assert "fail" in reason


class TestCollectTaskStatus:
    """Tests for _collect_task_status."""

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_complete(self, mock_counts: MagicMock, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        steps_dir = pr_info / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_1.md").write_text("step")
        mock_counts.return_value = (5, 5)
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.COMPLETE
        assert not blocking

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_incomplete(self, mock_counts: MagicMock, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        steps_dir = pr_info / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_1.md").write_text("step")
        mock_counts.return_value = (5, 3)
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.INCOMPLETE
        assert blocking
        assert "3 of 5" in reason

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_no_tasks_is_blocking(self, mock_counts: MagicMock, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        steps_dir = pr_info / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_1.md").write_text("step")
        mock_counts.return_value = (0, 0)
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.N_A
        assert blocking
        assert reason == "Task tracker is empty"

    def test_no_pr_info_dir(self, tmp_path: Path) -> None:
        """Missing pr_info directory returns N_A without calling get_task_counts."""
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.N_A
        assert not blocking
        assert "No pr_info" in reason

    def test_no_steps_files_returns_early(self, tmp_path: Path) -> None:
        """pr_info exists but no steps files -> early return N_A."""
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.N_A
        assert not blocking
        assert "No implementation plan found" in reason

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_file_not_found_with_steps(
        self, mock_counts: MagicMock, tmp_path: Path
    ) -> None:
        """Steps files exist but no tracker -> blocking."""
        from mcp_workspace.workflows.task_tracker import (
            TaskTrackerFileNotFoundError,
        )

        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        steps_dir = pr_info / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_1.md").write_text("step")
        mock_counts.side_effect = TaskTrackerFileNotFoundError("not found")
        status, reason, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.N_A
        assert blocking
        assert "TASK_TRACKER.md" in reason

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_general_exception_is_blocking(
        self, mock_counts: MagicMock, tmp_path: Path
    ) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        steps_dir = pr_info / "steps"
        steps_dir.mkdir()
        (steps_dir / "step_1.md").write_text("step")
        mock_counts.side_effect = RuntimeError("unexpected")
        status, _, blocking = _collect_task_status(tmp_path)
        assert status == TaskTrackerStatus.ERROR
        assert blocking


class TestCollectGithubLabel:
    """Tests for _collect_github_label."""

    def test_with_status_label(self) -> None:
        issue_data: IssueData = {
            "number": 1,
            "title": "test",
            "body": "",
            "state": "open",
            "labels": ["bug", "status-04:in-progress"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        assert _collect_github_label(issue_data) == "status-04:in-progress"

    def test_no_status_label(self) -> None:
        issue_data: IssueData = {
            "number": 1,
            "title": "test",
            "body": "",
            "state": "open",
            "labels": ["bug", "enhancement"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        assert _collect_github_label(issue_data) == "unknown"

    def test_none_issue_data(self) -> None:
        assert _collect_github_label(None) == "unknown"


class TestCollectPRInfo:
    """Tests for _collect_pr_info."""

    def test_pr_found(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = [
            {
                "number": 45,
                "url": "https://github.com/owner/repo/pull/45",
                "mergeable": True,
            }
        ]
        number, url, found, mergeable = _collect_pr_info(mock_pr, "feature")
        assert number == 45
        assert found is True
        assert mergeable is True

    def test_no_pr(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = []
        number, url, found, mergeable = _collect_pr_info(mock_pr, "feature")
        assert number is None
        assert found is False
        assert mergeable is None

    def test_exception(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.side_effect = Exception("fail")
        number, url, found, mergeable = _collect_pr_info(mock_pr, "feature")
        assert found is None
        assert mergeable is None

    def test_pr_found_mergeable_none(self) -> None:
        """PR exists but mergeable is None."""
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = [
            {
                "number": 45,
                "url": "https://github.com/owner/repo/pull/45",
                "mergeable": None,
            }
        ]
        number, url, found, mergeable = _collect_pr_info(mock_pr, "feature")
        assert number == 45
        assert found is True
        assert mergeable is None

    def test_pr_found_mergeable_false(self) -> None:
        """PR exists but mergeable is False."""
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = [
            {
                "number": 45,
                "url": "https://github.com/owner/repo/pull/45",
                "mergeable": False,
            }
        ]
        number, url, found, mergeable = _collect_pr_info(mock_pr, "feature")
        assert number == 45
        assert found is True
        assert mergeable is False


class TestGenerateRecommendations:
    """Tests for _generate_recommendations."""

    def test_all_good(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Ready to merge" in recs

    def test_all_good_na_tasks(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.N_A,
                "tasks_reason": "No tasks",
                "tasks_is_blocking": False,
            }
        )
        assert "Ready to merge" in recs

    def test_ci_failed(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.FAILED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Fix CI test failures" in recs

    def test_ci_failed_with_details(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.FAILED,
                "ci_details": "Some error log",
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Check CI error details above" in recs

    def test_not_configured(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.NOT_CONFIGURED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Configure CI pipeline" in recs

    def test_rebase_needed(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": True,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Rebase onto origin/main" in recs

    def test_rebase_needed_but_tasks_blocking(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": True,
                "tasks_status": TaskTrackerStatus.INCOMPLETE,
                "tasks_reason": "2 of 5",
                "tasks_is_blocking": True,
            }
        )
        assert not any("Rebase" in r for r in recs)
        assert any("remaining tasks" in r.lower() for r in recs)

    def test_tasks_incomplete(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.INCOMPLETE,
                "tasks_reason": "3 of 5 tasks complete",
                "tasks_is_blocking": True,
            }
        )
        assert any("remaining tasks" in r.lower() for r in recs)

    def test_ready_to_merge_squash_merge_safe(self) -> None:
        """When pr_mergeable=True and ready, recommend squash-merge safe."""
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
                "pr_mergeable": True,
            }
        )
        assert "Ready to merge (squash-merge safe)" in recs

    def test_ready_to_merge_without_mergeable(self) -> None:
        """When pr_mergeable is not True, recommend plain Ready to merge."""
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
                "pr_mergeable": None,
            }
        )
        assert "Ready to merge" in recs
        assert "Ready to merge (squash-merge safe)" not in recs

    def test_rebase_suppressed_when_ci_failed(self) -> None:
        """Rebase recommendation is suppressed when CI is failed."""
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.FAILED,
                "rebase_needed": True,
                "tasks_status": TaskTrackerStatus.COMPLETE,
                "tasks_reason": "All done",
                "tasks_is_blocking": False,
            }
        )
        assert "Fix CI test failures" in recs
        assert not any("Rebase" in r for r in recs)

    def test_na_blocking_recommends_fix_tracker(self) -> None:
        """N_A + blocking recommends fixing tracker."""
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.PASSED,
                "rebase_needed": False,
                "tasks_status": TaskTrackerStatus.N_A,
                "tasks_reason": "Task tracker is empty",
                "tasks_is_blocking": True,
            }
        )
        assert any("Fix task tracker" in r for r in recs)
        assert "Task tracker is empty" in recs[0] or any(
            "Task tracker is empty" in r for r in recs
        )

    def test_multiple_issues(self) -> None:
        recs = _generate_recommendations(
            {
                "ci_status": CIStatus.FAILED,
                "rebase_needed": True,
                "tasks_status": TaskTrackerStatus.INCOMPLETE,
                "tasks_reason": "3 of 5",
                "tasks_is_blocking": False,
            }
        )
        # CI failed + incomplete tasks; rebase suppressed because CI failed
        assert "Fix CI test failures" in recs
        assert any("remaining tasks" in r.lower() for r in recs)


class TestApplyPrMergeOverride:
    """Tests for _apply_pr_merge_override."""

    def test_rebase_not_needed_passthrough(self) -> None:
        """When rebase is not needed, return unchanged (no override needed)."""
        result = _apply_pr_merge_override(
            rebase_needed=False,
            rebase_reason="up-to-date",
            pr_mergeable=True,
        )
        assert result == (False, "up-to-date")

    def test_rebase_needed_and_mergeable_overrides(self) -> None:
        """When rebase needed but PR is mergeable, override to not needed."""
        result = _apply_pr_merge_override(
            rebase_needed=True,
            rebase_reason="3 commits behind",
            pr_mergeable=True,
        )
        assert result == (
            False,
            "Behind base branch but PR is mergeable (squash-merge safe)",
        )

    def test_rebase_needed_and_not_mergeable_unchanged(self) -> None:
        """When rebase needed and PR is not mergeable, keep original."""
        result = _apply_pr_merge_override(
            rebase_needed=True,
            rebase_reason="3 commits behind",
            pr_mergeable=False,
        )
        assert result == (True, "3 commits behind")

    def test_rebase_needed_and_mergeable_none_unchanged(self) -> None:
        """When rebase needed and mergeable is None, keep original."""
        result = _apply_pr_merge_override(
            rebase_needed=True,
            rebase_reason="3 commits behind",
            pr_mergeable=None,
        )
        assert result == (True, "3 commits behind")


class TestCollectBranchStatus:
    """Tests for collect_branch_status."""

    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    def test_no_branch_returns_empty(self, mock_branch: MagicMock) -> None:
        mock_branch.return_value = None
        report = collect_branch_status(Path("/tmp"))
        assert report.branch_name == "unknown"

    @patch("mcp_workspace.checks.branch_status._collect_pr_info")
    @patch("mcp_workspace.checks.branch_status._collect_github_label")
    @patch("mcp_workspace.checks.branch_status._collect_task_status")
    @patch("mcp_workspace.checks.branch_status._collect_rebase_status")
    @patch("mcp_workspace.checks.branch_status._collect_ci_status")
    @patch("mcp_workspace.checks.branch_status.detect_base_branch")
    @patch("mcp_workspace.checks.branch_status.PullRequestManager")
    @patch("mcp_workspace.checks.branch_status.IssueManager")
    @patch("mcp_workspace.checks.branch_status.extract_issue_number_from_branch")
    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    def test_full_collection(
        self,
        mock_branch: MagicMock,
        mock_extract: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        mock_pr_mgr_cls: MagicMock,
        mock_detect: MagicMock,
        mock_ci: MagicMock,
        mock_rebase: MagicMock,
        mock_tasks: MagicMock,
        mock_label: MagicMock,
        mock_pr_info: MagicMock,
    ) -> None:
        mock_branch.return_value = "123-feature"
        mock_extract.return_value = 123
        mock_issue_mgr = MagicMock()
        mock_issue_mgr.get_issue.return_value = {
            "number": 123,
            "labels": ["status-04:in-progress"],
        }
        mock_issue_mgr_cls.return_value = mock_issue_mgr
        mock_pr_mgr_cls.return_value = MagicMock()
        mock_detect.return_value = "main"
        mock_ci.return_value = (CIStatus.PASSED, None)
        mock_rebase.return_value = (False, "up-to-date")
        mock_tasks.return_value = (
            TaskTrackerStatus.COMPLETE,
            "All 5 tasks complete",
            False,
        )
        mock_label.return_value = "status-04:in-progress"
        mock_pr_info.return_value = (45, "https://url", True, True)

        report = collect_branch_status(Path("/tmp"))
        assert report.branch_name == "123-feature"
        assert report.base_branch == "main"
        assert report.ci_status == CIStatus.PASSED
        assert report.pr_number == 45
        assert report.pr_mergeable is True

    @patch("mcp_workspace.checks.branch_status.detect_base_branch")
    @patch("mcp_workspace.checks.branch_status.PullRequestManager")
    @patch("mcp_workspace.checks.branch_status.IssueManager")
    @patch("mcp_workspace.checks.branch_status.extract_issue_number_from_branch")
    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    def test_github_init_failure(
        self,
        mock_branch: MagicMock,
        mock_extract: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        mock_pr_mgr_cls: MagicMock,
        mock_detect: MagicMock,
    ) -> None:
        """Test that GitHub manager failures are handled gracefully."""
        mock_branch.return_value = "feature"
        mock_extract.return_value = None
        mock_issue_mgr_cls.side_effect = Exception("no token")
        mock_detect.return_value = "main"

        with (
            patch("mcp_workspace.checks.branch_status._collect_ci_status") as mock_ci,
            patch(
                "mcp_workspace.checks.branch_status._collect_rebase_status"
            ) as mock_rebase,
            patch(
                "mcp_workspace.checks.branch_status._collect_task_status"
            ) as mock_tasks,
        ):
            mock_ci.return_value = (CIStatus.NOT_CONFIGURED, None)
            mock_rebase.return_value = (False, "up-to-date")
            mock_tasks.return_value = (TaskTrackerStatus.N_A, "N/A", False)

            report = collect_branch_status(Path("/tmp"))
            assert report.branch_name == "feature"
            # pr_manager is None when init fails, so pr fields should be None
            assert report.pr_found is None
            assert report.pr_mergeable is None

    @patch("mcp_workspace.checks.branch_status._collect_pr_info")
    @patch("mcp_workspace.checks.branch_status._collect_github_label")
    @patch("mcp_workspace.checks.branch_status._collect_task_status")
    @patch("mcp_workspace.checks.branch_status._collect_rebase_status")
    @patch("mcp_workspace.checks.branch_status._collect_ci_status")
    @patch("mcp_workspace.checks.branch_status.detect_base_branch")
    @patch("mcp_workspace.checks.branch_status.PullRequestManager")
    @patch("mcp_workspace.checks.branch_status.IssueManager")
    @patch("mcp_workspace.checks.branch_status.extract_issue_number_from_branch")
    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    def test_rebase_behind_but_mergeable_squash_safe(
        self,
        mock_branch: MagicMock,
        mock_extract: MagicMock,
        mock_issue_mgr_cls: MagicMock,
        mock_pr_mgr_cls: MagicMock,
        mock_detect: MagicMock,
        mock_ci: MagicMock,
        mock_rebase: MagicMock,
        mock_tasks: MagicMock,
        mock_label: MagicMock,
        mock_pr_info: MagicMock,
    ) -> None:
        """Rebase behind + mergeable=True → override + squash-merge safe recommendation."""
        mock_branch.return_value = "123-feature"
        mock_extract.return_value = 123
        mock_issue_mgr = MagicMock()
        mock_issue_mgr.get_issue.return_value = {"number": 123, "labels": []}
        mock_issue_mgr_cls.return_value = mock_issue_mgr
        mock_pr_mgr_cls.return_value = MagicMock()
        mock_detect.return_value = "main"
        mock_ci.return_value = (CIStatus.PASSED, None)
        mock_rebase.return_value = (True, "3 commits behind")
        mock_tasks.return_value = (
            TaskTrackerStatus.COMPLETE,
            "All tasks complete",
            False,
        )
        mock_label.return_value = "unknown"
        mock_pr_info.return_value = (45, "https://url", True, True)

        report = collect_branch_status(Path("/tmp"))
        assert report.rebase_needed is False
        assert "squash-merge safe" in report.rebase_reason
        assert report.pr_mergeable is True
        assert any("squash-merge safe" in r for r in report.recommendations)

    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    def test_unexpected_exception_returns_empty_report(
        self, mock_branch: MagicMock
    ) -> None:
        """Outer try/except catches unexpected exceptions."""
        mock_branch.side_effect = RuntimeError("totally unexpected")
        report = collect_branch_status(Path("/tmp"))
        assert report.branch_name == "unknown"
        assert report.base_branch == "unknown"
        assert report.rebase_reason == "Unknown"
        assert report.tasks_reason == "Unknown"
        assert report.recommendations == []
