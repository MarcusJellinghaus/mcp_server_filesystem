# Step 3: Add branch protection checks (5–9) to `verify_github()`

**Ref:** See `pr_info/steps/summary.md` for full context (Issue #157).

## LLM Prompt

> Implement Step 3 of the verify_github plan (see `pr_info/steps/summary.md`).
> Add branch protection checks 5–9 to `verify_github()` in `verification.py`.
> These checks use `get_default_branch()` from Step 1 and a single `get_protection()` call.
> Follow TDD: write tests first, then implement. Run all quality checks before committing.

## WHERE

| File | Action |
|------|--------|
| `tests/github_operations/test_verification.py` | Add tests for checks 5–9 |
| `src/mcp_workspace/github_operations/verification.py` | Add branch protection logic to `verify_github()` |

## WHAT

Add branch protection checks inside `verify_github()` after check 4 (repo accessible). Uses the `repo` object already obtained in check 4.

## HOW

- After check 4, if `repo` is available, call `manager.get_default_branch()` to get branch name
- Call `repo.get_branch(default_branch)` then `branch.get_protection()`
- Single `get_protection()` call feeds checks 5–9
- `GithubException(404)` from `get_protection()` → all five checks report `ok: False` as warnings
- If repo was not accessible (check 4 failed), all five checks report `ok: False` with appropriate error

## ALGORITHM

```
# After check 4, if repo is available:
default_branch_name = manager.get_default_branch()
branch = repo.get_branch(default_branch_name)
try:
    protection = branch.get_protection()
except GithubException(404):
    # No protection — all 5 checks fail as warnings
    set checks 5-9 to ok=False, severity="warning"
    return

# Check 5: branch_protection — protection exists
result["branch_protection"] = ok=True, value=f"{default_branch_name} protected"

# Check 6: ci_checks_required — protection.required_status_checks is not None
status_checks = protection.required_status_checks
result["ci_checks_required"] = report count of checks or "not configured"

# Check 7: strict_mode — status_checks.strict is True
result["strict_mode"] = ok if strict else not ok

# Check 8: force_push — protection.allow_force_pushes is False
result["force_push"] = ok if disabled (False) else not ok

# Check 9: branch_deletion — protection.allow_deletions is False
result["branch_deletion"] = ok if disabled (False) else not ok
```

### Key detail: PyGithub protection API

- `branch.get_protection()` → `BranchProtection` object
- `protection.required_status_checks` → `RequiredStatusChecks | None`
- `protection.required_status_checks.contexts` → `list[str]` (the check names)
- `protection.required_status_checks.strict` → `bool`
- `protection.allow_force_pushes` → `bool` (PyGithub returns the raw value)
- `protection.allow_deletions` → `bool`
- **`required_status_checks` nullability**: When the GitHub API returns `null` for `required_status_checks`, PyGithub may return `None` or its `NotSet` sentinel. The implementation should check for both: `if status_checks is None or isinstance(status_checks, _NotSetType)`. Test with a mock returning `None` to cover this path.

### Key detail: Graceful handling when repo not accessible

If check 4 failed (`repo is None`), checks 5–9 still report — they all set `ok: False` with error `"repository not accessible"`. This preserves check independence.

## DATA

Checks 5–9 added to the return dict:

```python
{
    # ... checks 1-4 from Step 2 ...
    "branch_protection": {"ok": True, "value": "main protected", "severity": "warning"},
    "ci_checks_required": {"ok": True, "value": "8 checks configured", "severity": "warning"},
    "strict_mode": {"ok": True, "value": "enabled", "severity": "warning"},
    "force_push": {"ok": True, "value": "disabled", "severity": "warning"},
    "branch_deletion": {"ok": True, "value": "disabled", "severity": "warning"},
}
```

## TESTS

Add to `tests/github_operations/test_verification.py`:

| Test | Setup | Assertion |
|------|-------|-----------|
| `test_branch_protection_all_pass` | Mock full protection with strict, no force push, no deletions, status checks | All 5 checks `ok: True` |
| `test_no_branch_protection_404` | `get_protection()` raises `GithubException(404)` | All 5 checks `ok: False`, `severity: "warning"`, `overall_ok: True` |
| `test_no_status_checks_configured` | `required_status_checks` is `None` | `ci_checks_required.ok = False`, `strict_mode.ok = False` |
| `test_strict_mode_disabled` | `strict = False` | `strict_mode.ok = False`, value `"disabled"` |
| `test_force_push_enabled` | `allow_force_pushes = True` | `force_push.ok = False` |
| `test_branch_deletion_enabled` | `allow_deletions = True` | `branch_deletion.ok = False` |
| `test_branch_protection_checks_when_repo_not_accessible` | `_get_repository()` returns `None` | All 5 branch checks present with `ok: False` |
| `test_default_branch_name_in_protection_value` | `default_branch = "develop"` | `branch_protection.value` contains `"develop"` |
| `test_overall_ok_true_when_only_warnings_fail` | Connectivity passes, protection fails | `overall_ok: True` |

Mock strategy: Build on Step 2's mocking. Add `mock_repo.default_branch`, `mock_repo.get_branch()`, and `mock_branch.get_protection()` to the fixture chain.

## COMMIT

```
feat: add branch protection checks to verify_github() (#157)
```
