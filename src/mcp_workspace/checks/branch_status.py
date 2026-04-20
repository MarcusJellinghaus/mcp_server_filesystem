"""Branch status check — comprehensive branch readiness report.

Collects CI status, rebase status, task tracker progress, and GitHub
labels into a single BranchStatusReport dataclass. Used by the
check_branch_status MCP tool.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from mcp_workspace.git_operations.base_branch import detect_base_branch
from mcp_workspace.git_operations.branch_queries import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_workspace.git_operations.workflows import needs_rebase
from mcp_workspace.github_operations.ci_log_parser import (
    _build_ci_error_details,
    truncate_ci_details,
)
from mcp_workspace.github_operations.ci_results_manager import CIResultsManager
from mcp_workspace.github_operations.issues import IssueData, IssueManager
from mcp_workspace.github_operations.pr_manager import PullRequestManager
from mcp_workspace.workflows.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    TaskTrackerStatus,
    get_task_counts,
)

logger = logging.getLogger(__name__)


class CIStatus(str, Enum):
    """CI pipeline status."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PENDING = "PENDING"


@dataclass(frozen=True)
class BranchStatusReport:
    """Branch readiness status report."""

    branch_name: str
    base_branch: str
    ci_status: CIStatus
    ci_details: Optional[str]
    rebase_needed: bool
    rebase_reason: str
    tasks_status: TaskTrackerStatus
    tasks_reason: str
    tasks_is_blocking: bool
    current_github_label: str
    recommendations: List[str]
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_found: Optional[bool] = None

    def format_for_human(self) -> str:
        """Format report for human-readable terminal output."""
        lines: List[str] = []
        lines.append(f"Branch: {self.branch_name}")
        lines.append(f"Base: {self.base_branch}")
        lines.append(f"CI: {self.ci_status.value}")
        if self.ci_details:
            lines.append(f"CI Details:\n{self.ci_details}")
        lines.append(f"Rebase needed: {self.rebase_needed} ({self.rebase_reason})")
        lines.append(
            f"Tasks: {self.tasks_status.value} ({self.tasks_reason})"
        )
        lines.append(f"Label: {self.current_github_label}")
        if self.pr_found:
            lines.append(f"PR: #{self.pr_number} ({self.pr_url})")
        if self.recommendations:
            lines.append("Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  - {rec}")
        return "\n".join(lines)

    def format_for_llm(self, max_lines: int = 300) -> str:
        """Format report for LLM context window consumption."""
        lines: List[str] = []
        lines.append("## Branch Status Report")
        lines.append(f"- **Branch**: `{self.branch_name}`")
        lines.append(f"- **Base**: `{self.base_branch}`")
        lines.append(f"- **CI**: {self.ci_status.value}")
        lines.append(
            f"- **Rebase**: {'NEEDED' if self.rebase_needed else 'OK'}"
            f" — {self.rebase_reason}"
        )
        lines.append(
            f"- **Tasks**: {self.tasks_status.value} — {self.tasks_reason}"
        )
        lines.append(f"- **Label**: {self.current_github_label}")

        if self.pr_found:
            lines.append(f"- **PR**: #{self.pr_number} ({self.pr_url})")

        if self.recommendations:
            lines.append("")
            lines.append("### Recommendations")
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        if self.ci_details:
            lines.append("")
            lines.append("### CI Details")
            lines.append(self.ci_details)

        result = "\n".join(lines)
        return truncate_ci_details(result, max_lines=max_lines)


def create_empty_report() -> BranchStatusReport:
    """Create an empty/default report for error cases."""
    return BranchStatusReport(
        branch_name="unknown",
        base_branch="main",
        ci_status=CIStatus.NOT_CONFIGURED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="unknown",
        tasks_status=TaskTrackerStatus.N_A,
        tasks_reason="unknown",
        tasks_is_blocking=False,
        current_github_label="",
        recommendations=[],
    )


def get_failed_jobs_summary(
    jobs: Sequence[Mapping[str, Any]], logs: Mapping[str, str]
) -> Dict[str, Any]:
    """Summarize failed jobs from CI results.

    Args:
        jobs: List of job data dictionaries from CI status.
        logs: Dictionary mapping log filenames to contents.

    Returns:
        Dictionary with failed job names and log excerpts.
    """
    failed = [j for j in jobs if j.get("conclusion") == "failure"]
    summary: Dict[str, Any] = {
        "failed_count": len(failed),
        "failed_jobs": [],
    }
    for job in failed:
        job_name = str(job.get("name", "unknown"))
        job_info: Dict[str, Any] = {"name": job_name, "steps": []}
        raw_steps = job.get("steps", [])
        steps: Sequence[Mapping[str, Any]] = list(raw_steps) if raw_steps else []
        failed_steps = [s for s in steps if s.get("conclusion") == "failure"]
        for step in failed_steps:
            job_info["steps"].append(str(step.get("name", "unknown")))
        summary["failed_jobs"].append(job_info)
    return summary


def _collect_ci_status(
    project_dir: Path, branch_name: str, max_log_lines: int
) -> tuple[CIStatus, Optional[str]]:
    """Collect CI status and details.

    Returns:
        Tuple of (CIStatus, optional details string).
    """
    try:
        ci_manager = CIResultsManager(project_dir=project_dir)
        status_result = ci_manager.get_latest_ci_status(branch_name)
        run_data = status_result.get("run")

        if run_data is None or len(run_data) == 0:
            return CIStatus.NOT_CONFIGURED, None

        conclusion = run_data.get("conclusion")
        status = run_data.get("status", "")

        if conclusion == "success":
            return CIStatus.PASSED, None
        elif conclusion == "failure":
            details = _build_ci_error_details(
                ci_manager, status_result, max_lines=max_log_lines
            )
            return CIStatus.FAILED, details
        elif status in ("in_progress", "queued", "pending"):
            return CIStatus.PENDING, None
        else:
            return CIStatus.NOT_CONFIGURED, None

    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("CI status collection failed", exc_info=True)
        return CIStatus.NOT_CONFIGURED, None


def _collect_rebase_status(
    project_dir: Path, base_branch: str
) -> tuple[bool, str]:
    """Collect rebase status.

    Returns:
        Tuple of (needs_rebase, reason).
    """
    try:
        rebase_needed, reason = needs_rebase(project_dir, target_branch=base_branch)
        return rebase_needed, reason
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Rebase check failed", exc_info=True)
        return False, "error: rebase check failed"


def _collect_task_status(
    project_dir: Path,
) -> tuple[TaskTrackerStatus, str, bool]:
    """Collect task tracker status.

    Returns:
        Tuple of (status, reason, is_blocking).
    """
    try:
        pr_info_path = str(project_dir / "pr_info")
        total, completed = get_task_counts(pr_info_path)
        if total == 0:
            return TaskTrackerStatus.N_A, "No tasks found", False
        if completed >= total:
            return (
                TaskTrackerStatus.COMPLETE,
                f"All {total} tasks complete",
                False,
            )
        return (
            TaskTrackerStatus.INCOMPLETE,
            f"{completed} of {total} tasks complete",
            True,
        )
    except TaskTrackerFileNotFoundError:
        return TaskTrackerStatus.N_A, "No task tracker file", False
    except TaskTrackerSectionNotFoundError:
        return TaskTrackerStatus.N_A, "No tasks section in tracker", False
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Task tracker check failed", exc_info=True)
        return TaskTrackerStatus.ERROR, "Task tracker check failed", False


def _collect_github_label(issue_data: Optional[IssueData]) -> str:
    """Extract the current status label from issue data.

    Returns:
        Current status label string, or empty string if not found.
    """
    if issue_data is None:
        return ""
    labels = issue_data.get("labels", [])
    for label in labels:
        if isinstance(label, str) and label.startswith("status-"):
            return label
    return ""


def _collect_pr_info(
    pr_manager: PullRequestManager, branch_name: str
) -> tuple[Optional[int], Optional[str], Optional[bool]]:
    """Collect PR info for the branch.

    Returns:
        Tuple of (pr_number, pr_url, pr_found).
    """
    try:
        prs = pr_manager.find_pull_request_by_head(branch_name)
        if prs:
            pr = prs[0]
            return pr.get("number"), pr.get("url"), True
        return None, None, False
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("PR lookup failed", exc_info=True)
        return None, None, None


def _generate_recommendations(
    ci_status: CIStatus,
    rebase_needed: bool,
    tasks_status: TaskTrackerStatus,
    tasks_reason: str,
) -> List[str]:
    """Generate actionable recommendations based on status."""
    recs: List[str] = []
    if ci_status == CIStatus.FAILED:
        recs.append("Fix CI failures before merging")
    if ci_status == CIStatus.PENDING:
        recs.append("Wait for CI to complete")
    if rebase_needed:
        recs.append("Rebase onto base branch")
    if tasks_status == TaskTrackerStatus.INCOMPLETE:
        recs.append(f"Complete remaining tasks ({tasks_reason})")
    if tasks_status == TaskTrackerStatus.ERROR:
        recs.append("Fix task tracker errors")
    return recs


def collect_branch_status(
    project_dir: Path, max_log_lines: int = 300
) -> BranchStatusReport:
    """Collect comprehensive branch status from all sources.

    Args:
        project_dir: Path to the project directory.
        max_log_lines: Maximum CI log lines to include.

    Returns:
        A BranchStatusReport dataclass (not a dict).
    """
    # 1. Get current branch
    branch_name = get_current_branch_name(project_dir)
    if branch_name is None:
        logger.warning("Could not detect current branch")
        return create_empty_report()

    # 2. Fetch issue data once for sharing
    issue_data: Optional[IssueData] = None
    issue_manager: Optional[IssueManager] = None
    pr_manager: Optional[PullRequestManager] = None

    try:
        issue_manager = IssueManager(project_dir=project_dir)
        pr_manager = PullRequestManager(project_dir)
        issue_number = extract_issue_number_from_branch(branch_name)
        if issue_number is not None and issue_manager is not None:
            try:
                fetched = issue_manager.get_issue(issue_number)
                if fetched and fetched.get("number", 0) > 0:
                    issue_data = fetched
            except Exception:  # pylint: disable=broad-exception-caught
                logger.debug("Failed to fetch issue data", exc_info=True)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("GitHub manager initialization failed", exc_info=True)

    # 3. Detect base branch (DI: pass managers)
    base_branch_result = detect_base_branch(
        project_dir,
        current_branch=branch_name,
        issue_data=issue_data,
        issue_manager=issue_manager,
        pr_manager=pr_manager,
    )
    base_branch = base_branch_result if base_branch_result else "main"

    # 4. Collect CI status
    ci_status, ci_details = _collect_ci_status(
        project_dir, branch_name, max_log_lines
    )

    # 5. Check rebase status
    rebase_needed, rebase_reason = _collect_rebase_status(project_dir, base_branch)

    # 6. Check task tracker
    tasks_status, tasks_reason, tasks_is_blocking = _collect_task_status(project_dir)

    # 7. Collect GitHub label
    current_github_label = _collect_github_label(issue_data)

    # 8. Collect PR info
    pr_number, pr_url, pr_found = _collect_pr_info(
        pr_manager, branch_name
    ) if pr_manager else (None, None, None)

    # 9. Generate recommendations
    recommendations = _generate_recommendations(
        ci_status, rebase_needed, tasks_status, tasks_reason
    )

    return BranchStatusReport(
        branch_name=branch_name,
        base_branch=base_branch,
        ci_status=ci_status,
        ci_details=ci_details,
        rebase_needed=rebase_needed,
        rebase_reason=rebase_reason,
        tasks_status=tasks_status,
        tasks_reason=tasks_reason,
        tasks_is_blocking=tasks_is_blocking,
        current_github_label=current_github_label,
        recommendations=recommendations,
        pr_number=pr_number,
        pr_url=pr_url,
        pr_found=pr_found,
    )
