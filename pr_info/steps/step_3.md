# Step 3: Wire Up MCP Tool

> **Context**: See [summary.md](summary.md) for overall design. This is step 3 of 3. Steps 1-2 implemented all business logic and tests.

## LLM Prompt

Wire up `search_files` as an MCP tool in `server.py`, export from `file_tools/__init__.py`, and add to vulture whitelist. Read `summary.md` for architecture. Run all quality checks after.

## WHERE

- **Modify**: `src/mcp_workspace/file_tools/__init__.py`
- **Modify**: `src/mcp_workspace/server.py`
- **Modify**: `vulture_whitelist.py`

## WHAT

### `file_tools/__init__.py`
```python
from mcp_workspace.file_tools.search import search_files
# Add "search_files" to __all__
```

### `server.py` — new MCP tool function
```python
@mcp.tool()
@log_function_call
def search_files(
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]:
    """Search file contents by regex and/or find files by glob pattern.
    
    Modes:
        - File search: provide `glob` to find files by path pattern (like find)
        - Content search: provide `pattern` (regex) to search inside files (like grep)
        - Combined: both to search content within matching files
    
    Args:
        glob: File path pattern (e.g. "**/*.py", "tests/**/test_*.py")
        pattern: Regex to match file contents (e.g. "def foo", "TODO.*fix")
        context_lines: Lines of context around each match (0 = match line only)
        max_results: Maximum number of matches or files returned (default 50)
        max_result_lines: Hard cap on total output lines (default 200)
    
    Returns:
        Dict with matches (content search) or file list (file search),
        plus truncated flag if results were capped.
    """
```

### `vulture_whitelist.py`
```python
_.search_files  # under MCP Server Tool Handlers section
```

## HOW

- Import `search_files as search_files_util` from `mcp_workspace.file_tools` (follows existing pattern)
- Validate `_project_dir is not None`, then delegate to `search_files_util(project_dir=_project_dir, ...)`
- No gitignore check needed at server layer — `list_files()` in the business logic already handles it

## ALGORITHM

```
1. Validate _project_dir is set
2. Delegate to search_files_util(project_dir=_project_dir, glob=glob, pattern=pattern, ...)
3. Return result dict
```

## DATA

Pass-through of the return values from `search_files_util` (see steps 1 and 2).

## TESTS

No new test file. The existing `tests/test_server.py` pattern tests MCP tools at integration level. The business logic is fully tested in `tests/file_tools/test_search.py` from steps 1-2. If `test_server.py` has a pattern for testing tool registration, follow it; otherwise the tool wiring is straightforward delegation and covered by quality checks.

## COMMIT

```
feat: wire up search_files as MCP tool
```
