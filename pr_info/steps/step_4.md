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

Copied 1:1 from mcp-coder. Key dataclasses and functions:

```python
@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: Path
    line_count: int

@dataclass
class CheckResult:
    """Result of file size check."""
    passed: bool
    violations: list[FileMetrics]
    total_files_checked: int
    allowlisted_count: int
    stale_entries: list[str]

def count_lines(file_path: Path) -> int:
    """Count lines in a file. Returns -1 for binary/non-UTF-8."""

def load_allowlist(allowlist_path: Path) -> set[str]:
    """Load allowlist from file. Returns set of normalized path strings."""

def get_file_metrics(files: list[Path], project_dir: Path) -> list[FileMetrics]:
    """Get file metrics for a list of files."""

def check_file_sizes(
    project_dir: Path,
    max_lines: int,
    allowlist: set[str],
) -> CheckResult:
    """Check file sizes against maximum line limit.
    Note: allowlist is REQUIRED (no default). max_lines has no default.
    Returns CheckResult dataclass, not a raw list.
    """

def render_output(result: CheckResult, max_lines: int) -> str:
    """Render check result for terminal output.
    Takes a CheckResult dataclass, not a raw list of violations.
    """

def render_allowlist(violations: list[FileMetrics]) -> str:
    """Render violations as allowlist entries."""
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
1. files = list_files(".", project_dir) — get all project files
2. metrics = get_file_metrics(files, project_dir) — count lines for each
3. For each file over max_lines: if path in allowlist, count as allowlisted; else add to violations
4. Detect stale allowlist entries (file doesn't exist or is under limit)
5. Sort violations by line_count descending
6. Return CheckResult(passed, violations, total_files_checked, allowlisted_count, stale_entries)
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
    allowlist_path = _project_dir / ".large-files-allowlist"
    allowlist = load_allowlist(allowlist_path)
    result = check_file_sizes(_project_dir, max_lines=max_lines, allowlist=allowlist)
    return render_output(result, max_lines)
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

`check_file_sizes` returns a `CheckResult` dataclass:
```python
CheckResult(
    passed=False,
    violations=[FileMetrics(path=Path("src/server.py"), line_count=812)],
    total_files_checked=45,
    allowlisted_count=2,
    stale_entries=["old_file.py"],
)
```

`render_output` returns a formatted string like:
```
File size check failed: 1 file(s) exceed 600 lines

Violations:
  - src/server.py: 812 lines

Consider refactoring these files or adding them to the allowlist.
```

## Commit

```
feat: add file_sizes check and MCP tool

Move file_sizes.py from mcp-coder checks into mcp_workspace.checks.
Expose as check_file_size MCP tool. Auto-loads .large-files-allowlist.
Adjust imports only, no logic changes.

Ref: #114
```
