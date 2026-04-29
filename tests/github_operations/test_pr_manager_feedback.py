"""Unit tests for PullRequestManager.get_pr_feedback() method."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_workspace.github_operations.pr_manager import PullRequestManager


@pytest.mark.git_integration
class TestGetPRFeedback:
    """Tests for PullRequestManager.get_pr_feedback() method."""

    @pytest.fixture
    def mock_manager(self, tmp_path: Path) -> PullRequestManager:
        """Create a PullRequestManager with mocked dependencies."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch(
            "mcp_workspace.github_operations.base_manager.get_github_token",
            return_value="dummy-token",
        ):
            manager = PullRequestManager(git_dir)
            return manager

    def _setup_mocks(
        self,
        manager: PullRequestManager,
        graphql_response: Any = None,
        graphql_raises: Any = None,
        comments: Any = None,
        comments_raises: Any = None,
        alerts_response: Any = None,
        alerts_raises: Any = None,
    ) -> Mock:
        """Set up requester and repository mocks on manager.

        Returns the mocked repository for additional configuration.
        """
        mock_repo = Mock()
        mock_repo.owner.login = "test"
        mock_repo.name = "repo"
        manager._repository = mock_repo

        mock_requester = Mock()
        manager._github_client._Github__requester = mock_requester  # type: ignore[attr-defined]

        # GraphQL setup
        if graphql_raises is not None:
            mock_requester.graphql_query = Mock(side_effect=graphql_raises)
        else:
            mock_requester.graphql_query = Mock(
                return_value=({}, graphql_response or {"data": {}})
            )

        # REST conversation comments via repo.get_issue(...).get_comments()
        mock_issue = Mock()
        if comments_raises is not None:
            mock_issue.get_comments = Mock(side_effect=comments_raises)
        else:
            mock_issue.get_comments = Mock(return_value=comments or [])
        mock_repo.get_issue = Mock(return_value=mock_issue)

        # REST code-scanning alerts via raw requester
        if alerts_raises is not None:
            mock_requester.requestJsonAndCheck = Mock(side_effect=alerts_raises)
        else:
            mock_requester.requestJsonAndCheck = Mock(
                return_value=(200, {}, alerts_response or [])
            )

        return mock_repo

    def _make_comment(self, login: str, body: str) -> Mock:
        """Create a mock conversation comment."""
        comment = Mock()
        comment.user.login = login
        comment.body = body
        return comment

    def test_happy_path(self, mock_manager: PullRequestManager) -> None:
        """All sources return data — populated PRFeedback."""
        graphql_response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "isResolved": False,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "author": {"login": "alice"},
                                                "body": "issue here",
                                                "path": "src/foo.py",
                                                "line": 10,
                                                "diffSide": "RIGHT",
                                                "diffHunk": "@@ ... @@",
                                            }
                                        ]
                                    },
                                },
                                {
                                    "isResolved": False,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "author": {"login": "bob"},
                                                "body": "another",
                                                "path": "src/bar.py",
                                                "line": 5,
                                                "diffSide": "RIGHT",
                                                "diffHunk": "@@ ... @@",
                                            }
                                        ]
                                    },
                                },
                                {
                                    "isResolved": True,
                                    "comments": {
                                        "nodes": [
                                            {
                                                "author": {"login": "carol"},
                                                "body": "fixed",
                                                "path": "src/baz.py",
                                                "line": 1,
                                                "diffSide": "RIGHT",
                                                "diffHunk": "@@ ... @@",
                                            }
                                        ]
                                    },
                                },
                            ]
                        },
                        "reviews": {
                            "nodes": [
                                {
                                    "state": "CHANGES_REQUESTED",
                                    "author": {"login": "alice"},
                                    "body": "please fix",
                                    "submittedAt": "2025-01-01T00:00:00Z",
                                },
                                {
                                    "state": "APPROVED",
                                    "author": {"login": "bob"},
                                    "body": "lgtm",
                                    "submittedAt": "2025-01-02T00:00:00Z",
                                },
                            ]
                        },
                    }
                }
            }
        }
        comments = [
            self._make_comment("alice", "general comment 1"),
            self._make_comment("bob", "general comment 2"),
        ]
        alerts_response = [
            {
                "rule": {"description": "SQL injection"},
                "most_recent_instance": {
                    "message": {"text": "potential SQLi"},
                    "location": {"path": "src/foo.py", "start_line": 42},
                },
            }
        ]
        self._setup_mocks(
            mock_manager,
            graphql_response=graphql_response,
            comments=comments,
            alerts_response=alerts_response,
        )

        result = mock_manager.get_pr_feedback(42)

        assert len(result["unresolved_threads"]) == 2
        assert result["unresolved_threads"][0]["path"] == "src/foo.py"
        assert result["unresolved_threads"][0]["line"] == 10
        assert result["unresolved_threads"][0]["author"] == "alice"
        assert result["unresolved_threads"][0]["body"] == "issue here"
        assert result["unresolved_threads"][0]["diff_hunk"] == "@@ ... @@"
        assert result["resolved_thread_count"] == 1
        assert len(result["changes_requested"]) == 1
        assert result["changes_requested"][0]["author"] == "alice"
        assert result["changes_requested"][0]["body"] == "please fix"
        assert len(result["conversation_comments"]) == 2
        assert result["conversation_comments"][0]["author"] == "alice"
        assert result["conversation_comments"][0]["body"] == "general comment 1"
        assert len(result["alerts"]) == 1
        assert result["alerts"][0]["rule_description"] == "SQL injection"
        assert result["alerts"][0]["message"] == "potential SQLi"
        assert result["alerts"][0]["path"] == "src/foo.py"
        assert result["alerts"][0]["line"] == 42
        assert result["unavailable"] == []

    def test_clean_state(self, mock_manager: PullRequestManager) -> None:
        """All sources return empty — empty PRFeedback, no unavailable entries."""
        graphql_response: dict[str, Any] = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {"nodes": []},
                        "reviews": {"nodes": []},
                    }
                }
            }
        }
        self._setup_mocks(
            mock_manager,
            graphql_response=graphql_response,
            comments=[],
            alerts_response=[],
        )

        result = mock_manager.get_pr_feedback(42)

        assert result["unresolved_threads"] == []
        assert result["resolved_thread_count"] == 0
        assert result["changes_requested"] == []
        assert result["conversation_comments"] == []
        assert result["alerts"] == []
        assert result["unavailable"] == []

    def test_code_scanning_403_silent_skip(
        self, mock_manager: PullRequestManager
    ) -> None:
        """403 on code-scanning → empty alerts, NOT in unavailable."""
        graphql_response: dict[str, Any] = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {"nodes": []},
                        "reviews": {"nodes": []},
                    }
                }
            }
        }
        self._setup_mocks(
            mock_manager,
            graphql_response=graphql_response,
            comments=[],
            alerts_raises=GithubException(403, {"message": "forbidden"}, None),
        )

        result = mock_manager.get_pr_feedback(42)

        assert result["alerts"] == []
        assert "alerts" not in result["unavailable"]

    def test_code_scanning_500_unavailable(
        self, mock_manager: PullRequestManager
    ) -> None:
        """500 on code-scanning → empty alerts, 'alerts' in unavailable."""
        graphql_response: dict[str, Any] = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {"nodes": []},
                        "reviews": {"nodes": []},
                    }
                }
            }
        }
        self._setup_mocks(
            mock_manager,
            graphql_response=graphql_response,
            comments=[],
            alerts_raises=GithubException(500, {"message": "server error"}, None),
        )

        result = mock_manager.get_pr_feedback(42)

        assert result["alerts"] == []
        assert "alerts" in result["unavailable"]

    def test_graphql_failure(self, mock_manager: PullRequestManager) -> None:
        """GraphQL raises → 'threads' in unavailable, threads/changes_requested empty."""
        self._setup_mocks(
            mock_manager,
            graphql_raises=GithubException(500, {"message": "boom"}, None),
            comments=[],
            alerts_response=[],
        )

        result = mock_manager.get_pr_feedback(42)

        assert result["unresolved_threads"] == []
        assert result["resolved_thread_count"] == 0
        assert result["changes_requested"] == []
        assert "threads" in result["unavailable"]

    def test_conversation_comments_failure(
        self, mock_manager: PullRequestManager
    ) -> None:
        """Comments fetch raises → 'comments' in unavailable, comments empty."""
        graphql_response: dict[str, Any] = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {"nodes": []},
                        "reviews": {"nodes": []},
                    }
                }
            }
        }
        self._setup_mocks(
            mock_manager,
            graphql_response=graphql_response,
            comments_raises=GithubException(500, {"message": "boom"}, None),
            alerts_response=[],
        )

        result = mock_manager.get_pr_feedback(42)

        assert result["conversation_comments"] == []
        assert "comments" in result["unavailable"]

    def test_invalid_pr_number(self, mock_manager: PullRequestManager) -> None:
        """pr_number=0 → empty PRFeedback."""
        result = mock_manager.get_pr_feedback(0)

        assert result["unresolved_threads"] == []
        assert result["resolved_thread_count"] == 0
        assert result["changes_requested"] == []
        assert result["conversation_comments"] == []
        assert result["alerts"] == []
        assert result["unavailable"] == []
