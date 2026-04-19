# Step 4: MCP Server Wrappers + Config Updates

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## LLM Prompt

```
Implement step 4 of issue #77 (read-only git operations).
Read pr_info/steps/summary.md for context, then read this step file.
Add thin MCP tool wrappers in server.py, update tach.toml and vulture_whitelist.py,
and add server-level tests. Follow TDD.
Run all code quality checks after implementation. Produce one commit.
```

## WHERE

- **Modify**: `src/mcp_workspace/server.py` — add 4 tool wrappers + imports
- **Modify**: `tach.toml` — add git_operations dependency for server module
- **Modify**: `vulture_whitelist.py` — add 4 new tool names
- **Modify**: `tests/test_server.py` — add tests for new wrappers

## WHAT

### `server.py` — New Imports

```python
from mcp_workspace.git_operations.read_operations import (
    git_diff as git_diff_impl,
    git_log as git_log_impl,
    git_merge_base as git_merge_base_impl,
    git_status as git_status_impl,
)
```

### `server.py` — 4 New Tool Functions

```python
@mcp.tool()
@log_function_call
def git_log(
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    max_lines: int = 50,
) -> str:
    """Run git log with filtering support."""

@mcp.tool()
@log_function_call
def git_diff(
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: int = 100,
    compact: bool = True,
) -> str:
    """Run git diff with compact diff and filtering support."""

@mcp.tool()
@log_function_call
def git_status(
    args: Optional[List[str]] = None,
    max_lines: int = 200,
) -> str:
    """Run git status."""

@mcp.tool()
@log_function_call
def git_merge_base(
    args: Optional[List[str]] = None,
) -> str:
    """Run git merge-base."""
```

## HOW

### Server Wrappers Pattern

Each wrapper follows the same thin pattern (matching existing tools like `read_file`):

```python
@mcp.tool()
@log_function_call
def git_log(
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    max_lines: int = 50,
) -> str:
    """Run git log with filtering support. [full docstring]"""
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    return git_log_impl(
        project_dir=_project_dir,
        args=args,
        pathspec=pathspec,
        search=search,
        max_lines=max_lines,
    )
```

All 4 wrappers: validate `_project_dir`, then delegate to `git_operations.read_operations`.

### `tach.toml` Change

Add `git_operations` to `server.py` module's `depends_on`:

```toml
[[modules]]
path = "mcp_workspace.server"
layer = "protocol"
depends_on = [
    { path = "mcp_workspace.file_tools" },
    { path = "mcp_workspace.git_operations" },  # NEW
    { path = "mcp_coder_utils.log_utils" },
]
```

### `vulture_whitelist.py` Addition

Under the existing `# MCP Server Tool Handlers` section:

```python
# Git read-only operation tools registered in server.py
_.git_log
_.git_diff
_.git_status
_.git_merge_base
```

## DATA

### Return Values

All wrappers return `str` (delegated from read_operations).

## TEST CASES (`tests/test_server.py` additions)

Tests mock the implementation functions to test the wrappers in isolation (no git repo needed). Follow existing test patterns in `test_server.py`.

```python
class TestGitLogTool:
    def test_delegates_to_impl(): ...          # verify impl called with correct args
    def test_raises_without_project_dir(): ... # _project_dir is None → ValueError

class TestGitDiffTool:
    def test_delegates_to_impl(): ...
    def test_raises_without_project_dir(): ...

class TestGitStatusTool:
    def test_delegates_to_impl(): ...
    def test_raises_without_project_dir(): ...

class TestGitMergeBaseTool:
    def test_delegates_to_impl(): ...
    def test_raises_without_project_dir(): ...
```

The `setup_server` fixture (already exists) sets `_project_dir` via `set_project_dir()`. Tests that verify the "no project dir" case temporarily reset it.
