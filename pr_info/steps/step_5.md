# Step 5: `server.py` — New Data Model, Async Handlers, `ensure_available()` Integration

## LLM Prompt

> Implement Step 5 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Update `server.py` to use `Dict[str, ReferenceProject]`, make reference handlers async, and add `ensure_available()` calls. TDD — update existing tests first, then modify implementation.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(server): integrate ReferenceProject model with lazy cloning`

## WHERE

- **Tests:** `tests/test_reference_projects.py` — update `TestReferenceProjectMCPTools` and `TestReferenceProjectServerStorage`
- **Implementation:** `src/mcp_workspace/server.py`

## WHAT

### Module-level variable change

```python
# Before:
_reference_projects: Dict[str, Path] = {}

# After:
from mcp_workspace.reference_projects import ReferenceProject
_reference_projects: Dict[str, ReferenceProject] = {}
```

### Updated `set_reference_projects()`

```python
def set_reference_projects(reference_projects: Dict[str, ReferenceProject]) -> None:
```

### Updated `run_server()`

```python
def run_server(
    project_dir: Path, reference_projects: Optional[Dict[str, ReferenceProject]] = None
) -> None:
```

### `read_reference_file()` → async

```python
@mcp.tool()
@log_function_call
async def read_reference_file(...) -> str:
    project = _reference_projects[reference_name]  # ReferenceProject
    await ensure_available(project)
    ref_path = project.path
    # ... rest unchanged
```

### `list_reference_directory()` → async

```python
@mcp.tool()
@log_function_call
async def list_reference_directory(reference_name: str) -> List[str]:
    project = _reference_projects[reference_name]
    await ensure_available(project)
    ref_path = project.path
    # ... rest unchanged
```

## HOW

- Import `ReferenceProject` and `ensure_available` from `mcp_workspace.reference_projects`
- Path access changes: `_reference_projects[name]` → `_reference_projects[name].path`
- Two handlers become `async def` with `await ensure_available(project)` before file access
- `get_reference_projects()` stays sync (no cloning, just returns metadata)
- `set_reference_projects()` accepts `Dict[str, ReferenceProject]`

## ALGORITHM (handler pattern)

```
1. Check reference_name in _reference_projects → raise if not found
2. Get project = _reference_projects[reference_name]
3. await ensure_available(project)  # may clone, may raise
4. Use project.path for file operations
5. Delegate to existing utility function
```

## DATA

```python
# _reference_projects storage:
{
    "p_coder": ReferenceProject(name="p_coder", path=Path("/home/user/mcp_coder"), url="https://..."),
    "p_tools": ReferenceProject(name="p_tools", path=Path("/home/user/tools"), url=None),
}
```

## TESTS

### `TestReferenceProjectMCPTools` (update existing)
- All tests that set `server_module._reference_projects` → use `ReferenceProject` instances
- `test_list_reference_directory_success` — update to ReferenceProject, mock `ensure_available`
- `test_read_reference_file_success` — update to ReferenceProject, mock `ensure_available`
- `test_read_reference_file_forwards_line_range_params` — update to ReferenceProject
- All error tests remain structurally the same, just with ReferenceProject data

### `TestReferenceProjectServerStorage` (update existing)
- `test_set_reference_projects` — pass `Dict[str, ReferenceProject]`
- `test_run_server_with_reference_projects` — pass `Dict[str, ReferenceProject]`
- `test_reference_projects_logging` — pass `Dict[str, ReferenceProject]`

### New tests
- `test_read_reference_file_calls_ensure_available` — verify `ensure_available` is awaited before file access
- `test_list_reference_directory_calls_ensure_available` — same
- `test_ensure_available_failure_propagates` — mock `ensure_available` raising → handler raises
