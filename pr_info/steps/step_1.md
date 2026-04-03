# Step 1: File Search (Glob-Only) Mode

> **Context**: See [summary.md](summary.md) for overall design. This is step 1 of 3.

## LLM Prompt

Implement the glob-only file search mode for `search_files` in `src/mcp_workspace/file_tools/search.py` following TDD. Read `summary.md` for architecture context. Create the test file first, then implement the business logic. Run all quality checks after.

## WHERE

- **New**: `src/mcp_workspace/file_tools/search.py`
- **New**: `tests/file_tools/test_search.py`

## WHAT

### Business logic function

```python
# src/mcp_workspace/file_tools/search.py

def search_files(
    project_dir: Path,
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]:
    """Search file contents by regex and/or find files by glob pattern."""
```

### This step implements only:
- **Error case**: neither `glob` nor `pattern` provided → `ValueError`
- **File search mode** (`glob` provided, no `pattern`): return matching file paths
- Output limiting via `max_results` with `truncated` flag

## HOW

- Import `list_files` from `mcp_workspace.file_tools.directory_utils`
- Import `normalize_path` from `mcp_workspace.file_tools.path_utils`
- Use `list_files(".", project_dir=project_dir, use_gitignore=True)` to get all files
- Use `fnmatch.fnmatch(file_path, glob)` for glob filtering (uses `fnmatch` instead of `PurePath.match()` because `PurePath.match()` does not support recursive `**` patterns on Python 3.11)
- Import `fnmatch` from stdlib for glob matching
- No `@mcp.tool()` decorator — this is business logic only (wired in step 3)

## ALGORITHM (file search mode)

```
1. If neither glob nor pattern: raise ValueError
2. all_files = list_files(".", project_dir, use_gitignore=True)
3. If glob provided: matched = [f for f in all_files if fnmatch.fnmatch(f, glob)]
4. Uses `fnmatch.fnmatch()` instead of `PurePath.match()` because `PurePath.match()` does not support recursive `**` patterns on Python 3.11.
5. total = len(matched); truncate matched to max_results; set truncated = total > max_results
6. Return {"mode": "file_search", "files": matched[:max_results], "total_files": total, "truncated": truncated}
```

## DATA

### Return value (file search mode)
```python
{
    "mode": "file_search",
    "files": ["tests/test_server.py", "tests/test_log_utils.py"],
    "total_files": 2,
    "truncated": False
}
```

### Error case
```python
ValueError("At least one of 'glob' or 'pattern' must be provided")
```

## TESTS (`tests/file_tools/test_search.py`)

Use the existing `project_dir` fixture from `conftest.py` (provides isolated `tmp_path`).

Tests should create files in a dedicated subdirectory within `project_dir` and use assertions that account for pre-existing testdata files (e.g., check that expected files are a subset of results, or use a unique glob pattern that only matches test-created files).

1. `test_search_files_no_args_raises` — neither glob nor pattern → `ValueError`
2. `test_search_files_glob_finds_files` — create `.py` and `.txt` files, glob `**/*.py` returns only `.py` files
3. `test_search_files_glob_no_matches` — glob that matches nothing → empty `files` list
4. `test_search_files_glob_max_results` — create many files, verify `max_results` truncation and `truncated: True`
5. `test_search_files_glob_respects_gitignore` — create `.gitignore` with `*.log`, verify `.log` files excluded

## COMMIT

```
feat: add search_files glob-only file search mode
```
