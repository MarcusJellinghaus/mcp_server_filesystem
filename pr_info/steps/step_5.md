# Step 5: Wire into server.py — path and dirs_only parameters

**Summary:** [summary.md](summary.md)

## LLM Prompt

> Implement Step 5 of the plan in `pr_info/steps/step_5.md`.
> Read the summary at `pr_info/steps/summary.md` for full context.
> Follow TDD: write tests first, then implement, then run all checks.

## Goal

Add `path` and `dirs_only` parameters to the `list_directory()` MCP tool in `server.py`. This wires the tree listing logic into the public API.

## WHERE

- **Modify:** `src/mcp_workspace/server.py` — update `list_directory()` signature and body
- **Modify:** `tests/test_server.py` — add tests for new parameters

## WHAT

### Updated `list_directory` signature

```python
@mcp.tool()
@log_function_call
def list_directory(path: str = ".", dirs_only: bool = False) -> List[str]:
```

### Updated docstring

```python
"""List files and directories in the project directory.

Args:
    path: Scope listing to a subtree (relative to project root).
        Defaults to "." (entire project).
    dirs_only: Show only directories, each with trailing "/".

Returns:
    A list of filenames in the project directory
"""
```

## HOW

### Imports to add in `server.py`

```python
from mcp_workspace.file_tools import list_directory_tree
```

### Integration

```python
@mcp.tool()
@log_function_call
def list_directory(path: str = ".", dirs_only: bool = False) -> List[str]:
    if _project_dir is None:
        raise ValueError("Project directory has not been set")

    # Validate path — normalize_path handles traversal attacks
    abs_path, rel_path = normalize_path(path, _project_dir)

    # If path points to a file, return error
    if abs_path.is_file():
        raise ValueError(f"'{path}' is a file, not a directory. Use read_file() instead.")

    # Get raw file list (unchanged call)
    raw_files = list_files_util(path, project_dir=_project_dir, use_gitignore=True)

    # Build tree, collapse, render, truncate
    return list_directory_tree(raw_files, base_path=rel_path, dirs_only=dirs_only)
```

## ALGORITHM

```
validate _project_dir is set
abs_path, rel_path = normalize_path(path, _project_dir)
if abs_path.is_file(): raise ValueError("path is a file")
raw_files = list_files_util(path, project_dir, use_gitignore=True)
return list_directory_tree(raw_files, base_path=rel_path, dirs_only=dirs_only)
```

## DATA

- `list_directory()` → same as today (backward compatible)
- `list_directory(path="src")` → files under `src/`, paths relative to project root but with `src/` prefix stripped
- `list_directory(dirs_only=True)` → directory paths with trailing `/`
- `list_directory(path="README.md")` → `ValueError: 'README.md' is a file`

## TESTS (in `test_server.py`)

1. **Default call unchanged** — `list_directory()` returns file list (backward compatible)
2. **path parameter** — `list_directory(path="src")` scopes to subtree
3. **dirs_only parameter** — `list_directory(dirs_only=True)` returns only dir paths
4. **path points to file** — raises `ValueError` with "is a file" message
5. **path does not exist** — raises `FileNotFoundError` (from `list_files`)
6. **path traversal blocked** — `list_directory(path="../../etc")` raises `ValueError` (from `normalize_path`)

## DONE WHEN

- `list_directory()` with no args behaves identically to before
- `path` scopes listing to subtree
- `dirs_only=True` returns directory paths
- File path and traversal errors handled
- pylint, mypy, pytest all green
- **All CLAUDE.md requirements followed**
