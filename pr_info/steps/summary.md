# Summary: Port merge-base direction fix and migrate 4 tests

**Issue:** #135 — fix+test: port #803 merge-base direction fix and migrate 4 parent_branch_detection tests

## Problem

`detect_parent_branch_via_merge_base` in mcp_workspace has a buggy algorithm (copied before the fix landed in mcp_coder PR #873). Three bugs:

1. **Wrong distance direction**: measures `merge_base..candidate_HEAD` instead of `merge_base..current_HEAD`. This counts how far the *candidate* moved, not how far the *current branch* diverged — giving wrong results when a dormant branch diverged long ago.
2. **Early-exit on distance=0**: returns the first candidate with distance 0, preventing collection of all candidates and tiebreaker logic.
3. **No default-branch tiebreaker**: when two candidates have equal distance, there's no preference for the default branch (e.g., `main`).

## Architectural / Design Changes

- **No new files or modules** — this is a fix to an existing function.
- **New import**: `get_default_branch_name` from `.branch_queries` into `parent_branch_detection.py`. This is an intra-package import within `git_operations/` — fully allowed by the layered architecture.
- **Algorithm change**: the sort key becomes `(distance, 0 if default_branch else 1)` — a tiebreaker, not a new abstraction.
- **No API changes**: `detect_parent_branch_via_merge_base` keeps its existing signature and return type.
- **Mock strategy**: `get_default_branch_name` is patched per-test only where tiebreaker behavior matters — not added to the shared `mock_repo` fixture.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/git_operations/parent_branch_detection.py` | Algorithm fix (distance direction, remove early-exit, add tiebreaker) |
| `tests/git_operations/test_parent_branch_detection.py` | Update 2 existing tests + add 4 new tests |

No files created. No files deleted.

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Fix algorithm + update 2 existing tests whose mocks break with new direction | `fix: reverse merge-base distance direction and remove early-exit` |
| 2 | Add 4 new tests validating corrected behavior | `test: add 4 regression tests for merge-base parent detection` |
