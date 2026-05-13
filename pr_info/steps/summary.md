# Issue #198 — Implementation Summary

## Problem

`mcp__mcp-workspace__git` with `compact=True` (default) silently drops:

- **Non-patch diff formats** (`--stat`, `--shortstat`, `--numstat`, `--name-only`, `--name-status`, `--no-patch`) → returns `"No changes found"` even when there are real changes.
- **`--stat -p` combinations** → the stat block is dropped, only the compacted patch survives.
- **`git show` prefix lines** (commit sha / author / date / message, plus `--oneline`, `--format`, `--pretty` output) → dropped; only the patch survives.

## Root cause

`parse_diff()` (in `compact_diffs.py`) only collects lines from the first `diff --git` marker onward. For non-patch summary formats there is no marker → parser returns `[]` → `render_compact_diff()` returns `""` → caller hits `"No changes found"`. For `git show`, the commit header (and any pre-patch summary) is silently discarded.

## Fix at a glance

1. **Bypass** compact rendering when a non-patch flag is used without `-p` / `--patch` → reuse the existing non-compact code path (one git invocation, no `-M -C90%` rename-detection injection).
2. **Split-and-preserve** the raw plain output at the first `diff --git` line in the compact path:
   - Everything **before** = preserved as-is (stat block, commit header, oneline/format/pretty output).
   - Everything **from** that marker on = compacted by `render_compact_diff()`.
3. **Compact stats header** is only added when compaction actually ran on a patch portion and reflects only that portion's line counts.
4. **Allowlist symmetry**: add `--numstat` to `SHOW_ALLOWED_FLAGS` (already in `DIFF_ALLOWED_FLAGS`).

## Architectural / design changes

- **No new modules, no new public functions, no new abstractions.** Fix lives entirely inside `git_diff()` and `git_show()` in `read_operations.py`.
- **`compact_diffs.py` is untouched.** `parse_diff()` keeps its current hunk-only contract; the prefix is preserved at the caller level.
- **One new module-level constant**: `_NON_PATCH_FLAGS` frozenset in `read_operations.py`.
- **Dead-code removal**: the `if not output: output = plain` rescue in `git_show()` is removed because the split-and-prefix logic subsumes every case it handled.
- Layered architecture and import contracts are unaffected.

## Files modified

| File | Change |
|---|---|
| `src/mcp_workspace/git_operations/read_operations.py` | Add `_NON_PATCH_FLAGS`; rewrite the `if compact:` branch of `git_diff()` and `git_show()`; remove `git_show()`'s dead rescue. |
| `src/mcp_workspace/git_operations/arg_validation.py` | Add `"--numstat"` to `SHOW_ALLOWED_FLAGS`. |
| `tests/git_operations/test_read_operations.py` | Add integration tests for non-patch flags, `--stat -p` combinations, and `git show` prefix preservation. |
| `tests/git_operations/test_arg_validation.py` | Add a single test confirming `--numstat` is allowed for `show`. |

No files are created or deleted.

## Implementation steps

| Step | Scope | One commit |
|---|---|---|
| [Step 1](step_1.md) | Allowlist: add `--numstat` to `SHOW_ALLOWED_FLAGS` | ✓ |
| [Step 2](step_2.md) | Fix `git_diff()` compact rendering (non-patch flags, `--stat -p`) | ✓ |
| [Step 3](step_3.md) | Fix `git_show()` compact rendering (prefix preservation) | ✓ |

Step 2 introduces the `_NON_PATCH_FLAGS` constant; Step 3 reuses it.

## Constraints preserved

- All flags affected (except `--numstat` for `show`) are already in their respective allowlists.
- Bypass path reuses the existing non-compact `else` branch — no `-M -C90%` injection, single git call.
- `parse_diff()` and the rest of `compact_diffs.py` remain unmodified.
- `@pytest.mark.git_integration` tests use the existing `git_repo_with_commit` fixture, matching the established pattern in `test_read_operations.py`.
