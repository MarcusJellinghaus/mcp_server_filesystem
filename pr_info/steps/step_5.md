# Step 5: `server.py` — Async Handlers + `ensure_available()` Integration

## LLM Prompt

> Implement Step 5 of Issue #92. See `pr_info/steps/summary.md` for full context.
> Make `read_reference_file` and `list_reference_directory` async in `server.py`, add `ensure_available()` calls before file access, and remove `@log_function_call` from these now-async handlers.
> The `Dict[str, ReferenceProject]` type migration was already done in Step 4.
> Run all code quality checks (pylint, pytest, mypy) after changes. Commit: `feat(server): async handlers with lazy cloning via ensure_available`

## WHERE

- **Tests:** `tests/test_reference_projects.py` — update `TestReferenceProjectMCPTools` (add `ensure_available` mocking and new tests)
- **Implementation:** `src/mcp_workspace/server.py` — make two handlers async, add `ensure_available` calls, remove `@log_function_call`

## WHAT

> **Note:** The `ReferenceProject` type migration (`Dict[str, Path]` → `Dict[str, ReferenceProject]`), type signature updates for `set_reference_projects()` and `run_server()`, and `.path` access changes were all completed in Step 4. This step only adds async behavior and `ensure_available()` integration.

### `read_reference_file()` → async

```python
@mcp.tool()
async def read_reference_file(...) -> str:
    project = _reference_projects[reference_name]  # ReferenceProject (from Step 4)
    await ensure_available(project)
    ref_path = project.path
    # ... rest unchanged
```

> **IMPORTANT:** Remove `@log_function_call` from this handler. The decorator is sync-only — it creates a sync wrapper that doesn't `await` async functions. FastMCP checks `asyncio.iscoroutinefunction()` on the wrapper, which returns `False` for sync wrappers, causing the handler to break.

### `list_reference_directory()` → async

```python
@mcp.tool()
async def list_reference_directory(reference_name: str) -> List[str]:
    project = _reference_projects[reference_name]
    await ensure_available(project)
    ref_path = project.path
    # ... rest unchanged
```

> **IMPORTANT:** Same as above — remove `@log_function_call` from this handler.

## HOW

- Import `ensure_available` from `mcp_workspace.reference_projects`
- Two handlers become `async def` with `await ensure_available(project)` before file access
- **Remove** `@log_function_call` from both `read_reference_file` and `list_reference_directory` (sync-only decorator incompatible with async handlers)
- `get_reference_projects()` stays sync (no cloning, just returns metadata)

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

> **IMPORTANT:** ALL existing handler tests in `TestReferenceProjectMCPTools` must mock `ensure_available` as an async no-op: `AsyncMock(return_value=None)`. Without this, tests will attempt real clone operations or fail on missing paths. Use `@patch("mcp_workspace.server.ensure_available", new_callable=AsyncMock, return_value=None)` or equivalent.

### `TestReferenceProjectMCPTools` (update existing)
- `test_list_reference_directory_success` — add `ensure_available` mock (async no-op)
- `test_read_reference_file_success` — add `ensure_available` mock (async no-op)
- `test_read_reference_file_forwards_line_range_params` — add `ensure_available` mock (async no-op)
- All error tests that check for missing reference names remain structurally the same (they fail before `ensure_available` is called)

> **Note:** The `ReferenceProject` type migration for these tests was completed in Step 4. This step only adds `ensure_available` mocking.

### New tests
- `test_read_reference_file_calls_ensure_available` — verify `ensure_available` is awaited before file access
- `test_list_reference_directory_calls_ensure_available` — same
- `test_ensure_available_failure_propagates` — mock `ensure_available` raising → handler raises
- `test_log_function_call_removed` — verify `read_reference_file` and `list_reference_directory` are actual coroutine functions (`asyncio.iscoroutinefunction()` returns True)
