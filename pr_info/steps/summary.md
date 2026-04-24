# Issue #124: Redesign edit_file to Match Claude Code Edit Interface

## Problem

The MCP `edit_file` tool uses `edits` array with `old_text`/`new_text`, but Claude Code's built-in `Edit` uses `old_string`/`new_string` as top-level parameters. LLMs frequently mix up the schemas, causing validation failures and fallback to full file rewrites. Additionally, parallel `edit_file` calls on the same file cause race conditions.

## Solution

Redesign `edit_file` to match Claude Code's built-in Edit interface exactly, add `replace_all` support, and add file-level locking for parallel safety.

## Architectural / Design Changes

### Interface change (breaking)

| Aspect | Before | After |
|--------|--------|-------|
| Parameters | `edits: List[Dict]`, `dry_run`, `options` | `old_string`, `new_string`, `replace_all` |
| Field names | `old_text` / `new_text` | `old_string` / `new_string` |
| Return (success) | `Dict` with `success`, `diff`, `match_results`, etc. | `str` (diff) |
| Return (already applied) | `Dict` with `message` field | `str` (plain message) |
| Return (failure) | `Dict` with `error` field | Raises `ValueError` / `FileNotFoundError` |
| Batch edits | Yes (array of edits) | No (single edit per call) |

### New behavior

- **Empty `old_string`** → insert `new_string` at beginning of file
- **Uniqueness check** → `ValueError` if `old_string` matches >1 location (unless `replace_all=True`)
- **`replace_all=True`** → replace all occurrences

### Server layer changes

- `edit_file` tool becomes `async def` (was sync)
- File-level locking via `asyncio.Lock` dict keyed by resolved absolute path
- Prevents race conditions from parallel MCP calls on the same file

### What gets removed

- `edits` array, `dry_run`, `options` parameter, `preserve_indentation` feature
- `_error_result` helper, `_preserve_basic_indentation` function, `create_unified_diff` public alias
- Complex return dict structure (`match_results`, `dry_run`, `file_path` fields)

### What stays

- `_create_diff`, `_truncate`, `_is_edit_already_applied` helpers
- Both already-applied checks (position-aware + contextual)
- Backslash hint for LLM guidance
- CRLF normalization via `normalize_line_endings`

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/edit_file.py` | Rewrite utility function — new signature, new return type, remove dead code |
| `src/mcp_workspace/server.py` | Rewrite `edit_file` tool — async, locking, new params |
| `tests/file_tools/test_edit_file.py` | Rewrite tests for new signature and return types |
| `tests/file_tools/test_edit_file_api.py` | Rewrite server-layer tests, add locking tests |
| `tests/file_tools/test_edit_file_issues.py` | Migrate regression tests to new interface |
| `tests/file_tools/test_edit_already_applied_fix.py` | Migrate already-applied tests to new interface |
| `tests/file_tools/test_edit_file_backslash.py` | Migrate backslash hint tests to new interface |

## Files Verified (no changes expected)

| File | Why |
|------|-----|
| `src/mcp_workspace/file_tools/__init__.py` | Re-exports `edit_file` by name — works with new signature |
| `vulture_whitelist.py` | `_.edit_file` entry stays |

## Implementation Steps

4 steps, each producing one commit:

1. **Rewrite utility function** (`edit_file.py`) — new signature, tests first
2. **Rewrite server tool** (`server.py`) — async + locking, tests first
3. **Migrate regression test files** — `test_edit_file_issues.py`, `test_edit_already_applied_fix.py`, `test_edit_file_backslash.py`
4. **Final verification** — all checks pass, cleanup
