# Step 1: Add `@log_function_call` to `git()` in server.py

**Ref:** [summary.md](summary.md) — Step 1  
**Issue:** #142

## WHERE

- `src/mcp_workspace/server.py` — the `git()` async function (~line 330)

## WHAT

Add the `@log_function_call` decorator to the `git()` async function, matching the pattern used by all other tools in this file.

## HOW

The decorator is already imported: `from mcp_coder_utils.log_utils import log_function_call`

**Before:**
```python
@mcp.tool()
async def git(
    command: str,
    ...
) -> str:
```

**After:**
```python
@mcp.tool()
@log_function_call
async def git(
    command: str,
    ...
) -> str:
```

## ALGORITHM

No logic change — single decorator addition.

## DATA

No change to inputs/outputs. The decorator logs function entry (with args) and exit (with return value) at DEBUG level.

## Tests

No new tests needed. Existing `TestGitTool` tests in `tests/test_server.py` already verify `git()` delegates correctly. The decorator is transparent to callers since `asyncio.iscoroutinefunction` is preserved by the async-aware decorator.

## Commit

```
feat(logging): add @log_function_call to git() async wrapper (#142)
```
