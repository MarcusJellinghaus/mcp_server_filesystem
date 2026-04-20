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

Copied 1:1 from mcp-coder. Key classes and functions:

```python
class CIStatus(str, Enum):
    """CI pipeline status: PASSED, FAILED, NOT_CONFIGURED, PENDING."""

@dataclass(frozen=True)
class BranchStatusReport:
    """Branch readiness status report."""
    branch_name: str
    base_branch: str
    ci_status: CIStatus
    ci_details: Optional[str]
    rebase_needed: bool
    rebase_reason: str
    tasks_status: TaskTrackerStatus
    tasks_reason: str
    tasks_is_blocking: bool
    current_github_label: str
    recommendations: List[str]
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_found: Optional[bool] = None

    def format_for_human(self) -> str: ...
    def format_for_llm(self, max_lines: int = 300) -> str: ...

def create_empty_report() -> BranchStatusReport: ...

def get_failed_jobs_summary(
    jobs: Sequence[Mapping[str, Any]], logs: Mapping[str, str]
) -> Dict[str, Any]: ...

def collect_branch_status(
    project_dir: Path, max_log_lines: int = 300
) -> BranchStatusReport:
    """Collect comprehensive branch status from all sources.
    Returns a BranchStatusReport dataclass (not a dict).
    """
```

Note: `format_for_llm()` is a **method** on `BranchStatusReport`, not a standalone function.

## HOW — Import adjustments (the main rewiring work)

Old mcp-coder imports → new mcp-workspace imports:

| Old import | New import |
|-----------|-----------|
| `mcp_coder.checks.ci_log_parser._build_ci_error_details` | `mcp_workspace.github_operations.ci_log_parser._build_ci_error_details` |
| `mcp_coder.checks.ci_log_parser._extract_failed_step_log` | `mcp_workspace.github_operations.ci_log_parser._extract_failed_step_log` |
| `mcp_coder.checks.ci_log_parser._find_log_content` | `mcp_workspace.github_operations.ci_log_parser._find_log_content` |
| `mcp_coder.checks.ci_log_parser._strip_timestamps` | `mcp_workspace.github_operations.ci_log_parser._strip_timestamps` |
| `mcp_coder.checks.ci_log_parser.truncate_ci_details` | `mcp_workspace.github_operations.ci_log_parser.truncate_ci_details` |
| `mcp_coder.mcp_workspace_git.extract_issue_number_from_branch` | `mcp_workspace.git_operations.branch_queries.extract_issue_number_from_branch` |
| `mcp_coder.mcp_workspace_git.get_current_branch_name` | `mcp_workspace.git_operations.get_current_branch_name` |
| `mcp_coder.mcp_workspace_git.needs_rebase` | `mcp_workspace.git_operations.workflows.needs_rebase` |
| `mcp_coder.utils.github_operations.ci_results_manager.CIResultsManager` | `mcp_workspace.github_operations.ci_results_manager.CIResultsManager` |
| `mcp_coder.utils.github_operations.issues.IssueData` | `mcp_workspace.github_operations.issues.IssueData` |
| `mcp_coder.utils.github_operations.issues.IssueManager` | `mcp_workspace.github_operations.issues.IssueManager` |
| `mcp_coder.workflow_utils.base_branch.detect_base_branch` | `mcp_workspace.git_operations.base_branch.detect_base_branch` |
| `mcp_coder.workflow_utils.task_tracker.TaskTrackerFileNotFoundError` | `mcp_workspace.workflows.task_tracker.TaskTrackerFileNotFoundError` |
| `mcp_coder.workflow_utils.task_tracker.TaskTrackerSectionNotFoundError` | `mcp_workspace.workflows.task_tracker.TaskTrackerSectionNotFoundError` |
| `mcp_coder.workflow_utils.task_tracker.TaskTrackerStatus` | `mcp_workspace.workflows.task_tracker.TaskTrackerStatus` |
| `mcp_coder.workflow_utils.task_tracker.get_task_counts` | `mcp_workspace.workflows.task_tracker.get_task_counts` |

Also note: `MERGE_BASE_DISTANCE_THRESHOLD` is imported in the mcp-coder version's `base_branch.py` but not directly in `branch_status.py`.

## ALGORITHM — `collect_branch_status` (pseudocode)

```
1. Get current branch via get_current_branch_name()
2. Fetch issue data once (IssueManager) for sharing between detect_base_branch and label lookup
3. Detect base branch via detect_base_branch(project_dir, branch_name, issue_data,
   issue_manager=issue_manager, pr_manager=pr_manager)  # DI from step 3
4. Collect CI status via CIResultsManager; if failed, _build_ci_error_details()
5. Check rebase status via needs_rebase()
6. Check task tracker via get_task_counts()
7. Collect GitHub label from issue_data
8. Generate recommendations based on all statuses
9. Return BranchStatusReport dataclass
```

Note: since `base_branch.py` now uses dependency injection (step 3), `branch_status.py` is the caller that constructs `IssueManager` and `PullRequestManager` and passes them to `detect_base_branch`.

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
    report = collect_branch_status(_project_dir, max_log_lines=max_log_lines)
    return report.format_for_llm()
```

Note: `format_for_llm()` is a method on `BranchStatusReport`, not a standalone function.

**Imports to add in `server.py`**:
```python
from mcp_workspace.checks.branch_status import collect_branch_status
```

## WHAT — Tests

**File**: `tests/checks/test_branch_status.py`

Copied 1:1 from mcp-coder's `tests/checks/test_branch_status.py`. Adjust imports:
- `from mcp_coder.checks.branch_status` → `from mcp_workspace.checks.branch_status`
- Mock paths adjusted accordingly (patch targets change to `mcp_workspace.*`)

**File**: `tests/checks/test_branch_status_pr_fields.py`

Copied 1:1 from mcp-coder's `tests/checks/test_branch_status_pr_fields.py`. Same import adjustments.

## DATA

`collect_branch_status` returns a `BranchStatusReport` dataclass:
```python
BranchStatusReport(
    branch_name="123-feature",
    base_branch="main",
    ci_status=CIStatus.PASSED,
    ci_details=None,
    rebase_needed=False,
    rebase_reason="Up to date with origin/main",
    tasks_status=TaskTrackerStatus.INCOMPLETE,
    tasks_reason="3 of 5 tasks complete",
    tasks_is_blocking=True,
    current_github_label="status-04:in-progress",
    recommendations=["Complete remaining tasks (3 of 5 tasks complete)"],
    pr_number=45,
    pr_url="https://github.com/...",
    pr_found=True,
)
```

`report.format_for_llm()` returns a compact formatted multi-line string optimized for LLM context windows.

## Commit

```
feat: add branch_status check and MCP tool

Move branch_status.py from mcp-coder checks into mcp_workspace.checks.
Expose as check_branch_status MCP tool. Rewire imports from
mcp_coder.mcp_workspace_git to mcp_workspace direct modules.
No logic changes.

Ref: #114
```
