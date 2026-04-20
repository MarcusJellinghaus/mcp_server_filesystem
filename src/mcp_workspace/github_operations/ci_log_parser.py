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

__all__ = [
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
    lines = details.split("\n")
    if len(lines) <= max_lines:
        return details

    tail_lines = max_lines - head_lines
    head = lines[:head_lines]
    tail = lines[-tail_lines:]
    skipped = len(lines) - head_lines - tail_lines

    return "\n".join(head + [f"\n... ({skipped} lines truncated) ...\n"] + tail)


def _strip_timestamps(log_content: str) -> str:
    """Strip GitHub Actions timestamps from log lines.

    GitHub Actions log lines are prefixed with timestamps like:
    2024-01-15T10:30:45.1234567Z <actual content>

    Args:
        log_content: Raw log content with timestamps.

    Returns:
        Log content with timestamps stripped from each line.
    """
    timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s?")
    lines = log_content.split("\n")
    stripped = [timestamp_pattern.sub("", line) for line in lines]
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
    current_group = ""
    current_lines: List[str] = []

    for line in log_content.split("\n"):
        if "##[group]" in line:
            # Save previous group if it has content
            if current_lines:
                groups.append((current_group, current_lines))
            # Start new group - extract name after ##[group]
            current_group = line.split("##[group]", 1)[1].strip()
            current_lines = []
        elif "##[endgroup]" in line:
            # End current group
            if current_lines or current_group:
                groups.append((current_group, current_lines))
            current_group = ""
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget remaining lines
    if current_lines:
        groups.append((current_group, current_lines))

    return groups


def _extract_failed_step_log(log_content: str, step_name: str) -> str:
    """Extract log content for a specific failed step.

    Searches through log groups for a section matching the step name
    and returns its content.

    Args:
        log_content: Full log content for a job.
        step_name: Name of the failed step to extract.

    Returns:
        Log content for the matching step, or the full log if no
        matching group is found.
    """
    groups = _parse_groups(log_content)

    for group_name, lines in groups:
        if step_name.lower() in group_name.lower():
            return "\n".join(lines)

    # If no matching group found, return full content
    return log_content


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

    # Try to find exact match by job name and step number
    for filename, content in logs.items():
        # Log files are like "job_name/1_Step Name.txt"
        if job_name.lower() in filename.lower():
            step_pattern = f"{step_number}_"
            if step_pattern in filename:
                return content

    # Try matching just by job name and step name
    for filename, content in logs.items():
        if job_name.lower() in filename.lower():
            if step_name.lower() in filename.lower():
                return content

    # Try matching just by job name - return all content for that job
    job_logs: List[str] = []
    for filename, content in logs.items():
        if job_name.lower() in filename.lower():
            job_logs.append(content)

    if job_logs:
        return "\n".join(job_logs)

    return ""


def _build_ci_error_details(
    ci_manager: "CIResultsManager",
    status_result: Mapping[str, object],
    max_lines: int = 300,
) -> Optional[str]:
    """Build detailed CI error information from failed workflow runs.

    Extracts failed jobs from the status result, fetches logs for up to 3
    failed run IDs, and builds a structured report with job headers,
    log content, and truncation as needed.

    Args:
        ci_manager: CIResultsManager instance for fetching logs.
        status_result: CI status data dict with 'run' and 'jobs' keys.
        max_lines: Maximum lines for the output (default 300).

    Returns:
        Structured multi-line string with failed job summaries and
        log excerpts, or None if no logs are available.
    """
    jobs: Sequence[Mapping[str, object]] = status_result.get("jobs", [])  # type: ignore[assignment]
    if not jobs:
        return None

    # Find failed jobs
    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    if not failed_jobs:
        return None

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

    if not all_logs:
        return None

    # Build output for each failed job
    output_parts: List[str] = []
    for job in failed_jobs:
        job_name = str(job.get("name", "unknown"))
        steps: Sequence[Mapping[str, object]] = job.get("steps", [])  # type: ignore[assignment]

        # Find the failed step
        failed_steps = [s for s in steps if s.get("conclusion") == "failure"]

        header = f"## Failed Job: {job_name}"
        output_parts.append(header)

        if failed_steps:
            for step in failed_steps:
                step_name = str(step.get("name", "unknown"))
                step_number = int(str(step.get("number", 0)))

                output_parts.append(f"### Failed Step: {step_name}")

                log_content = _find_log_content(
                    all_logs, job_name, step_number, step_name
                )
                if log_content:
                    cleaned = _strip_timestamps(log_content)
                    extracted = _extract_failed_step_log(cleaned, step_name)
                    output_parts.append(extracted)
                else:
                    output_parts.append("(no log content available)")
        else:
            output_parts.append("(no failed steps identified)")

    result = "\n\n".join(output_parts)
    return truncate_ci_details(result, max_lines=max_lines)
