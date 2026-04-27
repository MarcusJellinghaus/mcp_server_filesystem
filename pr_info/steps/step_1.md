# Step 1: Add tests and implement auto_delete_branches check

**Context:** See `pr_info/steps/summary.md` for overall plan.

## LLM Prompt

> Implement step 1 of the plan in `pr_info/steps/summary.md`.
> First, add tests for the new `auto_delete_branches` check (check 10) in `tests/github_operations/test_verification.py` and update the `_patch_all_ok` helper.
> Then, implement check 10 in `src/mcp_workspace/github_operations/verification.py` so all tests pass.
> Run all three code quality checks after changes.

## WHERE

- `tests/github_operations/test_verification.py`
- `src/mcp_workspace/github_operations/verification.py`

## WHAT — Tests

1. **Update `_patch_all_ok` helper** — add a `delete_branch_on_merge: bool = True` parameter. Set `mock_repo.delete_branch_on_merge = delete_branch_on_merge` so the "all OK" path includes check 10.

2. **Add test class `TestAutoDeleteBranches`** with four test methods:
   - `test_enabled` — when `delete_branch_on_merge = True`, check is `ok=True`, value is `"auto-delete on merge"`, severity is `"warning"`
   - `test_disabled` — when `delete_branch_on_merge = False`, check is `ok=False`, value is `"not enabled"`, severity is `"warning"`
   - `test_present_when_no_branch_protection` — reuse the 404 pattern from `TestNoBranchProtection404._run`, verify `auto_delete_branches` key exists and is `ok=True` (repo setting works independently of branch protection)
   - `test_repo_not_accessible` — verify that when the repo is not accessible, `auto_delete_branches` is present with `ok=False`, value `"unknown"`, and an `error` field set

## HOW — Tests

- `test_enabled`: call `_patch_all_ok(tmp_path)` (default has `delete_branch_on_merge = True`), assert on `result["auto_delete_branches"]`
- `test_disabled`: call `_patch_all_ok(tmp_path, delete_branch_on_merge=False)`, assert `ok=False`, value `"not enabled"`, severity `"warning"`
- `test_present_when_no_branch_protection`: adapt the 404 test setup, set `mock_repo.delete_branch_on_merge = True`, verify the key is present and ok
- `test_repo_not_accessible`: reuse setup pattern from `TestBranchProtectionWhenRepoNotAccessible.test_all_five_present_and_not_ok` (set `mock_manager._get_repository.return_value = None` so repo is inaccessible), verify `auto_delete_branches` has `ok=False`, value `"unknown"`, and `error` field is set

## WHAT — Implementation

Add a single block in `verification.py` after the checks 5–9 section and before the `overall_ok` computation.

## HOW — Implementation

Insert after the closing of the checks 5–9 `if/else` block (the one guarded by `repo_is_ok`), before the `overall_ok` section.

## ALGORITHM

```
# Check 10: auto_delete_branches (repo-level setting)
if repo is accessible (repo_is_ok and repo is not None):
    if repo.delete_branch_on_merge:
        result["auto_delete_branches"] = ok, "auto-delete on merge", warning
    else:
        result["auto_delete_branches"] = not ok, "not enabled", warning
else:
    result["auto_delete_branches"] = not ok, "unknown", warning, error="repository not accessible"
```

## DATA

- Reads: `repo.delete_branch_on_merge` (bool) — PyGithub `Repository` property
- All checks use `CheckResult` TypedDict: `{ok: bool, value: str, severity: "warning"}`
- Key: `"auto_delete_branches"`
- OK value: `"auto-delete on merge"`
- WARN value: `"not enabled"`
- Fallback value: `"unknown"` with error

## INTEGRATION

- No new imports needed
- Uses existing `repo` and `repo_is_ok` variables already in scope
- `CheckResult` TypedDict already imported

## Commit

```
feat: add auto_delete_branches check to verify_github (#162)
```
