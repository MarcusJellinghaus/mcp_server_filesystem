"""Tests for GitHub issue formatters."""

from mcp_workspace.github_operations.formatters import (
    format_issue_list,
    format_issue_view,
    truncate_output,
)
from mcp_workspace.github_operations.issues.types import CommentData, IssueData


def _make_issue(
    number: int = 42,
    title: str = "Test issue",
    body: str = "Issue body text",
    state: str = "open",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> IssueData:
    """Create a test IssueData dict."""
    return IssueData(
        number=number,
        title=title,
        body=body,
        state=state,
        labels=labels or [],
        assignees=assignees or [],
        user="testuser",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
        url=f"https://github.com/owner/repo/issues/{number}",
        locked=False,
    )


def _make_comment(
    body: str = "Comment text",
    user: str = "commenter",
    created_at: str = "2024-01-03T00:00:00Z",
) -> CommentData:
    """Create a test CommentData dict."""
    return CommentData(
        id=1,
        body=body,
        user=user,
        created_at=created_at,
        updated_at=None,
        url="https://github.com/owner/repo/issues/42#comment-1",
    )


# --- truncate_output tests ---


class TestTruncateOutput:
    """Tests for truncate_output."""

    def test_truncate_output_no_truncation(self) -> None:
        """Text within limit returned as-is."""
        text = "line1\nline2\nline3"
        result = truncate_output(text, max_lines=5)
        assert result == text

    def test_truncate_output_truncation(self) -> None:
        """Text exceeding limit truncated with indicator."""
        text = "\n".join(f"line{i}" for i in range(10))
        result = truncate_output(text, max_lines=3)
        assert "line0" in result
        assert "line1" in result
        assert "line2" in result
        assert "line3" not in result
        assert "... truncated, 10 lines total" in result

    def test_truncate_output_exact_limit(self) -> None:
        """Text at exact limit not truncated."""
        text = "\n".join(f"line{i}" for i in range(5))
        result = truncate_output(text, max_lines=5)
        assert result == text
        assert "truncated" not in result


# --- format_issue_view tests ---


class TestFormatIssueView:
    """Tests for format_issue_view."""

    def test_format_issue_view_basic(self) -> None:
        """Title, state, labels, body rendered."""
        issue = _make_issue(
            number=42,
            title="Bug report",
            body="Something broke",
            state="open",
            labels=["bug", "urgent"],
            assignees=["alice"],
        )
        result = format_issue_view(issue, comments=[])
        assert "# #42: Bug report" in result
        assert "open" in result
        assert "bug" in result
        assert "urgent" in result
        assert "alice" in result
        assert "Something broke" in result

    def test_format_issue_view_with_comments(self) -> None:
        """Comments section rendered."""
        issue = _make_issue()
        comments = [
            _make_comment(body="First comment", user="alice", created_at="2024-01-03T00:00:00Z"),
            _make_comment(body="Second comment", user="bob", created_at="2024-01-04T00:00:00Z"),
        ]
        result = format_issue_view(issue, comments=comments)
        assert "Comments (2)" in result
        assert "**alice**" in result
        assert "First comment" in result
        assert "**bob**" in result
        assert "Second comment" in result

    def test_format_issue_view_no_comments(self) -> None:
        """No comments section when empty list."""
        issue = _make_issue()
        result = format_issue_view(issue, comments=[])
        assert "Comments" not in result

    def test_format_issue_view_truncation(self) -> None:
        """Long output truncated with indicator."""
        issue = _make_issue(body="\n".join(f"line {i}" for i in range(300)))
        result = format_issue_view(issue, comments=[], max_lines=10)
        assert "truncated" in result

    def test_format_issue_view_empty_body(self) -> None:
        """'(no description)' placeholder for empty body."""
        issue = _make_issue(body="")
        result = format_issue_view(issue, comments=[])
        assert "(no description)" in result


# --- format_issue_list tests ---


class TestFormatIssueList:
    """Tests for format_issue_list."""

    def test_format_issue_list_basic(self) -> None:
        """Renders summary lines."""
        issues = [
            _make_issue(number=1, title="First issue", state="open"),
            _make_issue(number=2, title="Second issue", state="closed"),
        ]
        result = format_issue_list(issues)
        assert "#1 [open] First issue" in result
        assert "#2 [closed] Second issue" in result

    def test_format_issue_list_empty(self) -> None:
        """'No issues found.' message."""
        result = format_issue_list([])
        assert result == "No issues found."

    def test_format_issue_list_max_results_cap(self) -> None:
        """Excess issues truncated with guidance."""
        issues = [_make_issue(number=i, title=f"Issue {i}") for i in range(5)]
        result = format_issue_list(issues, max_results=3)
        assert "#0" in result
        assert "#1" in result
        assert "#2" in result
        assert "#3" not in result
        assert "5 total results" in result
        assert "Showing first 3" in result

    def test_format_issue_list_labels(self) -> None:
        """Labels rendered in summary line."""
        issues = [_make_issue(number=1, title="Labeled", labels=["bug", "help wanted"])]
        result = format_issue_list(issues)
        assert "bug" in result
        assert "help wanted" in result
