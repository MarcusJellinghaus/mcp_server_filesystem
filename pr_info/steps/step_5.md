# Step 5: Add branch_status check and check_branch_status MCP tool

> See [summary.md](./summary.md) for full context. This is step 5 of 6.

## Goal

Move `branch_status.py` from mcp-coder `checks/` into `mcp_workspace/checks/`. Then expose as the `check_branch_status` MCP tool in `server.py`. This is the most complex module — it depends on `task_tracker` (step 1), `ci_log_parser` (step 2), and `base_branch` (step 3), which is why it comes last.

## LLM Prompt

```
Implement step 5 from pr_info/steps/step_5.md. Read pr_info/steps/summary.md for context.
Copy branch_status.py from mcp-coder's src/mcp_coder/checks/branch_status.py into
src/mcp_workspace/checks/branch_status.py. This module depends on task_tracker (step 1),
ci_log_parser (step 2), and base_branch (step 3) — all already in place.
Rewire imports from mcp_coder.mcp_workspace_git to mcp_workspace.git_operations.* and
mcp_workspace.github_operations.* directly. Add check_branch_status MCP tool. All checks must pass.
```

## WHERE

| Action | Path |
|--------|------|
| Create | `src/mcp_workspace/checks/branch_status.py` |
| Create | `tests/checks/test_branch_status.py` |
| Create | `tests/checks/test_branch_status_pr_fields.py` |
| Modify | `src/mcp_workspace/server.py` — add `check_branch_status` tool |
| Modify | `vulture_whitelist.py` — add `check_branch_status` |

## WHAT — Source module

**File**: `src/mcp_workspace/checks/branch_status.py`

Copied 1:1 from mcp-coder. Key functions:

```python
def collect_branch_status(
    project_dir: Path,
    max_log_lines: int = 300,
) -> dict[str, Any]:
    """Collect comprehensive branch status: git state, CI, PR, tasks.
    Always attempts PR lookup (no toggle parameter).
    """

def format_for_llm(status: dict[str, Any]) -> str:
    """Format collected status into LLM-friendly text output."""
```

## HOW — Import adjustments (the main rewiring work)

Old mcp-coder imports → new mcp-workspace imports:

| Old import | New import |
|-----------|-----------|
| `mcp_coder.mcp_workspace_git.get_current_branch_name` | `mcp_workspace.git_operations.get_current_branch_name` |
| `mcp_coder.mcp_workspace_git.get_default_branch_name` | `mcp_workspace.git_operations.get_default_branch_name` |
| `mcp_coder.mcp_workspace_git.get_github_repository_url` | `mcp_workspace.git_operations.get_github_repository_url` |
| `mcp_coder.workflow_utils.base_branch.detect_base_branch` | `mcp_workspace.git_operations.base_branch.detect_base_branch` |
| `mcp_coder.workflow_utils.task_tracker.*` | `mcp_workspace.workflows.task_tracker.*` |
| `mcp_coder.checks.ci_log_parser.get_failed_jobs_summary` | `mcp_workspace.github_operations.ci_log_parser.get_failed_jobs_summary` |
| `mcp_coder.mcp_workspace_git.PullRequestManager` | `mcp_workspace.github_operations.PullRequestManager` |
| `mcp_coder.mcp_workspace_git.CIResultsManager` | `mcp_workspace.github_operations.CIResultsManager` |
| `mcp_coder.mcp_workspace_git.LabelsManager` | `mcp_workspace.github_operations.LabelsManager` |

## ALGORITHM — `collect_branch_status` (pseudocode)

```
1. Get current branch, default branch, base branch via git_operations
2. Get PR for current branch via PullRequestManager
3. Get CI status via CIResultsManager
4. If CI has failures: get_failed_jobs_summary(ci_status, ci_manager, max_log_lines)
5. Parse TASK_TRACKER.md via task_tracker if it exists
6. Check labels via LabelsManager
7. Return dict with all collected status sections
```

## WHAT — MCP tool wrapper in `server.py`

```python
@mcp.tool()
@log_function_call
def check_branch_status(max_log_lines: int = 300) -> str:
    """Check comprehensive branch status: git state, CI, PR, tasks.

    Args:
        max_log_lines: Maximum CI log lines to include (default 300).

    Returns:
        Formatted branch status report for LLM consumption.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    status = collect_branch_status(_project_dir, max_log_lines=max_log_lines)
    return format_for_llm(status)
```

**Imports to add in `server.py`**:
```python
from mcp_workspace.checks.branch_status import collect_branch_status, format_for_llm
```

## WHAT — Tests

**File**: `tests/checks/test_branch_status.py`

Copied 1:1 from mcp-coder's `tests/checks/test_branch_status.py`. Adjust imports:
- `from mcp_coder.checks.branch_status` → `from mcp_workspace.checks.branch_status`
- Mock paths adjusted accordingly (patch targets change to `mcp_workspace.*`)

**File**: `tests/checks/test_branch_status_pr_fields.py`

Copied 1:1 from mcp-coder's `tests/checks/test_branch_status_pr_fields.py`. Same import adjustments.

## DATA

`collect_branch_status` returns:
```python
{
    "current_branch": "123-feature",
    "default_branch": "main",
    "base_branch": "main",
    "pr": {"number": 45, "title": "...", "state": "open", ...} | None,
    "ci_status": {"overall": "failure", "jobs": [...]} | None,
    "ci_log_summary": "Failed job output..." | None,
    "tasks": {"total": 5, "completed": 3, "remaining": 2} | None,
    "labels": ["status-04:in-progress"] | None,
    "rebase_needed": True | False,
}
```

`format_for_llm` returns a formatted multi-line string.

## Commit

```
feat: add branch_status check and MCP tool

Move branch_status.py from mcp-coder checks into mcp_workspace.checks.
Expose as check_branch_status MCP tool. Rewire imports from
mcp_coder.mcp_workspace_git to mcp_workspace direct modules.
No logic changes.

Ref: #114
```
