"""CI log parser for GitHub Actions workflow logs.

This module parses GitHub Actions log output to extract relevant failure
information. It provides utilities for stripping timestamps, parsing log
groups, extracting failed step logs, and building CI error detail reports.
"""

import logging
import re
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from mcp_workspace.github_operations.ci_results_manager import CIResultsManager

logger = logging.getLogger(__name__)

_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")

__all__ = [
    "build_ci_error_details",
    "truncate_ci_details",
]


def truncate_ci_details(
    details: str, max_lines: int = 300, head_lines: int = 10
) -> str:
    """Truncate CI details with head + tail preservation.

    If the details exceed max_lines, keeps the first head_lines and
    the last (max_lines - head_lines) lines, inserting a truncation marker.

    Args:
        details: The CI details string to potentially truncate.
        max_lines: Maximum number of lines to keep (default 300).
        head_lines: Number of lines to keep from the start (default 10).

    Returns:
        The original string if within limits, or a truncated version
        with head + tail preservation and a marker showing skipped lines.
    """
    if not details:
        return ""

    lines = details.split("\n")
    if len(lines) <= max_lines:
        return details

    tail_lines = max_lines - head_lines
    head = lines[:head_lines]
    tail = lines[-tail_lines:]
    truncated_count = len(lines) - head_lines - tail_lines

    return "\n".join(head + [f"[... truncated {truncated_count} lines ...]"] + tail)


def _strip_timestamps(log_content: str) -> str:
    """Strip GitHub Actions timestamps from log lines.

    GitHub Actions log lines are prefixed with timestamps like:
    2024-01-15T10:30:45.1234567Z <actual content>

    Args:
        log_content: Raw log content with timestamps.

    Returns:
        Log content with timestamps stripped from each line.
    """
    lines = log_content.split("\n")
    stripped = [_TIMESTAMP_PATTERN.sub("", line) for line in lines]
    return "\n".join(stripped)


def _parse_groups(log_content: str) -> List[Tuple[str, List[str]]]:
    """Parse GitHub Actions log groups from log content.

    GitHub Actions uses ::group:: and ::endgroup:: markers to create
    collapsible sections in logs.

    Args:
        log_content: Log content potentially containing group markers.

    Returns:
        List of (group_name, lines) tuples. Lines outside groups are
        collected under an empty group name.
    """
    groups: List[Tuple[str, List[str]]] = []
    current_group: Optional[str] = None
    current_lines: List[str] = []

    for line in log_content.split("\n"):
        if line.startswith("##[group]"):
            # Save previous group if it has content
            if current_lines and current_group is not None:
                groups.append((current_group, current_lines))
            elif current_lines and groups:
                # Attach to preceding group
                groups[-1] = (groups[-1][0], groups[-1][1] + current_lines)
            # Start new group - extract name after ##[group]
            current_group = line.split("##[group]", 1)[1].strip()
            current_lines = []
        elif line.startswith("##[endgroup]"):
            # End current group
            if current_group is not None:
                groups.append((current_group, current_lines))
            current_group = None
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget remaining lines - attach to preceding group
    if current_lines:
        if current_group is not None:
            groups.append((current_group, current_lines))
        elif groups:
            groups[-1] = (groups[-1][0], groups[-1][1] + current_lines)

    return groups


def _extract_failed_step_log(log_content: str, step_name: str) -> str:
    """Extract log content for a specific failed step.

    Searches through log groups for a section matching the step name
    using 3-tier matching: exact → prefix → contains. Falls back to
    groups containing ##[error] lines when no name match is found.

    Args:
        log_content: Full log content for a job.
        step_name: Name of the failed step to extract.

    Returns:
        Log content for the matching step, error group content as fallback,
        or empty string if no matches found.
    """
    groups = _parse_groups(log_content)

    if step_name and step_name.lower() != "unknown":
        step_lower = step_name.lower()

        # Tier 1: Exact match
        for group_name, lines in groups:
            if group_name.lower() == step_lower:
                return "\n".join(lines)

        # Tier 2: Prefix match
        for group_name, lines in groups:
            if group_name.lower().startswith(step_lower):
                return "\n".join(lines)

        # Tier 3: Contains match
        for group_name, lines in groups:
            if step_lower in group_name.lower():
                return "\n".join(lines)

    # Fallback: collect entire group sections containing ##[error] lines
    error_groups: List[str] = []
    for _group_name, lines in groups:
        if any("##[error]" in line for line in lines):
            error_groups.append("\n".join(lines))

    if error_groups:
        return "\n".join(error_groups)

    return ""


def _find_log_content(
    logs: Mapping[str, str],
    job_name: str,
    step_number: int,
    step_name: str,
) -> str:
    """Find log content for a specific job and step from downloaded logs.

    GitHub Actions log files are organized by job name in the ZIP archive.
    File names typically follow the pattern: "job_name/step_number_step_name.txt"

    Args:
        logs: Dictionary mapping log filenames to their contents.
        job_name: Name of the job to find logs for.
        step_number: Step number within the job.
        step_name: Name of the step.

    Returns:
        Log content for the matching job/step, or empty string if not found.
    """
    if not logs:
        return ""

    # Tier 1: GitHub's _{job_name}.txt suffix matching (primary strategy)
    suffix = f"_{job_name}.txt"
    for filename, content in logs.items():
        if filename.endswith(suffix):
            return content

    # Tier 2: Try to find match by job name and step number
    for filename, content in logs.items():
        # Log files are like "job_name/1_Step Name.txt"
        if job_name.lower() in filename.lower():
            step_pattern = f"{step_number}_"
            if step_pattern in filename:
                return content

    # Tier 3: Try matching just by job name and step name
    for filename, content in logs.items():
        if job_name.lower() in filename.lower():
            if step_name.lower() in filename.lower():
                return content

    # Tier 4: Try matching just by job name - return all content for that job
    job_logs: List[str] = []
    for filename, content in logs.items():
        if job_name.lower() in filename.lower():
            job_logs.append(content)

    if job_logs:
        return "\n".join(job_logs)

    return ""


def build_ci_error_details(
    ci_manager: "CIResultsManager",
    status_result: Mapping[str, object],
    max_lines: int = 300,
) -> Optional[str]:
    """Build detailed CI error information from failed workflow runs.

    Always produces a report when there are failed jobs, even without log
    content (shows job names, step names, GitHub URLs with fallback text).

    Args:
        ci_manager: CIResultsManager instance for fetching logs.
        status_result: CI status data dict with 'run' and 'jobs' keys.
        max_lines: Maximum lines for the output (default 300).

    Returns:
        Structured multi-line string with failed job summaries and
        log excerpts, or None if no failed jobs.
    """
    jobs: Sequence[Mapping[str, object]] = status_result.get("jobs", [])  # type: ignore[assignment]
    if not jobs:
        return None

    # Find failed jobs
    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    if not failed_jobs:
        return None

    run_data: Mapping[str, object] = status_result.get("run", {})  # type: ignore[assignment]
    run_url = str(run_data.get("url", ""))
    jobs_fetch_warning = str(run_data.get("jobs_fetch_warning", ""))

    # Get unique run IDs from failed jobs (limit to 3)
    run_ids: List[int] = []
    seen_ids: set[int] = set()
    for job in failed_jobs:
        rid = job.get("run_id")
        if isinstance(rid, int) and rid not in seen_ids:
            seen_ids.add(rid)
            run_ids.append(rid)
        if len(run_ids) >= 3:
            break

    # Fetch logs for each run
    all_logs: Dict[str, str] = {}
    for run_id in run_ids:
        try:
            logs = ci_manager.get_run_logs(run_id)
            all_logs.update(logs)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to fetch logs for run %d", run_id)

    # Build summary header
    lines_used = 0
    output_parts: List[str] = []

    summary = f"## CI Failure Details\nRun: {run_url}"
    if jobs_fetch_warning:
        summary += f"\nWarning: {jobs_fetch_warning}"
    output_parts.append(summary)
    lines_used += summary.count("\n") + 1

    # Per-job line budget
    lines_per_job = max(10, (max_lines - lines_used) // max(len(failed_jobs), 1))

    shown_jobs = 0
    for job in failed_jobs:
        if lines_used >= max_lines:
            remaining = len(failed_jobs) - shown_jobs
            output_parts.append(f"\n[... truncated {remaining} more failed jobs ...]")
            break

        job_name = str(job.get("name", "unknown"))
        job_id = job.get("id", "")
        steps: Sequence[Mapping[str, object]] = job.get("steps", [])  # type: ignore[assignment]

        # Find the failed step
        failed_steps = [s for s in steps if s.get("conclusion") == "failure"]

        # Build job header with URL
        job_url = f"{run_url}/job/{job_id}" if run_url and job_id else ""
        header = f"### Failed Job: {job_name}"
        if job_url:
            header += f"\n{job_url}"
        output_parts.append(header)
        lines_used += header.count("\n") + 1

        if failed_steps:
            for step in failed_steps:
                step_name = str(step.get("name", "unknown"))
                step_number = int(str(step.get("number", 0)))

                output_parts.append(f"**Failed Step: {step_name}**")
                lines_used += 1

                log_content = _find_log_content(
                    all_logs, job_name, step_number, step_name
                )
                if log_content:
                    cleaned = _strip_timestamps(log_content)
                    extracted = _extract_failed_step_log(cleaned, step_name)
                    # Apply per-job line budget
                    log_lines = extracted.split("\n")
                    if len(log_lines) > lines_per_job:
                        extracted = "\n".join(log_lines[:lines_per_job])
                        extracted += (
                            f"\n[... truncated to {lines_per_job} lines ...]"
                        )
                    output_parts.append(extracted)
                    lines_used += extracted.count("\n") + 1
                else:
                    output_parts.append("(logs not available)")
                    lines_used += 1
        else:
            output_parts.append("(no failed steps identified)")
            lines_used += 1

        shown_jobs += 1

    result = "\n\n".join(output_parts)
    return truncate_ci_details(result, max_lines=max_lines)
