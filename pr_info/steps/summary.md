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
- **Recommendation guard is fully additive.** All blocker lines (failing jobs, "Address review comments", "Not ready to merge (...)", rebase) emit independently whenever their respective conditions hold. The "Ready to merge" / "Ready to merge (squash-merge safe)" line emits only when *no* blocker fires.

## Architectural / Design Changes

| Area | Change |
|---|---|
| `_collect_ci_status` return type | `tuple[CIStatus, Optional[str]]` → `tuple[CIStatus, Optional[str], list[str]]` |
| Verdict rules added | (a) workflow=success + any job in `{failure, cancelled, timed_out}` → `FAILED`; (b) workflow=success + `jobs_fetch_warning` set → `PENDING` |
| `_generate_recommendations` new gate | `pr_mergeable_state ∈ {"unstable", "blocked", "dirty"}` blocks "Ready to merge" and emits a new line *independently* of CI/tasks state. `behind` is deliberately excluded (already handled by `_apply_pr_merge_override`). |
| `_generate_recommendations` lifted lines | Both `"Address review comments"` and `"Not ready to merge (GitHub mergeable_state: <state>)"` move *out* of the `if ci_ok and tasks_ok:` branch — they emit whenever their conditions hold, alongside any CI/task blockers. |
| `_generate_recommendations` "Ready to merge" gate | Emits only when `ci_ok and tasks_ok and not rebase_needed and not pr_blocks and not merge_state_blocked` — i.e., no blocker fires. |
| `_generate_recommendations` new wording | When `ci_failing_job_names` is non-empty: `"Fix failing job(s): n1, n2"` replaces `"Fix CI test failures"`. |
| `report_data` payload | Two new keys: `ci_failing_job_names`, `pr_mergeable_state`. |
| `CIResultsManager` | **No change** (preserves polling contract). |
| `build_ci_error_details` | **No change** — already filters `jobs_data` by `conclusion == "failure"` (`ci_log_parser.py:244`), so the new "workflow=success but jobs failed" path reuses it as-is. |
| `BranchStatusReport` dataclass / formatters | **No change** — `pr_mergeable_state` is already a field and already rendered. |

## Constants Introduced

- `_BLOCKING_MERGE_STATES: frozenset[str] = frozenset({"unstable", "blocked", "dirty"})` (private, module-level in `branch_status.py`; introduced in Step 2).
- `_JOB_FAIL_CONCLUSIONS: frozenset[str] = frozenset({"failure", "cancelled", "timed_out"})` (private, module-level in `branch_status.py`; introduced in Step 1) — mirrors `aggregate_conclusion` (`ci_results_manager.py:115`) for consistency.

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
