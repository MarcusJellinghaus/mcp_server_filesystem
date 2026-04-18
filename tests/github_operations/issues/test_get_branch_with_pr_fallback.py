"""Unit tests for IssueBranchManager.get_branch_with_pr_fallback() method."""

# pylint: disable=protected-access  # Tests need to access protected members for mocking

from typing import Any
from unittest.mock import Mock

import pytest
from github import GithubException

from mcp_workspace.github_operations.issues import IssueBranchManager


class TestGetBranchWithPRFallback:
    """Test suite for IssueBranchManager.get_branch_with_pr_fallback()."""

    def test_linked_branch_found_returns_branch_name(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test branch found via linkedBranches (primary path).

        When linkedBranches returns a branch, should return immediately
        without querying PR timeline.
        """
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return branch
        mock_manager.get_linked_branches = Mock(  # type: ignore[method-assign]
            return_value=["123-feature-branch"]
        )

        # Setup: Mock GraphQL client (should NOT be called)
        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_graphql_query = Mock()
        mock_manager._github_client._Github__requester.graphql_query = mock_graphql_query  # type: ignore[attr-defined]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result == "123-feature-branch"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        # GraphQL should NOT be called (short-circuit)
        mock_graphql_query.assert_not_called()

    @pytest.mark.parametrize(
        "pr_state,is_draft,pr_number",
        [
            ("OPEN", True, 42),  # Draft PR
            ("OPEN", False, 43),  # Open (non-draft) PR
        ],
    )
    def test_no_linked_branch_single_pr_returns_branch(
        self,
        mock_manager: IssueBranchManager,
        pr_state: str,
        is_draft: bool,
        pr_number: int,
    ) -> None:
        """Test fallback: no linkedBranches, single draft/open PR found."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with single PR
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": pr_number,
                                        "state": pr_state,
                                        "isDraft": is_draft,
                                        "headRefName": "123-feature-branch",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result == "123-feature-branch"
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]

    def test_no_linked_branch_multiple_prs_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test multiple PRs found returns None with warning."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with TWO PRs
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 42,
                                        "state": "OPEN",
                                        "isDraft": True,
                                        "headRefName": "123-feature-branch-1",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 43,
                                        "state": "OPEN",
                                        "isDraft": False,
                                        "headRefName": "123-feature-branch-2",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]

    def test_no_linked_branch_no_prs_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test no linkedBranches and no PRs falls through to pattern search."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with empty nodes
        timeline_response: dict[str, Any] = {
            "data": {"repository": {"issue": {"timelineItems": {"nodes": []}}}}
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Setup: Mock pattern search to return None
        mock_manager._search_branches_by_pattern = Mock(return_value=None)  # type: ignore[method-assign]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None
        mock_manager.get_linked_branches.assert_called_once_with(123)
        mock_manager._github_client._Github__requester.graphql_query.assert_called_once()  # type: ignore[attr-defined]
        mock_manager._search_branches_by_pattern.assert_called_once_with(123, mock_repo)

    def test_invalid_issue_number_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test invalid issue numbers return None."""
        # Test with negative number
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=-1, repo_owner="test-owner", repo_name="test-repo"
        )
        assert result is None

        # Test with zero
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=0, repo_owner="test-owner", repo_name="test-repo"
        )
        assert result is None

    def test_graphql_error_returns_none(self, mock_manager: IssueBranchManager) -> None:
        """Test GraphQL errors handled by decorator return None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL to raise exception
        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            side_effect=GithubException(500, {"message": "Internal Server Error"}, None)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_repository_not_found_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test repository access failure returns None."""
        # Mock _get_repository to return None
        mock_manager._repository = None
        mock_manager._get_repository = Mock(return_value=None)  # type: ignore[method-assign]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_malformed_timeline_response_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test malformed GraphQL timeline response returns None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL response with malformed data
        malformed_response: dict[str, Any] = {"data": None}  # Malformed response

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, malformed_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_issue_not_found_in_timeline_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test timeline query when issue is not found returns None."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL response with null issue
        timeline_response: dict[str, Any] = {"data": {"repository": {"issue": None}}}

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=999, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify
        assert result is None

    def test_closed_prs_filtered_out(self, mock_manager: IssueBranchManager) -> None:
        """Test that closed PRs are filtered out and only OPEN PRs are considered."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with closed and open PRs
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 40,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-closed-pr",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 42,
                                        "state": "OPEN",
                                        "isDraft": True,
                                        "headRefName": "123-feature-branch",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify - should return the OPEN PR branch, ignoring CLOSED
        assert result == "123-feature-branch"

    def test_non_pr_cross_references_filtered_out(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Test that non-PR cross-references are filtered out."""
        # Setup: Mock repository
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        # Setup: Mock get_linked_branches to return empty
        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Setup: Mock GraphQL timeline response with non-PR cross-reference
        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        # This is an Issue, not a PR - missing PR-specific fields
                                        "number": 40,
                                        "title": "Related issue",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Setup: Mock pattern search to return None
        mock_manager._search_branches_by_pattern = Mock(return_value=None)  # type: ignore[method-assign]

        # Execute
        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Verify - should return None as no valid PRs found
        assert result is None

    def test_multiple_linked_branches_returns_none(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Two linked branches returns None (ambiguous)."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(  # type: ignore[method-assign]
            return_value=["123-branch-a", "123-branch-b"]
        )

        # GraphQL should NOT be called (short-circuit)
        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_graphql_query = Mock()
        mock_manager._github_client._Github__requester.graphql_query = mock_graphql_query  # type: ignore[attr-defined]

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result is None
        mock_graphql_query.assert_not_called()

    def test_closed_pr_with_existing_branch(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Closed PR with existing branch returns branch name."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 50,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-closed-branch",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Branch exists
        mock_repo.get_branch = Mock(return_value=Mock())

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result == "123-closed-branch"
        mock_repo.get_branch.assert_called_once_with("123-closed-branch")

    def test_closed_pr_with_deleted_branch(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Closed PR with deleted branch falls through to pattern search."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 50,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-deleted-branch",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Branch deleted — get_branch raises GithubException
        mock_repo.get_branch = Mock(
            side_effect=GithubException(404, {"message": "Branch not found"}, None)
        )

        # Pattern search also returns None
        mock_manager._search_branches_by_pattern = Mock(return_value=None)  # type: ignore[method-assign]

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result is None
        mock_repo.get_branch.assert_called_once_with("123-deleted-branch")
        mock_manager._search_branches_by_pattern.assert_called_once_with(123, mock_repo)

    def test_merged_pr_not_matched(self, mock_manager: IssueBranchManager) -> None:
        """Merged PR in timeline is skipped (state is MERGED, not CLOSED)."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 50,
                                        "state": "MERGED",
                                        "isDraft": False,
                                        "headRefName": "123-merged-branch",
                                    },
                                }
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # get_branch should NOT be called (MERGED is not CLOSED)
        mock_repo.get_branch = Mock()
        mock_manager._search_branches_by_pattern = Mock(return_value=None)  # type: ignore[method-assign]

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result is None
        mock_repo.get_branch.assert_not_called()

    def test_closed_pr_25_check_cap(self, mock_manager: IssueBranchManager) -> None:
        """30 closed PRs, all branches deleted — stops checking after 25."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        # Build 30 closed PRs
        nodes = [
            {
                "__typename": "CrossReferencedEvent",
                "source": {
                    "number": i,
                    "state": "CLOSED",
                    "isDraft": False,
                    "headRefName": f"123-branch-{i}",
                },
            }
            for i in range(30)
        ]

        timeline_response = {
            "data": {"repository": {"issue": {"timelineItems": {"nodes": nodes}}}}
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # All branches deleted
        mock_repo.get_branch = Mock(
            side_effect=GithubException(404, {"message": "Not found"}, None)
        )

        mock_manager._search_branches_by_pattern = Mock(return_value=None)  # type: ignore[method-assign]

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result is None
        # Should only check 25 branches, not all 30
        assert mock_repo.get_branch.call_count == 25

    def test_closed_pr_most_recent_preferred(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Multiple closed PRs with existing branches — returns highest PR number."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 10,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-old-branch",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 55,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-newest-branch",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 30,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-middle-branch",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # All branches exist
        mock_repo.get_branch = Mock(return_value=Mock())

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Should return the branch from the highest PR number (55)
        assert result == "123-newest-branch"
        mock_repo.get_branch.assert_called_once_with("123-newest-branch")

    def test_closed_pr_prefers_open_pr(self, mock_manager: IssueBranchManager) -> None:
        """Both open and closed PRs exist — returns open PR branch (step order)."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response = {
            "data": {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "nodes": [
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 50,
                                        "state": "CLOSED",
                                        "isDraft": False,
                                        "headRefName": "123-closed-branch",
                                    },
                                },
                                {
                                    "__typename": "CrossReferencedEvent",
                                    "source": {
                                        "number": 60,
                                        "state": "OPEN",
                                        "isDraft": False,
                                        "headRefName": "123-open-branch",
                                    },
                                },
                            ]
                        }
                    }
                }
            }
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        # Open PR is checked first (step 6), before closed PR fallback (step 7)
        assert result == "123-open-branch"

    def test_pattern_fallback_used_when_no_prs(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """No linked branches, no PRs — pattern search is called and returns result."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(return_value=[])  # type: ignore[method-assign]

        timeline_response: dict[str, Any] = {
            "data": {"repository": {"issue": {"timelineItems": {"nodes": []}}}}
        }

        mock_manager._github_client._Github__requester = Mock()  # type: ignore[attr-defined]
        mock_manager._github_client._Github__requester.graphql_query = Mock(  # type: ignore[attr-defined]
            return_value=({}, timeline_response)
        )

        # Pattern search finds a branch
        mock_manager._search_branches_by_pattern = Mock(  # type: ignore[method-assign]
            return_value="123-pattern-match"
        )

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result == "123-pattern-match"
        mock_manager._search_branches_by_pattern.assert_called_once_with(123, mock_repo)

    def test_pattern_fallback_not_called_when_linked_branch_found(
        self, mock_manager: IssueBranchManager
    ) -> None:
        """Linked branch exists — pattern search NOT called."""
        mock_repo = Mock()
        mock_repo.owner.login = "test-owner"
        mock_repo.name = "test-repo"
        mock_manager._repository = mock_repo

        mock_manager.get_linked_branches = Mock(  # type: ignore[method-assign]
            return_value=["123-linked"]
        )

        mock_manager._search_branches_by_pattern = Mock()  # type: ignore[method-assign]

        result = mock_manager.get_branch_with_pr_fallback(
            issue_number=123, repo_owner="test-owner", repo_name="test-repo"
        )

        assert result == "123-linked"
        mock_manager._search_branches_by_pattern.assert_not_called()
