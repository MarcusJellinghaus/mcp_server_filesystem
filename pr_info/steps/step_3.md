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

Copied 1:1 from mcp-coder. Key function:

```python
def detect_base_branch(project_dir: Path) -> str:
    """Detect the base branch for the current branch.

    Returns branch name string. On default branch, returns that branch name
    (pass-through, matching CLI behavior).
    """
```

## HOW — Import adjustments in source

- `from mcp_coder.mcp_workspace_git` → direct imports from `mcp_workspace.git_operations` (e.g., `get_current_branch_name`, `get_default_branch_name`)
- Uses `parent_branch_detection.detect_parent_branch_via_merge_base` (already exists in mcp-workspace at `mcp_workspace.git_operations.parent_branch_detection`)

## ALGORITHM — `detect_base_branch` (pseudocode)

```
1. current = get_current_branch_name(project_dir)
2. default = get_default_branch_name(project_dir)
3. If current == default or current is None: return default (or "main")
4. parent = detect_parent_branch_via_merge_base(project_dir, current)
5. Return parent if found, else default (or "main")
```

## WHAT — MCP tool wrapper in `server.py`

```python
@mcp.tool()
@log_function_call
def get_base_branch() -> str:
    """Detect the base branch for the current branch.

    Returns:
        Branch name string (pass-through from detect_base_branch).
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    return detect_base_branch(_project_dir)
```

**Import to add in `server.py`**:
```python
from mcp_workspace.git_operations.base_branch import detect_base_branch
```

## WHAT — Tests

**File**: `tests/git_operations/test_base_branch.py`

Copied 1:1 from mcp-coder's `tests/workflow_utils/test_base_branch.py`. Only adjust imports:
- `from mcp_coder.workflow_utils.base_branch` → `from mcp_workspace.git_operations.base_branch`

## DATA

Returns: plain `str` — the branch name (e.g., `"main"`, `"develop"`, `"feature/parent"`).

## Commit

```
feat: add base_branch detection and MCP tool

Move base_branch.py from mcp-coder workflow_utils into
mcp_workspace.git_operations. Expose as get_base_branch MCP tool.
Adjust imports only, no logic changes.

Ref: #114
```
