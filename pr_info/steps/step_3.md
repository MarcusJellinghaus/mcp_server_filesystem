# Step 3: Unified `git()` Dispatcher

## Context
See [summary.md](./summary.md) for full context. This step adds the unified `git()` function that routes to all 11 commands.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.
Implement Step 3: add unified git() dispatcher in read_operations.py, with tests.
Follow TDD — write tests first, then implementation. Run all three quality checks after.
```

## WHERE
- `src/mcp_workspace/git_operations/read_operations.py` — add `git()` function
- `tests/git_operations/test_read_operations.py` — add tests

## WHAT

### `git()` — unified dispatcher
```python
def git(
    command: str,
    project_dir: Path,
    args: Optional[list[str]] = None,
    pathspec: Optional[list[str]] = None,
    search: Optional[str] = None,
    context: int = 3,
    max_lines: Optional[int] = None,
    compact: bool = True,
) -> str:
```

### Per-command defaults dict
```python
_DEFAULT_MAX_LINES: dict[str, int] = {
    "log": 50,
    "diff": 100,
    "status": 200,
}
# All others default to 100
```

### Parameter support matrix (for soft warnings)
```python
_SUPPORTS_SEARCH: frozenset[str] = frozenset({"log", "diff", "show"})
_SUPPORTS_COMPACT: frozenset[str] = frozenset({"diff", "show"})
_SUPPORTS_PATHSPEC: frozenset[str] = frozenset({"log", "diff", "show", "status", "ls_tree", "ls_files"})
_SUPPORTS_CONTEXT: frozenset[str] = frozenset({"diff", "show"})
```

## HOW
- Dict mapping command → callable (function reference or lambda wrapping `_run_simple_command`)
- Soft warnings collected in a list, prepended to output
- `max_lines` resolved: if `None`, use `_DEFAULT_MAX_LINES.get(command, 100)`
- Unknown command → raise `ValueError`

## ALGORITHM
```
1. Resolve max_lines from defaults if None
2. Collect soft warnings for unsupported params (search, compact, pathspec, context)
3. Look up command in handler dict
4. If not found: raise ValueError("Unknown git command: '{command}'")
5. Call handler with applicable params
6. If warnings: prepend warning lines to output
7. Return output
```

## DATA
- Returns `str` (output with optional warning prefix)
- Soft warning format: `"⚠ '{param}' is not supported for git {command} and was ignored.\n"`
- Multiple warnings on separate lines, blank line before output

### Command → handler mapping
```python
_HANDLERS = {
    "log": lambda: git_log(project_dir, args, pathspec, search, max_lines),
    "diff": lambda: git_diff(project_dir, args, pathspec, search, context, max_lines, compact),
    "status": lambda: _run_simple_command("status", project_dir, "status", args, pathspec, max_lines, "No changes found"),
    "merge_base": lambda: git_merge_base(project_dir, args),
    "show": lambda: git_show(project_dir, args, pathspec, search, context, max_lines, compact),
    "branch": lambda: git_branch(project_dir, args, max_lines),
    "fetch": lambda: _run_simple_command("fetch", project_dir, "fetch", args, None, max_lines, "Fetch complete (no output)."),
    "rev_parse": lambda: _run_simple_command("rev_parse", project_dir, "rev_parse", args, None, max_lines),
    "ls_tree": lambda: _run_simple_command("ls_tree", project_dir, "ls_tree", args, pathspec, max_lines),
    "ls_files": lambda: _run_simple_command("ls_files", project_dir, "ls_files", args, pathspec, max_lines),
    "ls_remote": lambda: _run_simple_command("ls_remote", project_dir, "ls_remote", args, None, max_lines),
}
```
Note: The actual implementation will use an inner dispatch pattern (not lambdas with closures) — this pseudocode shows the routing logic.

## TESTS (write first)

### `TestGitDispatcher` (unit tests, mocked implementations)

- `test_routes_to_log` — command="log" calls git_log with correct params
- `test_routes_to_diff` — command="diff" calls git_diff with correct params
- `test_routes_to_status` — command="status" calls _run_simple_command
- `test_routes_to_merge_base` — command="merge_base" calls git_merge_base
- `test_routes_to_show` — command="show" calls git_show
- `test_routes_to_branch` — command="branch" calls git_branch
- `test_routes_to_fetch` — command="fetch" calls _run_simple_command with git_method="fetch"
- `test_unknown_command_raises` — command="push" raises ValueError
- `test_default_max_lines_log` — log gets 50 when max_lines=None
- `test_default_max_lines_diff` — diff gets 100 when max_lines=None
- `test_default_max_lines_status` — status gets 200 when max_lines=None
- `test_default_max_lines_other` — fetch gets 100 when max_lines=None
- `test_explicit_max_lines_overrides` — explicit max_lines=25 passed through
- `test_soft_warning_search_on_status` — search param on status produces warning in output
- `test_soft_warning_compact_on_log` — compact=False on log produces warning
- `test_soft_warning_pathspec_on_fetch` — pathspec on fetch produces warning
- `test_no_warning_for_defaults` — compact=True (default) on log does NOT warn
- `test_no_warning_for_supported_params` — search on diff does NOT warn
