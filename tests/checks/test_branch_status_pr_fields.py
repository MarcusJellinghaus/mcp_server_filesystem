"""Tests for BranchStatusReport PR-related fields."""

from mcp_workspace.checks.branch_status import BranchStatusReport, CIStatus
from mcp_workspace.workflows.task_tracker import TaskTrackerStatus


def _make_report(
    pr_number: int | None = None,
    pr_url: str | None = None,
    pr_found: bool | None = None,
) -> BranchStatusReport:
    """Helper to create a report with specific PR fields."""
    return BranchStatusReport(
        branch_name="test-branch",
        base_branch="main",
        ci_status=CIStatus.PASSED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="up-to-date",
        tasks_status=TaskTrackerStatus.COMPLETE,
        tasks_reason="All done",
        tasks_is_blocking=False,
        current_github_label="",
        recommendations=[],
        pr_number=pr_number,
        pr_url=pr_url,
        pr_found=pr_found,
    )


class TestPRFieldDefaults:
    """Tests that PR fields default to None."""

    def test_defaults_are_none(self) -> None:
        report = _make_report()
        assert report.pr_number is None
        assert report.pr_url is None
        assert report.pr_found is None


class TestPRFieldsInHumanFormat:
    """Tests PR field rendering in human format."""

    def test_pr_found_shows_in_output(self) -> None:
        report = _make_report(
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            pr_found=True,
        )
        output = report.format_for_human()
        assert "PR: #42" in output

    def test_pr_not_found_shows_no_pr(self) -> None:
        report = _make_report(pr_found=False)
        output = report.format_for_human()
        assert "PR: No PR found" in output

    def test_pr_none_hides_pr_line(self) -> None:
        report = _make_report(pr_found=None)
        output = report.format_for_human()
        assert "PR:" not in output


class TestPRFieldsInLLMFormat:
    """Tests PR field rendering in LLM format."""

    def test_pr_found_shows_in_output(self) -> None:
        report = _make_report(
            pr_number=42,
            pr_url="https://github.com/owner/repo/pull/42",
            pr_found=True,
        )
        output = report.format_for_llm()
        assert "PR: #42" in output

    def test_pr_not_found_shows_no_pr(self) -> None:
        report = _make_report(pr_found=False)
        output = report.format_for_llm()
        assert "PR: No PR found" in output

    def test_pr_none_hides_pr_section(self) -> None:
        report = _make_report(pr_found=None)
        output = report.format_for_llm()
        assert "PR:" not in output
