# Step 1: Rename `"matches"` → `"details"` in search results

## Context
See `pr_info/steps/summary.md` for full context. This is a clean-break key rename with no backwards compatibility shim.

## WHERE
- `src/mcp_workspace/file_tools/search.py` — `_search_content()` function (line 62)
- `tests/file_tools/test_search.py` — all `result["matches"]` references

## WHAT
Rename the `"matches"` key to `"details"` in the return dict of `_search_content()`, and update all test assertions.

## HOW
1. In `_search_content()` (search.py line 62-67): change `"matches": matches` → `"details": matches` in the return dict.
2. In `tests/file_tools/test_search.py`: replace every `result["matches"]` with `result["details"]` (lines 92, 103, 123, 136, 137, 158, 170, 171).

## DATA
Return dict changes from:
```python
{"mode": "content_search", "matches": [...], "total_matches": N, "truncated": bool}
```
to:
```python
{"mode": "content_search", "details": [...], "total_matches": N, "truncated": bool}
```

## Commit
`refactor: rename "matches" key to "details" in search results`

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: rename the "matches" key to "details" in the _search_content() return dict
in src/mcp_workspace/file_tools/search.py, and update all test assertions in
tests/file_tools/test_search.py that reference result["matches"] to use result["details"].

This is a simple find-and-replace. No logic changes. Run all quality checks after.
```
