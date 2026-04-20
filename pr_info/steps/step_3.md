# Step 3: Add base_branch detection and get_base_branch MCP tool

> See [summary.md](./summary.md) for full context. This is step 3 of 6.

## Goal

Move `base_branch.py` from mcp-coder `workflow_utils/` into `mcp_workspace/git_operations/`. Then expose `detect_base_branch()` as the `get_base_branch` MCP tool in `server.py`. No new packages needed (target package exists).

## LLM Prompt

```
Implement step 3 from pr_info/steps/step_3.md. Read pr_info/steps/summary.md for context.
Copy base_branch.py from mcp-coder's src/mcp_coder/workflow_utils/base_branch.py into
src/mcp_workspace/git_operations/base_branch.py. Adjust imports only.
Copy the test file. Add the get_base_branch MCP tool to server.py. All checks must pass.
```

## WHERE

| Action | Path |
|--------|------|
| Create | `src/mcp_workspace/git_operations/base_branch.py` |
| Create | `tests/git_operations/test_base_branch.py` |
| Modify | `src/mcp_workspace/server.py` — add `get_base_branch` tool |
| Modify | `vulture_whitelist.py` — add `get_base_branch` |

## WHAT — Source module

**File**: `src/mcp_workspace/git_operations/base_branch.py`

Copied from mcp-coder with **one logic change**: dependency injection for github_operations objects.

Actual signature in mcp-coder:

```python
def detect_base_branch(
    project_dir: Path,
    current_branch: Optional[str] = None,
    issue_data: Optional[IssueData] = None,
) -> Optional[str]:
    """Detect the base branch for the current feature branch.

    Detection priority:
    1. Linked issue's `### Base Branch` section (explicit user intent)
    2. GitHub PR base branch (if open PR exists for current branch)
    3. Git merge-base (heuristic fallback from git history)
    4. Default branch (main/master)
    5. None if all detection fails

    Returns:
        Branch name string, or None if detection fails.
    """
```

**Dependency injection change**: The mcp-coder version internally imports and constructs `IssueManager` and `PullRequestManager` from `github_operations`. Since `git_operations/` is **below** `github_operations/` in the layer hierarchy, we cannot have upward imports. Instead:
- Add optional parameters for the github_operations objects that the internal helpers need:
  ```python
  def detect_base_branch(
      project_dir: Path,
      current_branch: Optional[str] = None,
      issue_data: Optional[IssueData] = None,
      issue_manager: Optional["IssueManager"] = None,
      pr_manager: Optional["PullRequestManager"] = None,
  ) -> Optional[str]:
  ```
- `_detect_from_issue()` uses the passed `issue_manager` instead of constructing one internally
- `_detect_from_pr()` uses the passed `pr_manager` instead of constructing one internally
- If the optional params are None, the helpers skip those detection steps (the caller in `branch_status.py` constructs and passes them)
- Remove the direct imports of `IssueManager`, `PullRequestManager`, `IssueData` from base_branch.py (use TYPE_CHECKING only for type hints)

This is the **one logic change** justified by architecture boundary enforcement.

## HOW — Import adjustments in source

Old mcp-coder imports → new mcp-workspace imports:

| Old import | New import |
|-----------|-----------|
| `mcp_coder.mcp_workspace_git.MERGE_BASE_DISTANCE_THRESHOLD` | `mcp_workspace.git_operations.parent_branch_detection.MERGE_BASE_DISTANCE_THRESHOLD` |
| `mcp_coder.mcp_workspace_git.detect_parent_branch_via_merge_base` | `mcp_workspace.git_operations.parent_branch_detection.detect_parent_branch_via_merge_base` |
| `mcp_coder.mcp_workspace_git.extract_issue_number_from_branch` | `mcp_workspace.git_operations.branch_queries.extract_issue_number_from_branch` |
| `mcp_coder.mcp_workspace_git.get_current_branch_name` | `mcp_workspace.git_operations.get_current_branch_name` |
| `mcp_coder.mcp_workspace_git.get_default_branch_name` | `mcp_workspace.git_operations.get_default_branch_name` |
| `mcp_coder.utils.github_operations.issues.IssueData` | **REMOVED** (TYPE_CHECKING only for type hints) |
| `mcp_coder.utils.github_operations.issues.IssueManager` | **REMOVED** (TYPE_CHECKING only for type hints) |
| `mcp_coder.utils.github_operations.pr_manager.PullRequestManager` | **REMOVED** (TYPE_CHECKING only for type hints) |

**Key rule**: base_branch.py must NOT import from `github_operations` at runtime. Use `TYPE_CHECKING` for type hints only.

## ALGORITHM — `detect_base_branch` (pseudocode)

```
1. If current_branch is None: get via get_current_branch_name(project_dir)
2. If still None (detached HEAD): return None
3. Try issue base_branch: if issue_data provided, check base_branch field;
   else if issue_manager provided, extract issue number from branch, fetch issue
4. Try PR lookup: if pr_manager provided, find open PR for current branch
5. Try git merge-base: detect_parent_branch_via_merge_base()
6. Try default branch: get_default_branch_name()
7. Return None if all fail
```

## WHAT — MCP tool wrapper in `server.py`

```python
@mcp.tool()
@log_function_call
def get_base_branch() -> str:
    """Detect the base branch for the current branch.

    Returns:
        Branch name string. Returns default branch name if detection fails.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    from mcp_workspace.github_operations.issues import IssueManager
    from mcp_workspace.github_operations.pr_manager import PullRequestManager

    issue_manager = IssueManager(project_dir=_project_dir)
    pr_manager = PullRequestManager(_project_dir)
    result = detect_base_branch(
        _project_dir,
        issue_manager=issue_manager,
        pr_manager=pr_manager,
    )
    if result is None:
        # Fallback: return "main" as safe default
        return "main"
    return result
```

The tool wrapper constructs the github_operations objects and passes them into `detect_base_branch` via dependency injection. It also handles the `Optional[str]` return by defaulting to `"main"`.

**Import to add in `server.py`**:
```python
from mcp_workspace.git_operations.base_branch import detect_base_branch
```

## WHAT — Tests

**File**: `tests/git_operations/test_base_branch.py`

Copied 1:1 from mcp-coder's `tests/workflow_utils/test_base_branch.py`. Only adjust imports:
- `from mcp_coder.workflow_utils.base_branch` → `from mcp_workspace.git_operations.base_branch`

## DATA

`detect_base_branch` returns: `Optional[str]` — the branch name (e.g., `"main"`, `"develop"`, `"feature/parent"`), or `None` if all detection methods fail.

The MCP tool wrapper handles `None` by returning `"main"` as a safe default.

## Commit

```
feat: add base_branch detection and MCP tool

Move base_branch.py from mcp-coder workflow_utils into
mcp_workspace.git_operations. Expose as get_base_branch MCP tool.
Apply dependency injection for github_operations objects
(architecture boundary enforcement). No other logic changes.

Ref: #114
```
