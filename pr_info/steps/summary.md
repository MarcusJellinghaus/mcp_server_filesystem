# Summary: Add `@log_function_call` to async MCP tool wrappers

**Issue:** #142  
**Branch:** feat/142-log-function-call-async-wrappers

## Goal

Apply `@log_function_call` to the 4 async MCP tool wrappers that currently lack it, and remove redundant manual `logger.debug` calls from 2 reference tool functions.

## Architectural / Design Changes

**No architectural changes.** This is a consistency fix — the decorator was already used on all sync MCP tool wrappers. The upstream `mcp-coder-utils` package now supports async functions (mcp-coder-utils#23), so we can apply it uniformly.

**Design pattern preserved:** The decorator ordering convention remains:
- `server.py`: `@mcp.tool()` → `@log_function_call` → `def/async def`
- `server_reference_tools.py`: `@log_function_call` on function definition; registration via `mcp.tool()(func)` in `register()`

**Logging consolidation:** The `@log_function_call` decorator handles entry/exit logging, making manual `logger.debug` calls in the 3 reference tool functions redundant. The removed debug calls only logged an intermediate value (resolved path) of little diagnostic value.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/server.py` | Add `@log_function_call` to `git()` |
| `src/mcp_workspace/server_reference_tools.py` | Add `@log_function_call` to 3 async functions; remove 2 manual `logger.debug` calls |
| `tests/test_reference_projects_mcp_tools.py` | Rename `test_log_function_call_removed` → `test_async_handlers_are_coroutines` (decorator now present, old name misleading) |

## Steps

1. **Step 1** — `server.py`: Add `@log_function_call` to `git()` (no test changes needed — existing tests cover delegation)
2. **Step 2** — `server_reference_tools.py`: Add `@log_function_call` to 3 async functions, remove 2 manual `logger.debug` calls, rename misleading test
