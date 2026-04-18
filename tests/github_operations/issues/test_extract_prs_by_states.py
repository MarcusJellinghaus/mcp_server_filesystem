"""Unit tests for IssueBranchManager._extract_prs_by_states() method."""

# pylint: disable=protected-access  # Tests need to access protected members for mocking

from typing import Any

from mcp_workspace.github_operations.issues import IssueBranchManager


class TestExtractPrsByStates:
    """Test suite for IssueBranchManager._extract_prs_by_states()."""

    @staticmethod
    def _make_pr_node(
        number: int, state: str, head_ref: str, is_draft: bool = False
    ) -> dict[str, Any]:
        """Helper to build a CrossReferencedEvent timeline node."""
        return {
            "__typename": "CrossReferencedEvent",
            "source": {
                "number": number,
                "state": state,
                "isDraft": is_draft,
                "headRefName": head_ref,
            },
        }

    def test_extract_prs_by_states_open_only(self) -> None:
        """Filters OPEN PRs, excludes CLOSED and MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
            self._make_pr_node(4, "OPEN", "branch-open-2", is_draft=True),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 2
        assert result[0]["headRefName"] == "branch-open"
        assert result[1]["headRefName"] == "branch-open-2"

    def test_extract_prs_by_states_closed_only(self) -> None:
        """Filters CLOSED PRs, excludes OPEN and MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
            self._make_pr_node(4, "CLOSED", "branch-closed-2"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"CLOSED"})

        assert len(result) == 2
        assert result[0]["headRefName"] == "branch-closed"
        assert result[1]["headRefName"] == "branch-closed-2"

    def test_extract_prs_by_states_multiple_states(self) -> None:
        """Passing {"OPEN", "CLOSED"} returns both OPEN and CLOSED, excludes MERGED."""
        timeline_items = [
            self._make_pr_node(1, "OPEN", "branch-open"),
            self._make_pr_node(2, "CLOSED", "branch-closed"),
            self._make_pr_node(3, "MERGED", "branch-merged"),
        ]

        result = IssueBranchManager._extract_prs_by_states(
            timeline_items, {"OPEN", "CLOSED"}
        )

        assert len(result) == 2
        head_refs = {pr["headRefName"] for pr in result}
        assert head_refs == {"branch-open", "branch-closed"}

    def test_extract_prs_by_states_skips_non_cross_referenced(self) -> None:
        """Skips nodes that are not CrossReferencedEvent."""
        timeline_items: list[dict[str, Any]] = [
            {
                "__typename": "SomeOtherEvent",
                "source": {"state": "OPEN", "headRefName": "x"},
            },
            self._make_pr_node(1, "OPEN", "branch-open"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 1
        assert result[0]["headRefName"] == "branch-open"

    def test_extract_prs_by_states_skips_missing_fields(self) -> None:
        """Skips nodes missing state or headRefName."""
        timeline_items = [
            {
                "__typename": "CrossReferencedEvent",
                "source": {"number": 1, "title": "Issue, not PR"},
            },
            self._make_pr_node(2, "OPEN", "branch-open"),
        ]

        result = IssueBranchManager._extract_prs_by_states(timeline_items, {"OPEN"})

        assert len(result) == 1
        assert result[0]["headRefName"] == "branch-open"

    def test_extract_prs_by_states_empty_input(self) -> None:
        """Returns empty list for empty timeline items."""
        result = IssueBranchManager._extract_prs_by_states([], {"OPEN"})
        assert result == []
