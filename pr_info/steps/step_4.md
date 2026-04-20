# Step 4: Add file_sizes check and check_file_size MCP tool

> See [summary.md](./summary.md) for full context. This is step 4 of 6.

## Goal

Move `file_sizes.py` from mcp-coder `checks/` into `mcp_workspace/checks/`. Then expose as the `check_file_size` MCP tool in `server.py`. Creates the new `checks/` package.

## LLM Prompt

```
Implement step 4 from pr_info/steps/step_4.md. Read pr_info/steps/summary.md for context.
Copy file_sizes.py from mcp-coder's src/mcp_coder/checks/file_sizes.py into
src/mcp_workspace/checks/file_sizes.py. Adjust imports only — use list_files from
mcp_workspace.file_tools.directory_utils directly. Auto-load .large-files-allowlist
from project root. Add the check_file_size MCP tool to server.py. All checks must pass.
```

## WHERE

| Action | Path |
|--------|------|
| Create | `src/mcp_workspace/checks/__init__.py` |
| Create | `src/mcp_workspace/checks/file_sizes.py` |
| Create | `tests/checks/__init__.py` |
| Create | `tests/checks/test_file_sizes.py` |
| Modify | `src/mcp_workspace/server.py` — add `check_file_size` tool |
| Modify | `vulture_whitelist.py` — add `check_file_size` |

## WHAT — Source module

**File**: `src/mcp_workspace/checks/file_sizes.py`

Copied 1:1 from mcp-coder. Key functions:

```python
def load_allowlist(project_dir: Path) -> set[str]:
    """Load .large-files-allowlist from project root. Returns set of relative paths."""

def check_file_sizes(
    project_dir: Path,
    max_lines: int = 600,
    allowlist: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Check all tracked files against max_lines threshold.
    Returns list of violations: [{"path": str, "lines": int}].
    """

def render_output(violations: list[dict[str, Any]], max_lines: int) -> str:
    """Format violations into human-readable output string."""
```

## WHAT — Package init

**File**: `src/mcp_workspace/checks/__init__.py`

```python
"""Checks package — branch status, file size, and other project checks."""
```

## HOW — Import adjustments in source

- `from mcp_coder.mcp_workspace_git` (list_files wrapper) → `from mcp_workspace.file_tools.directory_utils import list_files` (direct import, no wrapper needed in-package)
- Allowlist loaded from `project_dir / ".large-files-allowlist"` (same as CLI behavior)

## ALGORITHM — `check_file_sizes` (pseudocode)

```
1. all_files = list_files(".", project_dir, use_gitignore=True)
2. allowlist = load_allowlist(project_dir) if not provided
3. For each file, count lines; if lines > max_lines and path not in allowlist:
4.   Append {"path": rel_path, "lines": count} to violations
5. Sort violations by line count descending
6. Return violations list
```

## WHAT — MCP tool wrapper in `server.py`

```python
@mcp.tool()
@log_function_call
def check_file_size(max_lines: int = 600) -> str:
    """Check file line counts against threshold.

    Args:
        max_lines: Maximum allowed lines per file (default 600).

    Returns:
        Formatted report of files exceeding the threshold.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    allowlist = load_allowlist(_project_dir)
    violations = check_file_sizes(_project_dir, max_lines=max_lines, allowlist=allowlist)
    return render_output(violations, max_lines)
```

**Imports to add in `server.py`**:
```python
from mcp_workspace.checks.file_sizes import check_file_sizes, load_allowlist, render_output
```

## WHAT — Tests

**File**: `tests/checks/test_file_sizes.py`

Copied 1:1 from mcp-coder's `tests/checks/test_file_sizes.py`. Only adjust imports:
- `from mcp_coder.checks.file_sizes` → `from mcp_workspace.checks.file_sizes`

## DATA

`check_file_sizes` returns:
```python
[
    {"path": "src/mcp_workspace/server.py", "lines": 812},
    {"path": "src/mcp_workspace/some_big_file.py", "lines": 650},
]
```

`render_output` returns a formatted string like:
```
2 files exceed 600 lines:
  src/mcp_workspace/server.py: 812 lines
  src/mcp_workspace/some_big_file.py: 650 lines
```

## Commit

```
feat: add file_sizes check and MCP tool

Move file_sizes.py from mcp-coder checks into mcp_workspace.checks.
Expose as check_file_size MCP tool. Auto-loads .large-files-allowlist.
Adjust imports only, no logic changes.

Ref: #114
```
