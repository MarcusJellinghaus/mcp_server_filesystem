"""Tests for branch_status check module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_workspace.checks.branch_status import (
    BranchStatusReport,
    CIStatus,
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
        assert "Branch: 123-feature" in output
        assert "CI: PASSED" in output
        assert "PR: #45" in output
        assert "Do something" in output

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
        assert "## Branch Status Report" in output
        assert "FAILED" in output
        assert "NEEDED" in output
        assert "### Recommendations" in output
        assert "### CI Details" in output

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
        assert "**PR**" not in output
        assert "Recommendations" not in output


class TestCreateEmptyReport:
    """Tests for create_empty_report."""

    def test_returns_defaults(self) -> None:
        report = create_empty_report()
        assert report.branch_name == "unknown"
        assert report.base_branch == "main"
        assert report.ci_status == CIStatus.NOT_CONFIGURED
        assert report.tasks_status == TaskTrackerStatus.N_A
        assert report.recommendations == []


class TestGetFailedJobsSummary:
    """Tests for get_failed_jobs_summary."""

    def test_no_failed_jobs(self) -> None:
        jobs = [{"name": "test", "conclusion": "success", "steps": []}]
        result = get_failed_jobs_summary(jobs, {})
        assert result["failed_count"] == 0

    def test_with_failed_jobs(self) -> None:
        jobs = [
            {
                "name": "test",
                "conclusion": "failure",
                "steps": [
                    {"name": "Run tests", "conclusion": "failure"},
                    {"name": "Setup", "conclusion": "success"},
                ],
            }
        ]
        result = get_failed_jobs_summary(jobs, {})
        assert result["failed_count"] == 1
        assert result["failed_jobs"][0]["name"] == "test"
        assert "Run tests" in result["failed_jobs"][0]["steps"]


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

    @patch("mcp_workspace.checks.branch_status._build_ci_error_details")
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
        assert "error" in reason


class TestCollectTaskStatus:
    """Tests for _collect_task_status."""

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_complete(self, mock_counts: MagicMock) -> None:
        mock_counts.return_value = (5, 5)
        status, reason, blocking = _collect_task_status(Path("/tmp"))
        assert status == TaskTrackerStatus.COMPLETE
        assert not blocking

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_incomplete(self, mock_counts: MagicMock) -> None:
        mock_counts.return_value = (5, 3)
        status, reason, blocking = _collect_task_status(Path("/tmp"))
        assert status == TaskTrackerStatus.INCOMPLETE
        assert blocking
        assert "3 of 5" in reason

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_no_tasks(self, mock_counts: MagicMock) -> None:
        mock_counts.return_value = (0, 0)
        status, reason, blocking = _collect_task_status(Path("/tmp"))
        assert status == TaskTrackerStatus.N_A
        assert not blocking

    @patch("mcp_workspace.checks.branch_status.get_task_counts")
    def test_file_not_found(self, mock_counts: MagicMock) -> None:
        from mcp_workspace.workflows.task_tracker import (
            TaskTrackerFileNotFoundError,
        )

        mock_counts.side_effect = TaskTrackerFileNotFoundError("not found")
        status, _, blocking = _collect_task_status(Path("/tmp"))
        assert status == TaskTrackerStatus.N_A
        assert not blocking


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
        assert _collect_github_label(issue_data) == ""

    def test_none_issue_data(self) -> None:
        assert _collect_github_label(None) == ""


class TestCollectPRInfo:
    """Tests for _collect_pr_info."""

    def test_pr_found(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = [
            {"number": 45, "url": "https://github.com/owner/repo/pull/45"}
        ]
        number, url, found = _collect_pr_info(mock_pr, "feature")
        assert number == 45
        assert found is True

    def test_no_pr(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.return_value = []
        number, url, found = _collect_pr_info(mock_pr, "feature")
        assert number is None
        assert found is False

    def test_exception(self) -> None:
        mock_pr = MagicMock()
        mock_pr.find_pull_request_by_head.side_effect = Exception("fail")
        number, url, found = _collect_pr_info(mock_pr, "feature")
        assert found is None


class TestGenerateRecommendations:
    """Tests for _generate_recommendations."""

    def test_all_good(self) -> None:
        recs = _generate_recommendations(
            CIStatus.PASSED, False, TaskTrackerStatus.COMPLETE, "All done"
        )
        assert recs == []

    def test_ci_failed(self) -> None:
        recs = _generate_recommendations(
            CIStatus.FAILED, False, TaskTrackerStatus.COMPLETE, "All done"
        )
        assert any("CI" in r for r in recs)

    def test_rebase_needed(self) -> None:
        recs = _generate_recommendations(
            CIStatus.PASSED, True, TaskTrackerStatus.COMPLETE, "All done"
        )
        assert any("Rebase" in r for r in recs)

    def test_tasks_incomplete(self) -> None:
        recs = _generate_recommendations(
            CIStatus.PASSED,
            False,
            TaskTrackerStatus.INCOMPLETE,
            "3 of 5 tasks complete",
        )
        assert any("remaining tasks" in r.lower() for r in recs)

    def test_multiple_issues(self) -> None:
        recs = _generate_recommendations(
            CIStatus.FAILED,
            True,
            TaskTrackerStatus.INCOMPLETE,
            "3 of 5",
        )
        assert len(recs) == 3


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
        mock_pr_info.return_value = (45, "https://url", True)

        report = collect_branch_status(Path("/tmp"))
        assert report.branch_name == "123-feature"
        assert report.base_branch == "main"
        assert report.ci_status == CIStatus.PASSED
        assert report.pr_number == 45

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
