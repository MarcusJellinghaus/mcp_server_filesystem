# Step 1 — Job-Level CI Verdict + Failing-Job Names

## LLM Prompt

> Read `pr_info/steps/summary.md` for the design context, then implement Step 1 as described in `pr_info/steps/step_1.md`. Write tests first (TDD), then the implementation. All three code-quality checks (pylint, pytest, mypy) must pass before committing. This step produces exactly one commit.

## Scope

Make `_collect_ci_status` consult **job-level** conclusions and `jobs_fetch_warning`, then thread the failing-job names into `_generate_recommendations` so the user sees `"Fix failing job(s): <names>"` instead of the generic message.

**Out of scope for this step:** `mergeable_state` gating, end-to-end regression test through `collect_branch_status` (Step 2).

## WHERE

- `src/mcp_workspace/checks/branch_status.py`
- `tests/checks/test_branch_status.py` — extend `TestCollectCIStatus`
- `tests/checks/test_branch_status_recommendations.py` — extend `TestGenerateRecommendations`

## WHAT

### `_collect_ci_status` (modified signature)
```python
def _collect_ci_status(
    project_dir: Path, branch_name: str, max_log_lines: int
) -> tuple[CIStatus, Optional[str], list[str]]:
    """Returns (status, ci_details, failing_job_names)."""
```

### `_generate_recommendations` (modified body)
- Signature unchanged.
- Reads new key `report_data["ci_failing_job_names"]: list[str]` (default `[]`).
- When `ci_status == CIStatus.FAILED` and the list is non-empty, emit `f"Fix failing job(s): {', '.join(names)}"` *instead of* `"Fix CI test failures"`.

### `collect_branch_status` (call-site changes)
- Unpack the new 3-tuple from `_collect_ci_status`.
- Pass `ci_failing_job_names` into `report_data`.

## HOW (Integration Points)

- No new imports needed.
- No changes to `BranchStatusReport`, formatters, `CIResultsManager`, or `build_ci_error_details`.
- The existing `build_ci_error_details` call is now reached for *both* workflow-failure and "workflow-success-but-job-failed" cases. It already filters `jobs_data` by `conclusion == "failure"` (`ci_log_parser.py:244`), so no change there.

## ALGORITHM (core logic in `_collect_ci_status`)

```
# NOTE: This intentionally drops the existing `conclusion or status` fallback.
# `conclusion` is the authoritative completion field; `status` is only
# meaningful while the run is in flight. Branching explicitly on `conclusion`
# first (then on `status` for the in-flight cases) is clearer than the
# `or`-fallback expression. No behavior change for any valid GitHub payload.

_JOB_FAIL_CONCLUSIONS = frozenset({"failure", "cancelled", "timed_out"})
run_data = status_result["run"]
jobs_data = status_result["jobs"]
if not run_data: return (NOT_CONFIGURED, None, [])
failing_names = [j["name"] for j in jobs_data if j.get("conclusion") in _JOB_FAIL_CONCLUSIONS]
conclusion = run_data.get("conclusion")
status     = run_data.get("status", "")
if conclusion == "success":
    if failing_names:
        return (FAILED, build_ci_error_details(...), failing_names)
    if run_data.get("jobs_fetch_warning"):
        return (PENDING, None, [])
    return (PASSED, None, [])
if conclusion == "failure":
    return (FAILED, build_ci_error_details(...), failing_names)
if status in {"in_progress", "queued", "pending"}:
    return (PENDING, None, [])
return (NOT_CONFIGURED, None, [])
```

## DATA

- New module-level constant: `_JOB_FAIL_CONCLUSIONS: frozenset[str] = frozenset({"failure", "cancelled", "timed_out"})`
- `_collect_ci_status` return: `tuple[CIStatus, Optional[str], list[str]]`
- `report_data` key added: `"ci_failing_job_names": list[str]`

## Tests (write first)

In `tests/checks/test_branch_status.py` (`TestCollectCIStatus`):

1. `test_workflow_success_with_failed_job_returns_failed` — `run.conclusion="success"`, one job with `conclusion="failure"`, asserts `(FAILED, <details>, ["job-name"])`.
2. `test_workflow_success_with_cancelled_job_returns_failed` — same shape, `conclusion="cancelled"`.
3. `test_workflow_success_with_timed_out_job_returns_failed` — same shape, `conclusion="timed_out"`.
4. `test_workflow_success_clean_returns_passed_with_empty_names` — asserts `(PASSED, None, [])`.
5. `test_workflow_success_with_jobs_fetch_warning_returns_pending` — `run.jobs_fetch_warning` set, no jobs → `(PENDING, None, [])`.
6. Update every existing test method in `TestCollectCIStatus` (in `tests/checks/test_branch_status.py`) that calls `_collect_ci_status` to unpack the new 3-tuple. The complete list as of today:
   - `test_passed`
   - `test_failed`
   - `test_pending`
   - `test_not_configured`
   - `test_failed_with_details_exception`
   - `test_pending_via_status_fallback`
   - `test_exception_returns_not_configured`

   For each, change the unpack from `status, details = _collect_ci_status(...)` (or `status, _ = ...`) to `status, details, failing_names = _collect_ci_status(...)` (or `status, _, _ = ...`) and, where relevant, assert `failing_names == []`.

In `tests/checks/test_branch_status_recommendations.py` (`TestGenerateRecommendations`):

7. `test_failing_job_names_replace_generic_ci_message` — `ci_status=FAILED`, `ci_failing_job_names=["mssql-integration"]` → recs contain `"Fix failing job(s): mssql-integration"` and NOT `"Fix CI test failures"`.
8. `test_no_failing_job_names_keeps_generic_message` — `ci_status=FAILED`, no key / empty list → existing `"Fix CI test failures"` preserved.

## Acceptance Criteria

- All new tests pass.
- All existing tests still pass.
- `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_pytest_check` (with the recommended `-m "not …"` exclusions and `-n auto`), `mcp__mcp-tools-py__run_mypy_check` all clean.
- One commit named e.g. `feat(check): derive CI verdict from job-level conclusions (#207)`.
