"""Unit tests for `render_exception_for_display`."""

from github.GithubException import GithubException

from mcp_workspace.github_operations.exception_renderer import (
    render_exception_for_display,
)


class TestGithubException:
    """GithubException rendering."""

    def test_with_message(self) -> None:
        result = render_exception_for_display(
            GithubException(500, {"message": "Server Error"}, None)
        )
        assert result == "GithubException 500 — Server Error"

    def test_empty_data_omits_message_segment(self) -> None:
        result = render_exception_for_display(GithubException(500, {}, None))
        assert result == "GithubException 500"
        assert "—" not in result
        assert "(no message)" not in result

    def test_non_dict_data_omits_message_segment(self) -> None:
        result = render_exception_for_display(GithubException(500, "raw text", None))
        assert result == "GithubException 500"
        assert "—" not in result
        assert "(no message)" not in result

    def test_whitespace_only_message_omits_segment(self) -> None:
        result = render_exception_for_display(
            GithubException(500, {"message": "   "}, None)
        )
        assert result == "GithubException 500"
        assert "—" not in result
        assert "(no message)" not in result

    def test_multi_line_message_collapsed_to_single_spaces(self) -> None:
        result = render_exception_for_display(
            GithubException(500, {"message": "boom\nsecond line"}, None)
        )
        assert result == "GithubException 500 — boom second line"

    def test_truncation_at_200_chars(self) -> None:
        result = render_exception_for_display(
            GithubException(500, {"message": "x" * 500}, None)
        )
        assert result.endswith("...")
        assert len(result) == 203


class TestGenericException:
    """Non-GithubException rendering."""

    def test_with_message(self) -> None:
        result = render_exception_for_display(ConnectionError("getaddrinfo failed"))
        assert result == "ConnectionError — getaddrinfo failed"

    def test_whitespace_message_renders_no_message(self) -> None:
        result = render_exception_for_display(RuntimeError("   "))
        assert result == "RuntimeError — (no message)"

    def test_empty_message_renders_no_message(self) -> None:
        result = render_exception_for_display(RuntimeError(""))
        assert result == "RuntimeError — (no message)"

    def test_multi_line_message_collapsed(self) -> None:
        result = render_exception_for_display(RuntimeError("first\n\nsecond"))
        assert result == "RuntimeError — first second"

    def test_truncation_at_200_chars(self) -> None:
        result = render_exception_for_display(RuntimeError("x" * 500))
        assert result.endswith("...")
        assert len(result) == 203
