# Step 4: Replace Server Tools + Update Vulture Whitelist

## Context
See [summary.md](./summary.md) for full context. This step replaces the 4 separate git tool registrations in `server.py` with the single unified `git` tool and updates the vulture whitelist.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for context.
Implement Step 4: replace 4 git tool registrations in server.py with unified git tool, update test_server.py, update vulture_whitelist.py.
Run all three quality checks after.
```

## WHERE
- `src/mcp_workspace/server.py` — replace 4 tools with 1
- `tests/test_server.py` — replace 4 test classes with 1
- `vulture_whitelist.py` — update entries

## WHAT

### Remove from `server.py`:
- `git_log()` tool function
- `git_diff()` tool function
- `git_status()` tool function
- `git_merge_base()` tool function
- Imports: `git_log_impl`, `git_diff_impl`, `git_status_impl`, `git_merge_base_impl`

### Add to `server.py`:
```python
from mcp_workspace.git_operations.read_operations import git as git_impl

@mcp.tool()
@log_function_call
def git(
    command: str,
    args: Optional[List[str]] = None,
    pathspec: Optional[List[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: Optional[int] = None,
    compact: bool = True,
) -> str:
    """Run a read-only git command.

    Args:
        command: Git subcommand (log, diff, status, merge_base, fetch,
            show, branch, rev_parse, ls_tree, ls_files, ls_remote).
        args: Optional CLI flags (validated against per-command security allowlists).
        pathspec: Optional file paths appended after --.
        search: Optional regex to filter output (log, diff, show only).
        context: Lines of context around search matches (default 3).
        max_lines: Maximum output lines. Per-command defaults: log=50, diff=100, status=200, others=100.
        compact: If True, apply compact diff rendering (diff, show only).

    Returns:
        Command output, optionally filtered/truncated.
    """
    if _project_dir is None:
        raise ValueError("Project directory has not been set")
    return git_impl(
        command=command,
        project_dir=_project_dir,
        args=args,
        pathspec=pathspec,
        search=search,
        context=context,
        max_lines=max_lines,
        compact=compact,
    )
```

### Update `vulture_whitelist.py`:
```python
# REMOVE:
_.git_log
_.git_diff
_.git_status
_.git_merge_base

# ADD:
_.git
```

## HOW
- Single import replaces 4 imports
- Single tool function replaces 4 tool functions
- Signature matches the unified `git()` dispatcher from step 3
- Docstring describes all 11 commands and parameter applicability

## TESTS

### Replace in `test_server.py`:
Remove `TestGitLogTool`, `TestGitDiffTool`, `TestGitStatusTool`, `TestGitMergeBaseTool`.

Add `TestGitTool`:
```python
class TestGitTool:
    @patch("mcp_workspace.server.git_impl")
    def test_delegates_to_impl(self, mock_impl, project_dir):
        """Verify git() delegates all params to git_impl."""
        mock_impl.return_value = "output"
        result = git(
            command="log",
            args=["--oneline"],
            pathspec=["src/"],
            search="fix",
            context=5,
            max_lines=25,
            compact=False,
        )
        assert result == "output"
        mock_impl.assert_called_once_with(
            command="log",
            project_dir=project_dir,
            args=["--oneline"],
            pathspec=["src/"],
            search="fix",
            context=5,
            max_lines=25,
            compact=False,
        )

    def test_raises_without_project_dir(self):
        """git() raises ValueError when _project_dir is None."""
        # same pattern as existing tests
```

### Update imports in `test_server.py`:
```python
# REMOVE: git_diff, git_log, git_merge_base, git_status
# ADD: git
from mcp_workspace.server import (
    ...,
    git,
    ...,
)
```

## DATA
- No new data structures
- Return type: `str`
