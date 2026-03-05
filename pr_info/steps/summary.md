# Summary: Issue #55 — Backslash Hint in edit_file Failure Message

## Problem

`mcp__filesystem__edit_file` silently fails with "Text not found" when editing files
that contain double-backslash sequences (e.g. JSON-escaped Windows paths like `C:\\Users\\Marcus`).

**Root cause — LLM/raw-bytes semantic gap:**
- `read_file` returns raw file bytes: a JSON-encoded Windows path is stored on disk as `C:\\Users\\Marcus`
  (two backslashes per separator).
- An LLM reading this output interprets `\\` as a JSON escape and decodes it to a single `\`.
- When the LLM constructs `old_text` for `edit_file`, it uses the decoded (single backslash) value.
- `edit_file` does exact byte matching — it never finds the single-backslash string in the
  raw file content, which contains double backslashes.
- Result: silent "Text not found" failure with no actionable guidance.

## Proposed Fix

**No auto-correction.** Instead, improve the error detail with a targeted diagnostic hint:

When `old_text` is not found, check whether doubling every backslash in `old_text` would match
the file content. If yes, append a concise hint to `match_results[i]["details"]` only —
the top-level `message` and `error` fields remain the generic count summary.

## Architectural / Design Changes

**No new modules, no new imports, no new abstractions.**

The change is a single targeted in-place extension of the existing failure branch inside the
edit loop in `edit_file()`. It:

1. Computes `doubled = old_text.replace("\\", "\\\\")` (doubles every backslash).
2. Checks `doubled != old_text` (guard: only act when there are actual backslashes) **and**
   `doubled in current_content` (would-have-matched check).
3. If both conditions hold, builds a `details` string that includes the standard
   "Text not found" prefix plus the hint sentence.
4. Otherwise produces the unchanged generic `details` string.

This is backwards-compatible: existing behaviour is untouched when the hint does not apply.

## Files Created / Modified

| Action   | Path                                                   | Notes                                   |
|----------|--------------------------------------------------------|-----------------------------------------|
| Modified | `src/mcp_server_filesystem/file_tools/edit_file.py`   | ~7 lines added to the failure branch    |
| Created  | `tests/file_tools/test_edit_file_backslash.py`         | New test file — 1 class, 1 test method  |

No other files require changes. No new modules, packages, imports, or configuration entries.

## TDD Order

1. **Step 1** — Write the failing test first (red phase).
2. **Step 2** — Implement the hint logic in `edit_file.py` (green phase).
