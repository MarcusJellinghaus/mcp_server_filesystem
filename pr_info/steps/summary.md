# Summary: Support Numeric Parameters in Git Tool

**Issue:** #133 — The MCP `git` tool rejects bare numeric flags like `-10` (shorthand for `--max-count=10`).

## Problem

`validate_args()` in `arg_validation.py` rejects flags like `-10` because they don't match any allowlisted flag prefix. While `-n10`, `-n 10`, and `--max-count=10` all work, `-10` is valid git syntax that Claude naturally reaches for.

## Solution

Two minimal changes to `arg_validation.py`:

1. **Add a sentinel marker `"-<int>"` to three allowlist frozensets** (`LOG_ALLOWED_FLAGS`, `SHOW_ALLOWED_FLAGS`, `DIFF_ALLOWED_FLAGS`) — the commands where git supports `-<number>` syntax.
2. **Add a numeric-flag detection branch in `validate_args()`** — if an arg matches `-<digits>` and the command's allowlist contains `"-<int>"`, allow it.

No argument rewriting. No changes outside `arg_validation.py` and its test file.

## Architectural / Design Changes

- **No new modules, classes, or abstractions.** This is a leaf-level change to existing validation logic.
- **Design pattern preserved:** The existing per-command allowlist pattern is extended with a single sentinel value. The sentinel approach keeps the "which commands support this" knowledge inside the allowlist data (no separate command set to maintain).
- **Security model unchanged:** Only commands that explicitly opt in via `"-<int>"` accept numeric flags. All other commands continue to reject them.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/arg_validation.py` | Add `"-<int>"` to 3 frozensets; add numeric detection in `validate_args()` |
| `tests/git_operations/test_arg_validation.py` | Add test class for numeric flag acceptance and rejection |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| [Step 1](step_1.md) | Add tests for numeric flag support | Tests + sentinel + detection logic |
