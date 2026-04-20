"""Formatters for GitHub issue and PR data.

Pure formatting functions that take data dicts and return formatted text strings.
No API calls or manager dependencies.
"""

from typing import List

from mcp_workspace.github_operations.issues.types import CommentData, IssueData


def truncate_output(text: str, max_lines: int) -> str:
    """Apply max_lines truncation with indicator.

    Args:
        text: The text to potentially truncate.
        max_lines: Maximum number of lines to keep.

    Returns:
        Original text if within limit, otherwise truncated with indicator.
    """
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    total = len(lines)
    return "\n".join(lines[:max_lines]) + f"\n\n... truncated, {total} lines total"


def format_issue_view(
    issue: IssueData,
    comments: List[CommentData],
    max_lines: int = 200,
) -> str:
    """Format a single issue with full detail for LLM consumption.

    Args:
        issue: Issue data dict.
        comments: List of comment data dicts.
        max_lines: Maximum output lines before truncation.

    Returns:
        Formatted multi-line text string.
    """
    parts: list[str] = [f"# #{issue['number']}: {issue['title']}"]

    labels = ", ".join(issue["labels"]) if issue["labels"] else "none"
    assignees = ", ".join(issue["assignees"]) if issue["assignees"] else "none"
    parts.append(f"State: {issue['state']} | Labels: {labels} | Assignees: {assignees}")

    parts.append(issue["body"] or "(no description)")

    if comments:
        parts.append(f"## Comments ({len(comments)})")
        for comment in comments:
            parts.append(f"**{comment['user']}** ({comment['created_at']}):\n{comment['body']}")

    return truncate_output("\n\n".join(parts), max_lines)


def format_issue_list(
    issues: List[IssueData],
    max_results: int = 30,
) -> str:
    """Format issue list as compact summary lines.

    Args:
        issues: List of issue data dicts.
        max_results: Maximum number of issues to display.

    Returns:
        Compact one-line-per-issue text.
    """
    if not issues:
        return "No issues found."

    lines: list[str] = []
    for issue in issues[:max_results]:
        labels_str = ", ".join(issue["labels"]) if issue["labels"] else ""
        label_part = f"  {labels_str}" if labels_str else ""
        lines.append(f"#{issue['number']} [{issue['state']}] {issue['title']}{label_part}")

    if len(issues) > max_results:
        lines.append(
            f"\n... {len(issues)} total results. "
            f"Showing first {max_results}. "
            f"Refine your query for more specific results."
        )

    return "\n".join(lines)
