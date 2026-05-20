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
- Lifts BOTH `"Address review comments"` AND the new `"Not ready to merge (GitHub mergeable_state: <state>)"` lines OUT of the `if ci_ok and tasks_ok:` branch. They emit whenever their respective conditions hold, independent of CI/tasks state.
- The `"Ready to merge"` / `"Ready to merge (squash-merge safe)"` lines stay gated behind `ci_ok and tasks_ok and not rebase_needed and not pr_blocks and not merge_state_blocked` — i.e., emit only when *no* blocker fires.
- Signature unchanged.

### `collect_branch_status` (call-site change)
- Add `"pr_mergeable_state": pr_mergeable_state` to `report_data` (alongside the existing keys, at the section currently around `branch_status.py:671-680`).

## HOW (Integration Points)

- `pr_mergeable_state` is already collected by `_collect_pr_info` and already stored on `BranchStatusReport` and rendered by both formatters (Constraint F). The only missing wiring was into the recommender.
- `None` (no PR) and `"behind"` are naturally not in the blocker set, so no special-casing is needed (Constraints B, E).
- Recommendations are fully additive — when a PR has failing jobs AND blocking review AND `mergeable_state=unstable`, all three lines appear together. "Ready to merge" appears only when nothing else is blocking.

## ALGORITHM (delta in `_generate_recommendations`)

Read the existing `_generate_recommendations` in `src/mcp_workspace/checks/branch_status.py` and adapt the rewrite to its actual structure — in particular, preserve existing wording for `"Fix CI test failures"`, the rebase recommendation (today: `"Rebase onto origin/main"`), the task-tracker incomplete/error wording, and `"Check CI error details above"`. The point is the *structure*: ALL blocker lines emit independently; "Ready to merge" emits only when ALL blockers are clear.

```
pr_mergeable_state = report_data.get("pr_mergeable_state")
merge_state_blocked = pr_mergeable_state in _BLOCKING_MERGE_STATES
ci_failing_job_names = report_data.get("ci_failing_job_names", [])

# --- existing CI / tasks blocker blocks stay as-is (Step 1 wording for
#     "Fix failing job(s): ..." vs "Fix CI test failures" is preserved) ---

# blocker lines — emit independently
if ci_status == CIStatus.FAILED and ci_failing_job_names:
    recommendations.append(
        f"Fix failing job(s): {', '.join(ci_failing_job_names)}"
    )
elif ci_status == CIStatus.FAILED:
    recommendations.append("Fix CI test failures")
    # (plus the existing "Check CI error details above" follow-on)

# ... existing tasks / rebase / pending / not-configured blocks unchanged ...

if pr_blocks:
    recommendations.append("Address review comments")
if merge_state_blocked:
    recommendations.append(
        f"Not ready to merge (GitHub mergeable_state: {pr_mergeable_state})"
    )
# rebase keeps its existing wording — "Rebase onto origin/main" today
# (emitted by the existing `rebase_needed and tasks_ok and ci_status != FAILED` guard)

# "Ready to merge" only if nothing blocking
if (
    ci_ok
    and tasks_ok
    and not pr_blocks
    and not merge_state_blocked
    and not rebase_needed
):
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
7. `test_co_occurrence_additive` — `ci_status=FAILED`, `ci_failing_job_names=["mssql-integration"]`, `pr_feedback_blocks_merge=True`, `pr_mergeable_state="unstable"` → recs contain ALL THREE of: `"Fix failing job(s): mssql-integration"`, `"Address review comments"`, AND `"Not ready to merge (GitHub mergeable_state: unstable)"`. (All blocker lines are fully additive — see ALGORITHM above.)
8. `test_unstable_emits_even_when_ci_failed` — `ci_status=FAILED, pr_mergeable_state="unstable"` → recs contain `"Not ready to merge (GitHub mergeable_state: unstable)"`. Confirms the "Not ready to merge" line lifted out of the `ci_ok` branch.
9. `test_address_review_emits_even_when_ci_failed` — `ci_status=FAILED, pr_feedback_blocks_merge=True` → recs contain `"Address review comments"`. Regression test for the lifted behavior — this would *fail* under the current code, confirming the change is intentional.

### Existing tests to update

The following test methods in `tests/checks/test_branch_status_recommendations.py::TestPRFeedbackBlockingRecommendations` currently assert that `"Address review comments"` is *suppressed* when CI fails. They must be inverted (or rewritten) as part of Step 2, because the new behavior emits "Address review comments" independently of CI state:

- `test_no_review_rec_when_ci_failed` (lines ~247-259) — currently asserts `"Address review comments" not in recs` when `ci_status=FAILED, pr_feedback_blocks_merge=True`. Invert: now asserts `"Address review comments" in recs` *together with* `"Fix CI test failures"`. (This becomes redundant with the new `test_address_review_emits_even_when_ci_failed`; consider deleting it instead of inverting.)
- `test_no_review_rec_when_tasks_blocking` (lines ~261-273) — currently asserts `"Address review comments" not in recs` when tasks are incomplete + `pr_feedback_blocks_merge=True`. Same inversion logic: "Address review comments" now emits regardless of task state. Invert the assertion or delete in favor of the new symmetric `test_address_review_emits_even_when_ci_failed`.

Inspect any other tests in `test_branch_status_recommendations.py` for similar suppression assertions (`"Address review comments" not in recs` combined with a blocker condition) and invert them likewise.

### Regression test

In `tests/checks/test_branch_status.py`, new class `TestCollectBranchStatusRegressions`:

10. `test_issue_207_continue_on_error_scenario` — follow the same helper pattern as `TestCollectBranchStatus.test_full_collection`: patch the `_collect_*` helpers directly rather than mocking `CIResultsManager`/`PullRequestManager`/`IssueManager`/etc. Same coverage with a much smaller mock surface. Concretely, decorate with:

    ```python
    @patch("mcp_workspace.checks.branch_status._collect_pr_info")
    @patch("mcp_workspace.checks.branch_status._collect_github_label")
    @patch("mcp_workspace.checks.branch_status._collect_task_status")
    @patch("mcp_workspace.checks.branch_status._collect_rebase_status")
    @patch("mcp_workspace.checks.branch_status._collect_ci_status")
    @patch("mcp_workspace.checks.branch_status.detect_base_branch")
    @patch("mcp_workspace.checks.branch_status.PullRequestManager")
    @patch("mcp_workspace.checks.branch_status.IssueManager")
    @patch("mcp_workspace.checks.branch_status.extract_issue_number_from_branch")
    @patch("mcp_workspace.checks.branch_status.get_current_branch_name")
    ```

    Setup:
    - `mock_branch.return_value = "7-ms-sql-server-backend-pyodbc"`
    - `mock_ci.return_value = (CIStatus.FAILED, "<job details>", ["mssql-integration"])` — exact 3-tuple returned by the Step 1 `_collect_ci_status`.
    - `mock_pr_info.return_value = (45, "https://url", True, True, "unstable")` — matches `_collect_pr_info`'s 5-tuple (number, url, found, mergeable, mergeable_state).
    - `mock_rebase.return_value = (False, "up-to-date")`
    - `mock_tasks.return_value = (TaskTrackerStatus.N_A, "No pr_info folder found", False)`
    - `mock_label.return_value = "unknown"`
    - `mock_detect.return_value = "main"`
    - `mock_extract.return_value = 7`; issue manager returns empty/no labels.

    Asserts:
    - `report.ci_status == CIStatus.FAILED`
    - `"Ready to merge" not in report.recommendations`
    - `"Ready to merge (squash-merge safe)" not in report.recommendations`
    - `any("Fix failing job(s): mssql-integration" in r for r in report.recommendations)`
    - `any("Not ready to merge (GitHub mergeable_state: unstable)" in r for r in report.recommendations)`

## Acceptance Criteria

- All new tests pass.
- All existing tests still pass (including Step 1's).
- `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (with `-n auto` and the `-m "not …"` exclusions), `mcp__mcp-tools-py__run_mypy_check` all clean.
- Manual scan of `report.format_for_llm()` output for the regression scenario contains `"CI=FAILED"`, `"Mergeable_State=unstable"`, and the failing-job recommendation.
- One commit named e.g. `feat(check): gate "Ready to merge" on mergeable_state (#207)`.
