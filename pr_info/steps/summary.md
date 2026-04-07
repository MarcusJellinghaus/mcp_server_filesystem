# Issue #28: read_file — support reading specific line ranges

## Summary

Extend `read_file` (and `read_reference_file`) with optional `start_line` / `end_line` / `with_line_numbers` parameters so callers can read a slice of a file instead of the whole thing.

## Architectural / Design Changes

### Before
- `read_file(file_path, project_dir)` reads the entire file via `f.read()` and returns raw content as a string.
- `read_reference_file` in `server.py` calls `read_file_util(file_path, project_dir=ref_path)`.
- MCP tool wrappers in `server.py` expose `file_path` only.

### After
- `read_file(file_path, project_dir, start_line?, end_line?, with_line_numbers?)` streams line-by-line via `enumerate(file)`, optionally slicing and formatting.
- The return type stays `str` — no metadata, no new classes.
- Validation, slicing, clamping, and line-number formatting all live in the single `read_file` util function. No new helpers, no new modules.
- `server.py` wrappers (`read_file`, `read_reference_file`) forward the three new optional params to `read_file_util`.
- `append_file` calls `read_file(file_path, project_dir)` without new params — backward compatible, unaffected.

### Design Decisions
- **No separate helper functions** — the logic is ~30 lines total, used in one place.
- **Streaming** replaces `f.read()` for both full and sliced reads, keeping memory usage proportional to the returned slice.
- **Smart default for `with_line_numbers`**: `False` for full reads (backward compat), `True` for sliced reads (useful context). Caller can override either way.
- **Strict validation**: both `start_line` and `end_line` required together, must be positive ints, `end >= start`. No one-sided ranges.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/file_operations.py` | Add 3 params + validation + slicing + formatting to `read_file` |
| `src/mcp_workspace/server.py` | Forward new params in `read_file` and `read_reference_file` tools |
| `tests/file_tools/test_file_operations.py` | Add all unit tests for slicing, formatting, validation, edge cases |
| `tests/test_reference_projects.py` | Update 1 existing test to verify new params are forwarded |

## Files NOT Modified

| File | Reason |
|------|--------|
| `src/mcp_workspace/file_tools/__init__.py` | `read_file` already exported; new params are optional |
| `src/mcp_workspace/file_tools/edit_file.py` | Out of scope per issue |
| Any other file tool | Out of scope per issue |

## Implementation Steps

1. **Step 1** — Parameter validation in `read_file` + tests
2. **Step 2** — Line-range slicing with streaming + tests
3. **Step 3** — `with_line_numbers` formatting + tests
4. **Step 4** — Server wrapper updates + forwarding test
