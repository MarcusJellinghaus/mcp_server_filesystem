# Plan Review Log — Issue #207

Branch: `207-check-branch-status-reports-ci-passed-when-a-failing-job-is-masked-by-continue-on-error-true`
Base: `main`
Started: 2026-05-20


## Round 1 — 2026-05-20

**Findings:**
- *Critical:* Step 2 `test_co_occurrence_additive` asserts `"Address review comments"` emits when `ci_status=FAILED`, but the existing `_generate_recommendations` gates that line behind `ci_ok and tasks_ok`. As written, the test would fail.
- *Suggestion:* Constant name inconsistency between summary (`BLOCKING_MERGE_STATES`) and steps (`_BLOCKING_MERGE_STATES`).
- *Suggestion:* Step 1's "update existing tests" list is incomplete — missing `test_pending_via_status_fallback` (and any other 2-tuple unpackers in `TestCollectCIStatus`).
- *Suggestion:* Tool-prefix typo in acceptance criteria — `mcp__tools-py__` should be `mcp__mcp-tools-py__`.
- *Suggestion:* Step 2 regression test 8 mocks `CIResultsManager` + `PullRequestManager` + `IssueManager` + helpers — overkill. Existing `TestCollectBranchStatus.test_full_collection` patches the `_collect_*` helpers directly with much smaller surface.
- *Awareness only:* New `_collect_ci_status` algorithm subtly drops the `conclusion or status` fallback — intentional (conclusion is the authoritative completion field) but worth noting in the ALGORITHM comment.
- *Verified accurate:* All asserted paths/structures exist; Constraints A, D, F confirmed against source; failure conclusion set matches `aggregate_conclusion`; step granularity (2 commits) is appropriate.

**Decisions:**
- Accept the critical finding — but the *resolution* depends on a user decision (see User decisions below).
- Accept all suggestions and apply them.
- Awareness note: add a comment in step_1.md ALGORITHM about the fallback drop; no behavior change in plan.

**User decisions:**
- *Q:* Issue #207 Decision 12 says recommendations are "additive — emit every applicable line. No priority filter." But `_generate_recommendations` currently gates `"Address review comments"` behind `ci_ok and tasks_ok`, suppressing it when CI fails. Should "additive" be applied (a) conservatively (preserve current gating), (b) only to the new merge-state line, or (c) fully (lift all blocker lines out of the CI gate)?
- *A:* **Option 3 — fully additive.** Lift `"Address review comments"` AND `"Not ready to merge (...)"` out of the `ci_ok and tasks_ok` gate. All blocker lines emit independently; `"Ready to merge"` only when no blocker fires. Rationale: transparency — user sees all applicable blockers at once.

**Changes:**
- `pr_info/steps/summary.md` — Design Approach + Architectural table updated for fully-additive blockers; split "Ready to merge" gate; renamed constants to `_BLOCKING_MERGE_STATES` and `_JOB_FAIL_CONCLUSIONS` (both private).
- `pr_info/steps/step_1.md` — Tests item 6 expanded with full unpack list; ALGORITHM comment about fallback drop; tool-prefix typo fixed.
- `pr_info/steps/step_2.md` — ALGORITHM rewritten for fully-additive structure; `test_co_occurrence_additive` now asserts all three lines; added `test_unstable_emits_even_when_ci_failed` and `test_address_review_emits_even_when_ci_failed`; new "Existing tests to update" subsection (lists `test_no_review_rec_when_ci_failed`, `test_no_review_rec_when_tasks_blocking` for inversion); regression test rewritten to patch `_collect_*` helpers instead of managers; tool-prefix typo fixed.

**Status:** plan changed — committing and looping for round 2.


## Round 2 — 2026-05-20

**Findings:**
- *Critical:* Step 1's "update existing tests" list was scoped to `TestCollectCIStatus` and missed 3 tests in `TestCollectBranchStatus` (`test_full_collection`, `test_github_init_failure`, `test_rebase_behind_but_mergeable_squash_safe`) that mock `_collect_ci_status.return_value` as 2-tuples. After the signature change these will raise `ValueError: not enough values to unpack`.
- *Suggestion:* Note that the rebase recommendation is deliberately NOT lifted out of its `tasks_ok and ci_status != FAILED` gate under the fully-additive design — only merge-readiness blockers go additive.
- *Suggestion (skipped):* Make algorithm reference dict-key names explicitly — trivial.
- *Suggestion (skipped):* Add a "rebase alone suppresses Ready to merge" test — already implied by existing tests.
- *Round 1 fixes verified:* constants renamed consistently, fully-additive algorithm correctly described, `test_co_occurrence_additive` updated, new tests listed, "Existing tests to update" identifies the right suppression tests, Step 1 item 6 covers all `TestCollectCIStatus` callers, tool-prefix fixed, regression test uses `_collect_*` helper-patch pattern, fallback-drop comment added.

**Decisions:**
- Accept critical finding — apply.
- Accept first suggestion — apply.
- Skip the two trivial/redundant suggestions.

**User decisions:** None — autonomous round.

**Changes:**
- `pr_info/steps/step_1.md` — added item 6b listing the three `TestCollectBranchStatus` tests with 2-tuple mocks plus a re-grep instruction.
- `pr_info/steps/summary.md` — added a one-line note under "Design Approach (KISS)" clarifying the rebase recommendation stays gated behind `tasks_ok and ci_status != FAILED`; only merge-readiness blockers become fully additive.

**Status:** plan changed — committing and looping for round 3.


## Round 3 — 2026-05-20

**Findings:** None worth churning a commit for. Plan is internally consistent; round-2 fixes verified in place; blocker semantics match between summary table and Step 2 algorithm; constants and tool prefixes correct; TDD/one-commit-per-step structure preserved.

**Decisions:** No changes.

**User decisions:** None.

**Changes:** None.

**Status:** no plan changes — convergence reached.

---

## Final Status

**Rounds run:** 3 (rounds 1 and 2 produced plan changes; round 3 converged with no changes).

**Commits produced:**
- `ede67eb` — `docs(plan): apply round 1 plan review — additive recommendations and small fixes (#207)`
- `48b2a43` — `docs(plan): round 2 — extend test-update list and note rebase gating (#207)`

**User decisions made:** 1 — fully additive recommendations (round 1).

**Plan is ready for approval.** Step 1 and Step 2 are well-scoped, one-commit-each, tests-first, with all 12 issue decisions covered and constraints honored.
