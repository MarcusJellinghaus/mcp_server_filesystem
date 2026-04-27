# Step 2: Implement check 10 in verification.py

**Context:** See `pr_info/steps/summary.md` for overall plan.

## LLM Prompt

> Implement step 2 of the plan in `pr_info/steps/summary.md`.
> Add check 10 (`auto_delete_branches`) to `verify_github()` in `src/mcp_workspace/github_operations/verification.py`.
> This should make the tests from step 1 pass. Run all three code quality checks after changes.

## WHERE

- `src/mcp_workspace/github_operations/verification.py`

## WHAT

Add a single block after the checks 5–9 section and before the `overall_ok` computation.

## HOW

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
- Key: `"auto_delete_branches"`
- Severity: `"warning"` (does not affect `overall_ok`)
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
