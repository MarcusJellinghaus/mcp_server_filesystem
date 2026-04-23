# Search: Auto-fallback to Literal When Regex is Invalid

**Issue:** #139

## Problem

LLMs pass grep-style patterns (e.g. `functionname(`) to the search tool. In grep (POSIX BRE), `(` is literal, but Python `re` treats it as a metacharacter and raises `re.error`. This causes unnecessary failures and wasted round-trips.

## Solution

Auto-fallback to literal search when `re.compile(pattern)` raises `re.error`:
- Retry with `re.escape(pattern)` (literal match)
- Add a `"note"` field to the result dict explaining the fallback
- Update docstrings to clarify Python regex behavior

## Architectural / Design Changes

- **No new modules, classes, or parameters** — this is a behavioral change within the existing `search_files()` function
- **Error-to-recovery transformation**: The `re.error` exception path in `search_files()` changes from raising `ValueError` to a graceful fallback. The function now always returns a result dict (never raises on bad regex)
- **Result dict schema addition**: A new optional top-level `"note"` key is added to the content search result dict, present only when fallback is triggered. All existing keys (`mode`, `details`, `total_matches`, `truncated`, `matched_files`) are unchanged
- **Docstring contract update**: The `pattern` parameter description in three tool docstrings is updated to document the fallback behavior

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/search.py` | Core fallback logic + docstring update |
| `src/mcp_workspace/server.py` | Tool docstring update for `pattern` param |
| `src/mcp_workspace/server_reference_tools.py` | Tool docstring update for `pattern` param |
| `tests/file_tools/test_search.py` | Replace error test with fallback tests |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Tests: replace error test with fallback tests | Tests + impl in `search.py` |
| 2 | Docstring updates in server wrappers | Docstrings in `server.py` + `server_reference_tools.py` |
