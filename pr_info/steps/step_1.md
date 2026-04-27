# Step 1: Add tests for auto_delete_branches check

**Context:** See `pr_info/steps/summary.md` for overall plan.

## LLM Prompt

> Implement step 1 of the plan in `pr_info/steps/summary.md`.
> Add tests for the new `auto_delete_branches` check (check 10) in `tests/github_operations/test_verification.py`.
> Also update the `_patch_all_ok` helper so it sets `mock_repo.delete_branch_on_merge = True`.
> Tests should fail until step 2 implements the production code. Run all three code quality checks after changes.

## WHERE

- `tests/github_operations/test_verification.py`

## WHAT

1. **Update `_patch_all_ok` helper** — set `mock_repo.delete_branch_on_merge = True` so the "all OK" path includes check 10.

2. **Add test class `TestAutoDeleteBranches`** with three test methods:
   - `test_enabled` — when `delete_branch_on_merge = True`, check is `ok=True`, value is `"auto-delete on merge"`, severity is `"warning"`
   - `test_disabled` — when `delete_branch_on_merge = False`, check is `ok=False`, value is `"not enabled"`, severity is `"warning"`
   - `test_present_when_no_branch_protection` — reuse the 404 pattern from `TestNoBranchProtection404._run`, verify `auto_delete_branches` key exists and is `ok=True` (repo setting works independently of branch protection)

## HOW

- `test_enabled`: call `_patch_all_ok(tmp_path)` (default has `delete_branch_on_merge = True`), assert on `result["auto_delete_branches"]`
- `test_disabled`: inside `_patch_all_ok`, after the mock_repo is created, override `mock_repo.delete_branch_on_merge = False` — but since `_patch_all_ok` doesn't expose that, instead create a dedicated helper call with a patched mock. Simplest: just duplicate the relevant mock setup inline (3-4 lines) or add a `delete_branch_on_merge` parameter to `_patch_all_ok` defaulting to `True`.
- `test_present_when_no_branch_protection`: adapt the 404 test setup, set `mock_repo.delete_branch_on_merge = True`, verify the key is present and ok

## DATA

- All checks use `CheckResult` TypedDict: `{ok: bool, value: str, severity: "warning"}`
- Key: `"auto_delete_branches"`
- OK value: `"auto-delete on merge"`
- WARN value: `"not enabled"`

## Commit

```
test: add tests for auto_delete_branches verification check (#162)
```
