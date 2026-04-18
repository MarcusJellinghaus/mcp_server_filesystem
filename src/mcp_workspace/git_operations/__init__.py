"""Git operations package - modular git utilities."""

from mcp_workspace.git_operations.branch_queries import get_default_branch_name
from mcp_workspace.git_operations.file_tracking import (
    git_move,
    is_file_tracked,
)
from mcp_workspace.git_operations.remotes import get_github_repository_url
from mcp_workspace.git_operations.repository_status import is_git_repository

__all__ = [
    "is_git_repository",
    "is_file_tracked",
    "git_move",
    "get_default_branch_name",
    "get_github_repository_url",
]
