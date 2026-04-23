# feat(git): Support git operations on reference projects (#140)

## Goal

Add an optional `reference_name` parameter to the `git()` MCP tool so it can run read-only git commands against configured reference projects, not just the workspace repo.

## Architectural / Design Changes

### Before
- `git()` in `server.py` is a **sync** function decorated with `@log_function_call`
- It only operates on `_project_dir` (the workspace repo)
- Each reference tool (`read_reference_file`, `list_reference_directory`, `search_reference_files`) inlines the same 4-line lookup+ensure pattern to resolve a reference project

### After
- `git()` becomes **async** (required to call `ensure_available()` which uses `asyncio.Lock`)
- `@log_function_call` is dropped from `git()` (decorator doesn't support async — mcp-coder-utils#23, tracked in #142)
- `git_impl` is wrapped in `asyncio.to_thread()` to avoid blocking the event loop
- New `get_reference_project_path()` async helper in `server_reference_tools.py` encapsulates the lookup+ensure+return-path sequence
- All 4 reference tools (3 existing + `git`) use the shared helper — DRY

### Key constraints
- `git_impl` in `read_operations.py` already accepts any `project_dir` — no changes needed there
- `ensure_available()` is async (uses `asyncio.Lock` + `asyncio.to_thread` for cloning)
- `_project_dir` guard is conditional — only checked when `reference_name` is absent

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/server_reference_tools.py` | Add `get_reference_project_path()` helper; refactor 3 existing tools to use it |
| `src/mcp_workspace/server.py` | Modify `git()` — async, `reference_name` param, `asyncio.to_thread`, drop `@log_function_call` |
| `tests/test_reference_projects_mcp_tools.py` | Add tests for helper; add 4 tests for git with reference projects |

No new files created. No files deleted.

## Implementation Steps

1. **Add `get_reference_project_path()` helper + tests** — new helper in `server_reference_tools.py` with unit tests
2. **Refactor existing reference tools** — replace inlined lookup+ensure pattern with helper call; existing tests validate
3. **Add `reference_name` to `git()` + tests** — make `git()` async, add parameter, wrap `git_impl`, add 4 test cases
