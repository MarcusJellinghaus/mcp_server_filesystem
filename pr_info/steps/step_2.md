# Step 2: Add `@log_function_call` to 3 async reference tools, remove manual debug logging

**Ref:** [summary.md](summary.md) — Step 2  
**Issue:** #142

## WHERE

- `src/mcp_workspace/server_reference_tools.py` — functions: `read_reference_file()`, `list_reference_directory()`, `search_reference_files()`
- `tests/test_reference_projects_mcp_tools.py` — rename misleading test

## WHAT

1. Add `@log_function_call` decorator to 3 async functions
2. Remove 2 manual `logger.debug(...)` calls (from `read_reference_file` and `list_reference_directory`) — now redundant with decorator
3. Rename `test_log_function_call_removed` → `test_async_handlers_are_coroutines` (the decorator is now present; old name is misleading)

**Note:** `search_reference_files` has no manual `logger.debug` call, so only the decorator is added there. `get_reference_project_path()` is a helper — do NOT add the decorator (would cause double-logging).

## HOW

### `server_reference_tools.py` — `read_reference_file`

**Before:**
```python
async def read_reference_file(
    ...
) -> str:
    ...
    ref_path = await get_reference_project_path(reference_name)

    # Log operation at DEBUG level
    logger.debug(
        "Reading file '%s' from reference project '%s' at path: %s",
        file_path,
        reference_name,
        ref_path,
    )

    return read_file_util(...)
```

**After:**
```python
@log_function_call
async def read_reference_file(
    ...
) -> str:
    ...
    ref_path = await get_reference_project_path(reference_name)

    return read_file_util(...)
```

### `server_reference_tools.py` — `list_reference_directory`

**Before:**
```python
async def list_reference_directory(reference_name: str) -> List[str]:
    ...
    ref_path = await get_reference_project_path(reference_name)

    # Log operation at DEBUG level
    logger.debug(
        "Listing files in reference project '%s' at path: %s",
        reference_name,
        ref_path,
    )

    return list_files_util(...)
```

**After:**
```python
@log_function_call
async def list_reference_directory(reference_name: str) -> List[str]:
    ...
    ref_path = await get_reference_project_path(reference_name)

    return list_files_util(...)
```

### `server_reference_tools.py` — `search_reference_files`

**Before:**
```python
async def search_reference_files(
    ...
) -> Dict[str, Any]:
    ...
```

**After:**
```python
@log_function_call
async def search_reference_files(
    ...
) -> Dict[str, Any]:
    ...
```

### `test_reference_projects_mcp_tools.py` — rename test

**Before:**
```python
def test_log_function_call_removed(self) -> None:
    """Verify async reference handlers are coroutine functions."""
```

**After:**
```python
def test_async_handlers_are_coroutines(self) -> None:
    """Verify async reference handlers are coroutine functions."""
```

## ALGORITHM

No logic change — decorator additions + dead code removal + test rename.

## DATA

No change to inputs/outputs. The decorator handles entry/exit logging transparently.

## Tests

- Existing async tests in `TestReferenceProjectMCPTools` and `TestSearchReferenceFiles` already cover all 3 functions
- The `test_async_handlers_are_coroutines` test (renamed) verifies `asyncio.iscoroutinefunction` — confirms the decorator preserves async nature
- Logging tests (`test_*_logging`) mock `logger` but only assert on return values, not on specific `.debug` calls — removing `logger.debug` won't break them

## Commit

```
feat(logging): add @log_function_call to async reference tools (#142)
```
