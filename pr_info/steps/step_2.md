# Step 2 — `mergeable_state` Recommendation Guard + Regression Test

## LLM Prompt

> Read `pr_info/steps/summary.md` for the design context and confirm Step 1 is merged, then implement Step 2 as described in `pr_info/steps/step_2.md`. Write tests first (TDD), then the implementation. All three code-quality checks (pylint, pytest, mypy) must pass before committing. This step produces exactly one commit.

## Scope

Gate the "Ready to merge" recommendation on GitHub's `mergeable_state` and emit an actionable line when blocked. Add one integration regression test that reproduces the issue scenario end-to-end through `collect_branch_status`.

**Pre-requisite:** Step 1 already landed — `_collect_ci_status` returns the 3-tuple and `ci_failing_job_names` flows through `report_data`.

## WHERE

- `src/mcp_workspace/checks/branch_status.py`
- `tests/checks/test_branch_status_recommendations.py` — extend with a new `TestMergeableStateGuard` class
- `tests/checks/test_branch_status.py` — add a regression test under a new `TestCollectBranchStatusRegressions` class

## WHAT

### Module-level constant (new)
```python
_BLOCKING_MERGE_STATES: frozenset[str] = frozenset({"unstable", "blocked", "dirty"})
```

### `_generate_recommendations` (modified body)

- Reads new key `report_data["pr_mergeable_state"]: Optional[str]`.
- Computes `merge_state_blocked = pr_mergeable_state in _BLOCKING_MERGE_STATES`.
- Gates the existing "Ready to merge" / "Ready to merge (squash-merge safe)" branch on `not merge_state_blocked`.
- When `merge_state_blocked` and the rec would otherwise be "Ready to merge", append `f"Not ready to merge (GitHub mergeable_state: {pr_mergeable_state})"` instead.
- Signature unchanged.

### `collect_branch_status` (call-site change)
- Add `"pr_mergeable_state": pr_mergeable_state` to `report_data` (alongside the existing keys, at the section currently around `branch_status.py:671-680`).

## HOW (Integration Points)

- `pr_mergeable_state` is already collected by `_collect_pr_info` and already stored on `BranchStatusReport` and rendered by both formatters (Constraint F). The only missing wiring was into the recommender.
- `None` (no PR) and `"behind"` are naturally not in the blocker set, so no special-casing is needed (Constraints B, E).
- Recommendations remain additive — when a PR has failing jobs AND `mergeable_state=unstable`, both lines appear (Decision 12).

## ALGORITHM (delta in `_generate_recommendations`)

```
pr_mergeable_state = report_data.get("pr_mergeable_state")
merge_state_blocked = pr_mergeable_state in _BLOCKING_MERGE_STATES

# inside the existing "ci_ok and tasks_ok" branch:
if pr_blocks:
    recommendations.append("Address review comments")
elif merge_state_blocked:
    recommendations.append(
        f"Not ready to merge (GitHub mergeable_state: {pr_mergeable_state})"
    )
elif not rebase_needed:
    if pr_mergeable is True:
        recommendations.append("Ready to merge (squash-merge safe)")
    else:
        recommendations.append("Ready to merge")
```

## DATA

- New module-level constant `_BLOCKING_MERGE_STATES`.
- `report_data` key added: `"pr_mergeable_state": Optional[str]`.
- No dataclass / formatter changes.

## Tests (write first)

In `tests/checks/test_branch_status_recommendations.py`, new class `TestMergeableStateGuard`:

1. `test_unstable_blocks_ready_to_merge` — all other signals good, `pr_mergeable_state="unstable"` → recs contain `"Not ready to merge (GitHub mergeable_state: unstable)"`, NOT `"Ready to merge"` or `"Ready to merge (squash-merge safe)"`.
2. `test_blocked_blocks_ready_to_merge` — same with `"blocked"`.
3. `test_dirty_blocks_ready_to_merge` — same with `"dirty"`.
4. `test_behind_does_not_block` — `pr_mergeable_state="behind"`, `pr_mergeable=True` → recs contain `"Ready to merge (squash-merge safe)"`. (Confirms `behind` is excluded — Constraint B.)
5. `test_none_does_not_block` — `pr_mergeable_state=None` → "Ready to merge" still emitted.
6. `test_clean_does_not_block` — `pr_mergeable_state="clean"` → "Ready to merge" still emitted.
7. `test_co_occurrence_additive` — `ci_status=FAILED`, `ci_failing_job_names=["mssql-integration"]`, `pr_feedback_blocks_merge=True`, `pr_mergeable_state="unstable"` → recs contain ALL of: `"Fix failing job(s): mssql-integration"`, `"Address review comments"`. (Note: `"Not ready to merge..."` is gated under the `ci_ok and tasks_ok` branch in the current structure, so when CI fails it won't appear — verify against the actual algorithm in the existing code; if the test author wants it to appear unconditionally, lift the emit out of the ci_ok branch. Default: keep it inside, since "fix CI" is the user's first action anyway.)

In `tests/checks/test_branch_status.py`, new class `TestCollectBranchStatusRegressions`:

8. `test_issue_207_continue_on_error_scenario` — uses `unittest.mock.patch` on `CIResultsManager`, `PullRequestManager`, `IssueManager`, `needs_rebase`, and `extract_issue_number_from_branch` (or `get_current_branch_name`) to construct the exact issue scenario:
   - Branch: `"7-ms-sql-server-backend-pyodbc"`.
   - `get_latest_ci_status` returns `run.conclusion="success"` plus jobs including one named `"mssql-integration"` with `conclusion="failure"` and several others with `conclusion="success"`.
   - `find_pull_request_by_head` returns one PR with `mergeable=True`, `mergeable_state="unstable"`.
   - No `pr_info` folder (or empty).
   - Calls `collect_branch_status(...)`.
   - Asserts: `report.ci_status == CIStatus.FAILED`, `"Ready to merge" not in report.recommendations`, `"Ready to merge (squash-merge safe)" not in report.recommendations`, `any("Fix failing job(s): mssql-integration" in r for r in report.recommendations)`.

## Acceptance Criteria

- All new tests pass.
- All existing tests still pass (including Step 1's).
- `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with `-n auto` and the `-m "not …"` exclusions), `mcp__tools-py__run_mypy_check` all clean.
- Manual scan of `report.format_for_llm()` output for the regression scenario contains `"CI=FAILED"`, `"Mergeable_State=unstable"`, and the failing-job recommendation.
- One commit named e.g. `feat(check): gate "Ready to merge" on mergeable_state (#207)`.
