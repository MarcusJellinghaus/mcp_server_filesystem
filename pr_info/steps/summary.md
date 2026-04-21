# search_files: fix volume cap and add compact fallback (#130)

## Problem

`_search_content()` in `src/mcp_workspace/file_tools/search.py` uses newline-counting (`max_result_lines`) to cap output volume. This fails for files with very long lines (e.g. single-line 231K JSON blobs) because a 231K single-line file counts as "1 line".

## Solution

Three fixes in `_search_content()`, plus a key rename:

1. **Per-line truncation** — cap every line in the context block to 500 chars, appending ` ... [truncated, line has {n} chars]` when hit.
2. **Character budget** — replace newline-counting with `char_budget = max_result_lines * 120`. Track `chars_used`, stop adding detailed matches when budget is exceeded.
3. **Compact fallback** — when truncated, include a `"matched_files"` key with the complete map of all matching files and line numbers. `"matched_files"` key is only present when `truncated=True`.
4. **Key rename** — `"matches"` → `"details"` everywhere (clean break, no backwards compat).

## Architectural / Design Changes

- **No new files, modules, classes, or parameters.** The change is entirely within `_search_content()` return structure.
- **Response key rename:** `"matches"` → `"details"` in the content_search result dict. This is a breaking change to the internal API. Both `search_files` and `search_reference_files` use the same `_search_content` utility, so both are fixed automatically.
- **New optional key:** `"matched_files"` (list of `{"file": str, "lines": list[int]}`) appears only when `truncated=True`.
- **Volume measurement semantic change:** `max_result_lines` now measures character budget (`* 120`) instead of counting newlines. The parameter name and default value (200) are unchanged — only the internal interpretation changes.
- **No server layer changes needed.** `server.py` and `server_reference_tools.py` pass through the dict from `search_files_util` transparently.

## Files Modified

| File | What Changes |
|------|--------------|
| `src/mcp_workspace/file_tools/search.py` | `_search_content()`: per-line truncation, char budget, compact fallback, key rename |
| `tests/file_tools/test_search.py` | Rename `"matches"` → `"details"` in all assertions; add tests for long-line truncation, char budget, and compact fallback |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Rename `"matches"` → `"details"` in `_search_content()` and all tests | `refactor: rename "matches" key to "details" in search results` |
| 2 | Per-line truncation (500 char cap) with tests | `feat: add per-line truncation to search content results` |
| 3 | Character budget replacing line-counting, with compact fallback and tests | `feat: add char budget and compact fallback for large search results` |
