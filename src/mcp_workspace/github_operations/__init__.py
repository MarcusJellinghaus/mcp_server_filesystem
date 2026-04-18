"""GitHub operations module for MCP Workspace.

This module provides GitHub API integration functionality for managing
pull requests, labels, and repository operations.
"""

from .base_manager import BaseGitHubManager, get_authenticated_username
from .ci_results_manager import CIResultsManager, CIStatusData
from .github_utils import RepoIdentifier
from .labels_manager import LabelData, LabelsManager
from .pr_manager import PullRequestManager

# Issue-related imports REMOVED per Decision #1
# Consumers must import from: mcp_workspace.github_operations.issues


__all__ = [
    "BaseGitHubManager",
    "get_authenticated_username",
    "CIResultsManager",
    "CIStatusData",
    "LabelData",
    "LabelsManager",
    "PullRequestManager",
    "RepoIdentifier",
]
