# Step 4: Register `github_issue_view` and `github_issue_list` Tools in `server.py`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

> Implement Step 4 of issue #78 (see `pr_info/steps/summary.md`).
> Register `github_issue_view` and `github_issue_list` as MCP tools in `server.py`. These use `IssueManager` for data fetching and formatters from step 2 for output. Also update `tach.toml` to allow `server` → `github_operations` dependency, and add vulture whitelist entries. Write tests first (TDD), then implement. Run all code quality checks before committing.

## WHERE

- **Modify**: `src/mcp_workspace/server.py` (add 2 tool functions + imports)
- **Create**: `tests/github_operations/test_github_read_tools.py`
- **Modify**: `tach.toml` (add `github_operations` to server depends_on)
- **Modify**: `vulture_whitelist.py` (add 2 tool names)

## WHAT

### New tool functions in `server.py`

```python
@mcp.tool()
@log_function_call
def github_issue_view(
    number: int,
    include_comments: bool = True,
    max_lines: int = 200,
) -> str:
    """View a GitHub issue with full detail.

    Args:
        number: Issue number to view
        include_comments: Include issue comments (default: True)
        max_lines: Maximum output lines (default: 200)

    Returns:
        Formatted issue detail text, or error message string.
    """

@mcp.tool()
@log_function_call
def github_issue_list(
    state: str = "open",
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    since: Optional[str] = None,
    max_results: int = 30,
) -> str:
    """List GitHub issues with optional filters.

    Args:
        state: Filter by state - "open", "closed", or "all" (default: "open")
        labels: Filter by label names
        assignee: Filter by assignee username, "none", or "*"
        since: Only issues updated after this ISO datetime string
        max_results: Maximum results to return (default: 30)

    Returns:
        Compact summary lines, or error message string.
    """
```

## HOW

- Import `IssueManager` from `mcp_workspace.github_operations.issues`
- Import `format_issue_view`, `format_issue_list` from `mcp_workspace.github_operations.formatters`
- Each tool creates `IssueManager(project_dir=_project_dir)` inside a try/except
- Catches all exceptions → returns `f"Error: {e}"` as text string
- `since` parameter: parse ISO string to `datetime` in the tool function before passing to manager
- Does NOT use `_handle_github_errors` decorator — tool functions handle errors themselves

## ALGORITHM

### `github_issue_view`
```
try:
    manager = IssueManager(project_dir=_project_dir)
    issue = manager.get_issue(number)
    # Note: manager.get_issue() is decorated with _handle_github_errors which
    # returns empty IssueData (number=0) on 404 instead of raising an exception.
    if not issue["number"]: return f"Error: Issue #{number} not found"
    comments = manager.get_comments(number) if include_comments else []
    return format_issue_view(issue, comments, max_lines)
except Exception as e:
    return f"Error: {e}"
```

### `github_issue_list`
```
try:
    manager = IssueManager(project_dir=_project_dir)
    since_dt = datetime.fromisoformat(since) if since else None
    issues = manager.list_issues(state=state, labels=labels, assignee=assignee,
                                  since=since_dt, max_results=max_results)
    return format_issue_list(issues, max_results)
except Exception as e:
    return f"Error: {e}"
```

## DATA

- `github_issue_view` returns: formatted text string (issue detail) or `"Error: ..."`
- `github_issue_list` returns: compact summary text or `"Error: ..."`

## CONFIG CHANGES

### `tach.toml` — add to server module

```toml
[[modules]]
path = "mcp_workspace.server"
layer = "protocol"
depends_on = [
    { path = "mcp_workspace.file_tools" },
    { path = "mcp_workspace.git_operations" },
    { path = "mcp_workspace.github_operations" },   # NEW
    { path = "mcp_workspace.reference_projects" },
    { path = "mcp_workspace.server_reference_tools" },
    { path = "mcp_coder_utils.log_utils" },
]
```

### `vulture_whitelist.py` — add under GitHub tools section

```python
# GitHub read-only tools registered in server.py
_.github_issue_view
_.github_issue_list
```

## TESTS

In `tests/github_operations/test_github_read_tools.py`:

### `github_issue_view`
1. `test_github_issue_view_basic` — returns formatted text with title, state, body
2. `test_github_issue_view_with_comments` — comments included when `include_comments=True`
3. `test_github_issue_view_without_comments` — no comments when `include_comments=False`
4. `test_github_issue_view_not_found` — returns error text when issue number=0 (empty IssueData)
5. `test_github_issue_view_error` — returns `"Error: ..."` on exception

### `github_issue_list`
1. `test_github_issue_list_basic` — returns compact summary lines
2. `test_github_issue_list_empty` — returns "No issues found."
3. `test_github_issue_list_with_filters` — verifies labels/assignee/since passed through
4. `test_github_issue_list_error` — returns `"Error: ..."` on exception

### Test approach
- Mock `IssueManager` class (patch constructor + methods)
- Set `_project_dir` module variable before calling tool functions
- Verify formatter output contains expected content (not exact string matching)

## COMMIT

```
feat(github): add github_issue_view and github_issue_list MCP tools (#78)
```
