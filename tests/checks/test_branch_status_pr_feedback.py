"""Tests for the `format_pr_feedback` pure formatter."""

from typing import Any

from github.GithubException import GithubException

from mcp_workspace.checks.pr_feedback import format_pr_feedback
from mcp_workspace.github_operations.pr_manager import PRFeedback


def _empty_feedback() -> PRFeedback:
    return {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": [],
        "unavailable": {},
    }


def _thread(
    path: str = "src/foo.py",
    line: int = 42,
    author: str = "alice",
    body: str = "Please refactor this.",
    diff_hunk: str = "@@ -1,2 +1,2 @@\n-x = 1\n+x = 2",
) -> dict[str, Any]:
    return {
        "path": path,
        "line": line,
        "author": author,
        "body": body,
        "diff_hunk": diff_hunk,
    }


def _comment(author: str = "bob", body: str = "Looks good") -> dict[str, Any]:
    return {"author": author, "body": body}


def _changes_requested(
    author: str = "carol", body: str = "Needs work"
) -> dict[str, Any]:
    return {"author": author, "body": body}


def _alert(
    rule_description: str = "py/sql-injection",
    message: str = "SQL injection vulnerability",
    path: str = "src/db.py",
    line: int = 17,
) -> dict[str, Any]:
    return {
        "rule_description": rule_description,
        "message": message,
        "path": path,
        "line": line,
    }


class TestEmptyFeedback:
    """Empty feedback returns affirmation line."""

    def test_empty_feedback_returns_clean_line(self) -> None:
        result = format_pr_feedback(_empty_feedback())
        assert result == "Reviews: clean (0 unresolved threads, 0 alerts)"

    def test_only_resolved_threads_shows_clean(self) -> None:
        feedback = _empty_feedback()
        feedback["resolved_thread_count"] = 5
        result = format_pr_feedback(feedback)
        assert result == "Reviews: clean (0 unresolved threads, 0 alerts)"


class TestUnresolvedThreads:
    """Unresolved threads rendering."""

    def test_unresolved_thread_rendered(self) -> None:
        feedback = _empty_feedback()
        feedback["unresolved_threads"] = [
            _thread(path="src/foo.py", line=42, author="alice"),
        ]
        result = format_pr_feedback(feedback)
        assert result.startswith("PR Reviews:")
        assert "[unresolved thread]" in result
        assert "src/foo.py:42" in result
        assert "alice" in result
        assert "@@ -1,2 +1,2 @@" in result
        assert "Please refactor this." in result

    def test_unresolved_thread_without_line_no(self) -> None:
        """Outdated/file-level threads have line=None; render path only."""
        feedback = _empty_feedback()
        thread = _thread(path="src/foo.py", author="alice")
        thread["line"] = None
        feedback["unresolved_threads"] = [thread]
        result = format_pr_feedback(feedback)
        assert "[unresolved thread]" in result
        assert "src/foo.py" in result
        assert ":None" not in result
        assert "src/foo.py (alice)" in result


class TestConversationComments:
    """Conversation comments rendering."""

    def test_conversation_comment_rendered(self) -> None:
        feedback = _empty_feedback()
        feedback["conversation_comments"] = [_comment(author="bob", body="Nice work")]
        result = format_pr_feedback(feedback)
        assert result.startswith("PR Reviews:")
        assert "[comment]" in result
        assert "bob" in result
        assert "Nice work" in result


class TestChangesRequested:
    """Changes requested rendering."""

    def test_changes_requested_rendered(self) -> None:
        feedback = _empty_feedback()
        feedback["changes_requested"] = [
            _changes_requested(author="carol", body="Needs work")
        ]
        result = format_pr_feedback(feedback)
        assert result.startswith("PR Reviews:")
        assert "[changes_requested]" in result
        assert "carol" in result
        assert "Needs work" in result


class TestAlerts:
    """Code-scanning alerts rendering."""

    def test_alert_rendered(self) -> None:
        feedback = _empty_feedback()
        feedback["alerts"] = [
            _alert(
                rule_description="py/sql-injection",
                message="SQL injection",
                path="src/db.py",
                line=17,
            )
        ]
        result = format_pr_feedback(feedback)
        assert result.startswith("PR Reviews:")
        assert "[alert]" in result
        assert "py/sql-injection" in result
        assert "SQL injection" in result
        assert "src/db.py:17" in result

    def test_alert_without_line_no(self) -> None:
        """Alerts without a specific line number render path only."""
        feedback = _empty_feedback()
        alert = _alert(
            rule_description="py/sql-injection",
            message="SQL injection",
            path="src/db.py",
        )
        alert["line"] = None
        feedback["alerts"] = [alert]
        result = format_pr_feedback(feedback)
        assert "[alert]" in result
        assert "src/db.py" in result
        assert ":None" not in result
        assert "@ src/db.py" in result


class TestResolvedThreadsTrailingLine:
    """Resolved threads trailing line."""

    def test_resolved_count_trailing_line(self) -> None:
        feedback = _empty_feedback()
        feedback["unresolved_threads"] = [_thread()]
        feedback["resolved_thread_count"] = 12
        result = format_pr_feedback(feedback)
        assert result.endswith("12 resolved threads")

    def test_resolved_count_zero_omitted(self) -> None:
        feedback = _empty_feedback()
        feedback["unresolved_threads"] = [_thread()]
        feedback["resolved_thread_count"] = 0
        result = format_pr_feedback(feedback)
        assert "resolved threads" not in result


class TestBodyTruncation:
    """Body truncation per `_MAX_LINES_PER_COMMENT`."""

    def test_long_comment_body_truncated(self) -> None:
        feedback = _empty_feedback()
        long_body = "\n".join(f"line {i}" for i in range(1, 21))
        feedback["conversation_comments"] = [_comment(body=long_body)]
        result = format_pr_feedback(feedback)
        assert "line 10" in result
        assert "line 11" not in result
        assert "... (truncated)" in result


class TestItemCap:
    """Total item cap at `_MAX_FEEDBACK_ITEMS`."""

    def test_thirty_items_capped_at_twenty(self) -> None:
        feedback = _empty_feedback()
        feedback["conversation_comments"] = [
            _comment(author=f"user{i}", body=f"comment {i}") for i in range(30)
        ]
        result = format_pr_feedback(feedback)
        assert result.count("[comment]") == 20
        assert "... and 10 more" in result


class TestUnavailableSection:
    """Unavailable sections render rich error detail per exception."""

    def test_github_exception_with_message(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {
            "threads": GithubException(500, {"message": "Server Error"}, None)
        }
        result = format_pr_feedback(feedback)
        assert "[unavailable] threads: GithubException 500 — Server Error" in result

    def test_github_exception_empty_data_omits_message_segment(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {"threads": GithubException(500, {}, None)}
        result = format_pr_feedback(feedback)
        assert "[unavailable] threads: GithubException 500" in result
        assert "GithubException 500 —" not in result
        assert "(no message)" not in result

    def test_github_exception_non_dict_data_omits_message_segment(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {"threads": GithubException(500, "raw text", None)}
        result = format_pr_feedback(feedback)
        assert "[unavailable] threads: GithubException 500" in result
        assert "GithubException 500 —" not in result
        assert "(no message)" not in result

    def test_generic_exception_with_message(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {"comments": ConnectionError("getaddrinfo failed")}
        result = format_pr_feedback(feedback)
        assert "[unavailable] comments: ConnectionError — getaddrinfo failed" in result

    def test_generic_exception_whitespace_message_renders_no_message(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {"alerts": RuntimeError("   ")}
        result = format_pr_feedback(feedback)
        assert "[unavailable] alerts: RuntimeError — (no message)" in result

    def test_multi_line_message_collapsed_to_single_spaces(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {
            "threads": GithubException(500, {"message": "boom\nsecond line"}, None)
        }
        result = format_pr_feedback(feedback)
        assert (
            "[unavailable] threads: GithubException 500 — boom second line" in result
        )

    def test_github_exception_whitespace_only_message_omits_segment(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {
            "threads": GithubException(500, {"message": "   "}, None)
        }
        result = format_pr_feedback(feedback)
        assert "[unavailable] threads: GithubException 500" in result
        assert "GithubException 500 —" not in result
        assert "(no message)" not in result

    def test_truncation_at_200_chars(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {
            "threads": GithubException(500, {"message": "x" * 500}, None)
        }
        result = format_pr_feedback(feedback)
        line = next(
            line
            for line in result.split("\n")
            if line.startswith("[unavailable] threads: ")
        )
        payload = line[len("[unavailable] threads: ") :]
        assert payload.endswith("...")
        assert len(payload) == 203

    def test_multiple_sections_preserve_insertion_order(self) -> None:
        feedback = _empty_feedback()
        feedback["unavailable"] = {
            "threads": GithubException(500, {"message": "a"}, None),
            "comments": GithubException(502, {"message": "b"}, None),
            "alerts": GithubException(503, {"message": "c"}, None),
        }
        result = format_pr_feedback(feedback)
        lines = result.split("\n")
        t_idx = next(
            i for i, line in enumerate(lines) if line.startswith("[unavailable] threads")
        )
        c_idx = next(
            i for i, line in enumerate(lines) if line.startswith("[unavailable] comments")
        )
        a_idx = next(
            i for i, line in enumerate(lines) if line.startswith("[unavailable] alerts")
        )
        assert t_idx < c_idx < a_idx


class TestMixedFullExample:
    """Mixed example matching issue spec."""

    def test_mixed_full_example(self) -> None:
        feedback = _empty_feedback()
        feedback["unresolved_threads"] = [
            _thread(
                path="src/foo.py",
                line=42,
                author="alice",
                body="Please refactor this.",
                diff_hunk="@@ -40,3 +40,3 @@\n-old\n+new",
            )
        ]
        feedback["conversation_comments"] = [_comment(author="bob", body="LGTM")]
        feedback["changes_requested"] = [
            _changes_requested(author="carol", body="Needs work")
        ]
        feedback["alerts"] = [
            _alert(
                rule_description="py/sql-injection",
                message="SQL injection",
                path="src/db.py",
                line=17,
            )
        ]
        feedback["resolved_thread_count"] = 12

        result = format_pr_feedback(feedback)
        lines = result.split("\n")
        assert lines[0] == "PR Reviews:"
        assert any("[unresolved thread]" in line for line in lines)
        assert any("[comment]" in line for line in lines)
        assert any("[changes_requested]" in line for line in lines)
        assert any("[alert]" in line for line in lines)
        assert lines[-1] == "12 resolved threads"


class TestCapOrdering:
    """Cap-ordering: unresolved → comments → changes_requested → alerts."""

    def test_unresolved_threads_filling_cap_drops_others(self) -> None:
        feedback = _empty_feedback()
        feedback["unresolved_threads"] = [_thread() for _ in range(25)]
        feedback["conversation_comments"] = [_comment()]
        feedback["alerts"] = [_alert()]
        result = format_pr_feedback(feedback)
        assert result.count("[unresolved thread]") == 20
        assert "[comment]" not in result
        assert "[alert]" not in result
        assert "... and 7 more" in result
