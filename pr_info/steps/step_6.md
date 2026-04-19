# Step 6: `server.py` — `search_reference_files()` Tool + API Response Update

## LLM Prompt

> Implement Step 6 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Add `search_reference_files()` MCP tool and update `get_reference_projects()` API response to return objects with name + url. TDD approach.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(server): add search_reference_files tool and update API response`

## WHERE

- **Tests:** `tests/test_reference_projects.py` (add new test classes, update existing)
- **Implementation:** `src/mcp_workspace/server.py`

## WHAT

### `search_reference_files()` MCP tool

```python
@mcp.tool()
@log_function_call
async def search_reference_files(
    reference_name: str,
    glob: Optional[str] = None,
    pattern: Optional[str] = None,
    context_lines: int = 0,
    max_results: int = 50,
    max_result_lines: int = 200,
) -> Dict[str, Any]:
    """Search file contents by regex and/or find files by glob pattern in a reference project."""
    project = _reference_projects[reference_name]  # raise if not found
    await ensure_available(project)
    return search_files_util(
        project_dir=project.path,
        glob=glob, pattern=pattern,
        context_lines=context_lines,
        max_results=max_results,
        max_result_lines=max_result_lines,
    )
```

### Updated `get_reference_projects()` response

```python
# Before:
{"count": 3, "projects": ["alpha", "beta", "zebra"], "usage": "..."}

# After:
{"count": 3, "projects": [{"name": "alpha", "url": null}, {"name": "beta", "url": "https://..."}, ...], "usage": "..."}
```

## HOW

- `search_reference_files` follows same pattern as `read_reference_file` / `list_reference_directory`
- Reuses `search_files_util` (already imported in server.py) with reference project's path
- `get_reference_projects()` builds list of dicts from `ReferenceProject` instances
- Same glob + regex interface as `search_files()` — consistent API

## ALGORITHM (search_reference_files)

```
1. Validate reference_name exists in _reference_projects
2. Get project = _reference_projects[reference_name]
3. await ensure_available(project)
4. Delegate to search_files_util(project_dir=project.path, ...)
5. Return result dict
```

## ALGORITHM (get_reference_projects update)

```
1. Build sorted list of {"name": p.name, "url": p.url} from _reference_projects.values()
2. Return {"count": len, "projects": list, "usage": "..."}
```

## DATA

```python
# search_reference_files returns same format as search_files:
{"mode": "content_search", "matches": [...], "total_matches": 5, "truncated": False}
# or
{"mode": "file_search", "files": [...], "total_files": 10, "truncated": False}

# get_reference_projects returns:
{
    "count": 2,
    "projects": [
        {"name": "p_coder", "url": "https://github.com/org/mcp_coder"},
        {"name": "p_tools", "url": null}
    ],
    "usage": "Use these 2 projects with list_reference_directory(), read_reference_file(), and search_reference_files()"
}
```

## TESTS

### New `TestSearchReferenceFiles`
- `test_search_by_glob` — mock `search_files_util`, verify called with reference project path
- `test_search_by_pattern` — content search mode
- `test_search_combined` — glob + pattern together
- `test_search_not_found_project` — non-existent project → ValueError
- `test_search_calls_ensure_available` — verify `ensure_available` is awaited before search

### Update `TestReferenceProjectMCPTools`
- `test_get_reference_projects_empty` — update expected format (projects: [] still)
- `test_get_reference_projects_sorted` — update expected format to list of objects with name + url
- `test_get_reference_projects_logging` — update expected format
