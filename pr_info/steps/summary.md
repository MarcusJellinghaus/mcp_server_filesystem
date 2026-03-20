# Issue #36: Filter Reference Projects That Overlap With Main Project Directory

## Summary

Add overlap detection to `validate_reference_projects()` so that reference projects pointing to the same, parent, or child directory of `--project-dir` are filtered out with specific warning messages.

## Architectural / Design Changes

### What changes

- **`validate_reference_projects()` gains a `project_dir: Path` parameter** — this is an internal function with a single call site in `main()`, so the change is contained.
- **Path resolution switches from `.absolute()` to `.resolve()`** — both in `main()` for `project_dir` and in `validate_reference_projects()` for reference paths. This produces canonical paths that handle symlinks, `..` segments, and Windows case normalization correctly.
- **Overlap filtering is added as a simple if/elif block** inside the existing validation loop, placed after the existence/directory checks (so we only check overlap for valid paths).

### What does NOT change

- `server.py` — filtering happens before the server starts, no changes needed.
- CLI interface — no new arguments, no breaking changes.
- Behavior for valid, non-overlapping reference projects — unchanged.

### Design Decisions

- **KISS**: Overlap detection is a simple if/elif chain using `==` and `Path.is_relative_to()` (Python 3.11+). No helper functions, no new modules.
- **Consistent with existing pattern**: Other validation failures (missing `=`, empty name, non-existent path) already use `warning + continue`. Overlap follows the same pattern.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/main.py` | Add `project_dir` param to `validate_reference_projects()`, `.absolute()` → `.resolve()`, add overlap checks, update call site |
| `tests/test_reference_projects.py` | Add `project_dir` arg to existing calls, add parameterized overlap tests, update `.absolute()` → `.resolve()` in assertions |

## Implementation Steps

| Step | Description | File |
|------|-------------|------|
| 1 | Tests first: update existing tests + add overlap tests | `tests/test_reference_projects.py` |
| 2 | Implement overlap filtering + `.resolve()` changes | `src/mcp_workspace/main.py` |

## Review Decisions

See [Decisions.md](./Decisions.md) for the full log. Key decisions:

1. Update `.absolute()` → `.resolve()` across **entire** test file, not just integration tests
2. Overlap tests use **real temp directories** (`tmp_path`) instead of mocking `Path.resolve`
3. No symlink edge case test (no special code path)
4. Resolve `project_dir` once at top of `validate_reference_projects()` for safety
5. Strengthen `test_path_normalization` to assert canonical path equality
