# Issue #152: Security — normalize_path bypasses traversal check when resolve() throws OSError

## Summary

Fix a path traversal vulnerability in `normalize_path()` where an `OSError` from `Path.resolve()` silently skips the security check, returning a path that may still contain `..` components.

## Architectural / Design Changes

**No architectural changes.** This is a targeted security hardening of one function in one module. The fix:

- Narrows the exception catch from `(FileNotFoundError, OSError)` to `OSError` only — `FileNotFoundError` is dead code on Python 3.6+ with `resolve(strict=False)`
- Adds a fallback `..` traversal check on `absolute_path.parts` when `resolve()` fails
- Adds a `logger.warning()` call when the fallback path triggers (unusual condition, aids debugging)

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/file_tools/path_utils.py` | Fix `except` block in `normalize_path()` |
| `tests/file_tools/test_path_utils.py` | Add 2 new tests for OSError fallback behavior |

No new files or modules created.

## Implementation Plan

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Add tests for OSError fallback, then fix `normalize_path()` | `fix: harden normalize_path against OSError bypass (#152)` |
