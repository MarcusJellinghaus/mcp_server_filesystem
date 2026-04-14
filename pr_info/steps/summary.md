# Issue #96: Normalize CRLF Line Endings from LLM Input

## Problem

LLMs produce content with arbitrary line endings (`\r\n`, `\n`, `\r`). The MCP server writes this content without normalization, causing:

- **Windows:** Python text-mode converts `\n` → `\r\n`. If content already has `\r\n`, result is `\r\r\n` (double endings).
- **Linux/Mac:** `\r\n` written as-is, contaminating repos that expect LF.
- **`edit_file` (all platforms):** `old_text`/`new_text` with `\r\n` silently fails exact match. CRLF files on Linux/Mac aren't normalized by Python text mode, so even LF `old_text` fails against raw CRLF content.

## Solution: Normalize at the Boundary

Add a single `normalize_line_endings` function in `path_utils.py` and call it at the three entry points where LLM content enters the system. No platform-specific logic — Python text-mode and git handle the rest downstream.

## Architectural / Design Changes

- **Shared utility in `path_utils.py`**: The existing `normalize_line_endings` in `edit_file.py` (incomplete legacy copy) is removed and a complete version is added to `path_utils.py` as the single source of truth. Both `edit_file.py` and `file_operations.py` already import from `path_utils`.
- **Boundary normalization pattern**: Content is normalized once at entry (`_validate_save_parameters` for writes, `edit_file` for edits), not at the write layer. This keeps `_write_file_atomically` and `read_file` unchanged.
- **`append_file` refactored to use `_validate_save_parameters`**: Eliminates duplicated validation code (~15 lines) and ensures normalization applies before concatenation.
- **No new modules, no new dependencies**: All changes stay within the existing `mcp_workspace.file_tools` layer. No new import edges.

## Files Modified

| File | Change |
|---|---|
| `src/mcp_workspace/file_tools/path_utils.py` | Add `normalize_line_endings` function |
| `src/mcp_workspace/file_tools/file_operations.py` | Normalize in `_validate_save_parameters`; refactor `append_file` to use it |
| `src/mcp_workspace/file_tools/edit_file.py` | Normalize `original_content`, `old_text`, `new_text`; remove local legacy copy; update import |
| `tests/file_tools/test_file_operations.py` | Add CRLF normalization tests for `save_file` and `append_file` |
| `tests/file_tools/test_path_utils.py` | Add `normalize_line_endings` unit tests (moved from `test_edit_file.py`, plus new cases) |
| `tests/file_tools/test_edit_file.py` | Add CRLF normalization tests for `edit_file`; remove `test_normalize_line_endings` (moved to `test_path_utils.py`) |

## Implementation Steps

| Step | Description | Commit |
|---|---|---|
| 1 | Add `normalize_line_endings` to `path_utils.py` + tests, update `edit_file.py` import | `feat: add normalize_line_endings to path_utils` |
| 2 | Normalize in `_validate_save_parameters` + refactor `append_file` + tests | `fix: normalize CRLF in save_file/append_file` |
| 3 | Normalize in `edit_file` + tests | `fix: normalize CRLF in edit_file` |
