# Summary: Add "auto-delete head branches" check to verify_github()

**Issue:** #162 — verify: check "auto-delete head branches" repo setting

## Goal

Add check 10 (`auto_delete_branches`) to `verify_github()` that verifies the GitHub repo-level "Automatically delete head branches" setting. This prevents stale branch accumulation after PR merges.

## Architecture / Design Changes

**No architectural changes.** This is a single-check extension to the existing verification pipeline:

- The new check follows the same `CheckResult` pattern used by checks 1–9
- It reads `repo.delete_branch_on_merge` (PyGithub `Repository` boolean property)
- It is a **repo-level** setting, not a branch protection attribute — so it lives as a standalone block after the checks 5–9 branch protection section, guarded only by repo accessibility

**Design decision:** The fallback (repo not accessible) is a separate `if/else` block, not merged into the checks 5–9 fallback loop. This keeps the semantics accurate — it's not a branch protection attribute.

## Files Modified

| File | Action | Purpose |
|------|--------|---------|
| `src/mcp_workspace/github_operations/verification.py` | Modify | Add check 10 block |
| `tests/github_operations/test_verification.py` | Modify | Add tests + update `_patch_all_ok` helper |

No new files or modules created (beyond the plan files).

## Implementation Steps

| Step | Description |
|------|-------------|
| 1 | Add tests for check 10 + update `_patch_all_ok` helper |
| 2 | Implement check 10 in `verification.py` |
