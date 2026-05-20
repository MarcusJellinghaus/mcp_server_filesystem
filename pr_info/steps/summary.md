# Implementation Summary — Issue #207

## Problem

`check_branch_status` reports `CI=PASSED` and recommends `Ready to merge` even when a GitHub Actions job has `conclusion: failure`. This happens when the failing job is declared `continue-on-error: true` in the workflow: GitHub rolls the **workflow-run** conclusion up as `success`, and the tool only inspects that field. The tool also already collects `pr.mergeable_state` (which GitHub flips to `unstable` in this scenario) but the recommender ignores it.

Net effect: the tool actively recommends merging a PR with visibly red checks.

## Goal

Make the verdict consult job-level conclusions, gate "Ready to merge" on `mergeable_state`, and surface the failing job name(s) in the recommendation. Do this with minimal code and no API changes outside the check itself.

## Design Approach (KISS)

- **One function, one place.** All verdict policy stays in `_collect_ci_status` (`branch_status.py`). No new `_derive_ci_verdict` helper — the existing function is already small and tested; we just extend it.
- **`CIResultsManager` untouched.** `run_data["conclusion"]` must continue to mirror GitHub's workflow-run conclusion verbatim because `branch_status_polling.py:53` polls it to decide when to stop. Verdict logic is *policy*; raw conclusion is *fact*.
- **Tuple expansion, not new dataclass.** `_collect_ci_status` returns `(CIStatus, Optional[str], list[str])` — the third slot is `failing_job_names`, threaded into `report_data` for the recommender. No `BranchStatusReport` field changes; no formatter changes.
- **Recommendation guard is additive.** Failing jobs + blocking review + `mergeable_state=unstable` all emit their own lines; no priority filter.

## Architectural / Design Changes

| Area | Change |
|---|---|
| `_collect_ci_status` return type | `tuple[CIStatus, Optional[str]]` → `tuple[CIStatus, Optional[str], list[str]]` |
| Verdict rules added | (a) workflow=success + any job in `{failure, cancelled, timed_out}` → `FAILED`; (b) workflow=success + `jobs_fetch_warning` set → `PENDING` |
| `_generate_recommendations` new gate | `pr_mergeable_state ∈ {"unstable", "blocked", "dirty"}` blocks "Ready to merge" and emits a new line. `behind` is deliberately excluded (already handled by `_apply_pr_merge_override`). |
| `_generate_recommendations` new wording | When `ci_failing_job_names` is non-empty: `"Fix failing job(s): n1, n2"` replaces `"Fix CI test failures"`. |
| `report_data` payload | Two new keys: `ci_failing_job_names`, `pr_mergeable_state`. |
| `CIResultsManager` | **No change** (preserves polling contract). |
| `build_ci_error_details` | **No change** — already filters `jobs_data` by `conclusion == "failure"` (`ci_log_parser.py:244`), so the new "workflow=success but jobs failed" path reuses it as-is. |
| `BranchStatusReport` dataclass / formatters | **No change** — `pr_mergeable_state` is already a field and already rendered. |

## Constants Introduced

- `BLOCKING_MERGE_STATES = {"unstable", "blocked", "dirty"}` (module-level in `branch_status.py`).
- Failing job-conclusion set `{"failure", "cancelled", "timed_out"}` — mirrors `aggregate_conclusion` (`ci_results_manager.py:115`) for consistency.

## Files / Modules Touched

**Modified:**
- `src/mcp_workspace/checks/branch_status.py`
- `tests/checks/test_branch_status.py`
- `tests/checks/test_branch_status_recommendations.py`

**Created:**
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`
- `pr_info/steps/step_2.md`

**Not touched (deliberately):**
- `src/mcp_workspace/github_operations/ci_results_manager.py` — Constraint A
- `src/mcp_workspace/github_operations/ci_log_parser.py` — Constraint D
- `src/mcp_workspace/checks/branch_status_polling.py` — depends on raw `run["conclusion"]`, which is preserved

## Step Overview

| Step | Title | Outcome |
|---|---|---|
| 1 | Job-level CI verdict + failing-job names in recommendation | Verdict reflects job failures; recommendation names them |
| 2 | `mergeable_state` recommendation guard + end-to-end regression test | "Ready to merge" suppressed for unstable/blocked/dirty; regression test mirrors the issue scenario |

Each step is one commit. Tests-first within each step.
