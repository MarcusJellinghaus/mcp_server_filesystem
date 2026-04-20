"""Tests for IssueManager.list_issues() extended parameters: labels, assignee, max_results."""

from unittest.mock import MagicMock

import pytest

from mcp_workspace.github_operations.issues import IssueManager


@pytest.mark.git_integration
class TestListIssuesExtendedParams:
    """Tests for labels, assignee, and max_results parameters."""

    def test_list_issues_with_labels(self, mock_issue_manager: IssueManager) -> None:
        """Verify labels param is forwarded to repo.get_issues()."""
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.pull_request = None
        mock_issue.body = ""

        mock_issue_manager._repository.get_issues.return_value = [mock_issue]

        result = mock_issue_manager.list_issues(labels=["bug", "enhancement"])

        assert len(result) == 1
        mock_issue_manager._repository.get_issues.assert_called_once_with(
            state="open", labels=["bug", "enhancement"]
        )

    def test_list_issues_with_assignee(self, mock_issue_manager: IssueManager) -> None:
        """Verify assignee param is forwarded to repo.get_issues()."""
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.pull_request = None
        mock_issue.body = ""

        mock_issue_manager._repository.get_issues.return_value = [mock_issue]

        result = mock_issue_manager.list_issues(assignee="octocat")

        assert len(result) == 1
        mock_issue_manager._repository.get_issues.assert_called_once_with(
            state="open", assignee="octocat"
        )

    def test_list_issues_with_max_results(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Verify iteration stops at max_results limit."""
        mock_issues = []
        for i in range(10):
            issue = MagicMock()
            issue.number = i + 1
            issue.pull_request = None
            issue.body = ""
            mock_issues.append(issue)

        mock_issue_manager._repository.get_issues.return_value = mock_issues

        result = mock_issue_manager.list_issues(max_results=3)

        assert len(result) == 3
        assert [r["number"] for r in result] == [1, 2, 3]

    def test_list_issues_max_results_with_pr_filtering(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Verify max_results counts only non-PR issues when include_pull_requests=False."""
        items = []
        for i in range(6):
            item = MagicMock()
            item.number = i + 1
            item.body = ""
            # Alternate: issue, PR, issue, PR, issue, PR
            item.pull_request = MagicMock() if i % 2 == 1 else None
            items.append(item)

        mock_issue_manager._repository.get_issues.return_value = items

        result = mock_issue_manager.list_issues(
            include_pull_requests=False, max_results=2
        )

        assert len(result) == 2
        # Should get issues #1 and #3 (skipping PRs #2 and #4)
        assert [r["number"] for r in result] == [1, 3]

    def test_list_issues_combined_params(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Verify all new params work together."""
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.pull_request = None
        mock_issue.body = ""

        mock_issue_manager._repository.get_issues.return_value = [mock_issue]

        result = mock_issue_manager.list_issues(
            state="closed",
            labels=["bug"],
            assignee="octocat",
            max_results=10,
        )

        assert len(result) == 1
        mock_issue_manager._repository.get_issues.assert_called_once_with(
            state="closed", labels=["bug"], assignee="octocat"
        )

    def test_list_issues_max_results_none_returns_all(
        self, mock_issue_manager: IssueManager
    ) -> None:
        """Verify that max_results=None returns all issues (default behavior)."""
        mock_issues = []
        for i in range(5):
            issue = MagicMock()
            issue.number = i + 1
            issue.pull_request = None
            issue.body = ""
            mock_issues.append(issue)

        mock_issue_manager._repository.get_issues.return_value = mock_issues

        result = mock_issue_manager.list_issues(max_results=None)

        assert len(result) == 5
