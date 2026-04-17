"""Git operations package - modular git utilities."""

from mcp_workspace.file_tools.git_operations.branch_queries import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    has_remote_tracking_branch,
    remote_branch_exists,
    validate_branch_name,
)
from mcp_workspace.file_tools.git_operations.branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)
from mcp_workspace.file_tools.git_operations.commits import (
    commit_staged_files,
    get_latest_commit_sha,
)
from mcp_workspace.file_tools.git_operations.diffs import (
    get_branch_diff,
    get_git_diff_for_commit,
)
from mcp_workspace.file_tools.git_operations.file_tracking import (
    git_move,
    is_file_tracked,
)
from mcp_workspace.file_tools.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)
from mcp_workspace.file_tools.git_operations.remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)
from mcp_workspace.file_tools.git_operations.repository_status import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
)
from mcp_workspace.file_tools.git_operations.staging import (
    stage_all_changes,
    stage_specific_files,
)
from mcp_workspace.file_tools.git_operations.workflows import (
    commit_all_changes,
    needs_rebase,
)

__all__ = [
    # branch_queries
    "branch_exists",
    "extract_issue_number_from_branch",
    "get_current_branch_name",
    "get_default_branch_name",
    "has_remote_tracking_branch",
    "remote_branch_exists",
    "validate_branch_name",
    # branches
    "checkout_branch",
    "create_branch",
    "delete_branch",
    # commits
    "commit_staged_files",
    "get_latest_commit_sha",
    # diffs
    "get_branch_diff",
    "get_git_diff_for_commit",
    # file_tracking
    "git_move",
    "is_file_tracked",
    # parent_branch_detection
    "MERGE_BASE_DISTANCE_THRESHOLD",
    "detect_parent_branch_via_merge_base",
    # remotes
    "fetch_remote",
    "get_github_repository_url",
    "git_push",
    "push_branch",
    "rebase_onto_branch",
    # repository_status
    "get_full_status",
    "get_staged_changes",
    "get_unstaged_changes",
    "is_git_repository",
    "is_working_directory_clean",
    # staging
    "stage_all_changes",
    "stage_specific_files",
    # workflows
    "commit_all_changes",
    "needs_rebase",
]
