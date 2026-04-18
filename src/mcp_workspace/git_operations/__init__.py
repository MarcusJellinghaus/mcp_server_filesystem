"""Git operations package - modular git utilities."""

from mcp_workspace.git_operations.branch_queries import (
    branch_exists,
    get_current_branch_name,
    get_default_branch_name,
)
from mcp_workspace.git_operations.branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)
from mcp_workspace.git_operations.file_tracking import (
    git_move,
    is_file_tracked,
)
from mcp_workspace.git_operations.remotes import (
    fetch_remote,
    get_github_repository_url,
    push_branch,
)
from mcp_workspace.git_operations.repository_status import is_git_repository

__all__ = [
    "branch_exists",
    "checkout_branch",
    "create_branch",
    "delete_branch",
    "fetch_remote",
    "get_current_branch_name",
    "get_default_branch_name",
    "get_github_repository_url",
    "git_move",
    "is_file_tracked",
    "is_git_repository",
    "push_branch",
]
