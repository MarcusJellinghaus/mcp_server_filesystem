# Plan Review Log — Run 1

**Issue:** #173
**Branch:** 173-check-branch-status-surface-unresolved-pr-review-threads-conversation-comments-and-code-scanning-alerts
**Date started:** 2026-04-29


## Round 1 — 2026-04-29

**Findings**:
- [Cross-cut] `_collect_pr_info` 5-tuple expansion noted as awkward — accepted as-is (INFO).
- [Step 1] `find_pull_request_by_head` test split lives in `test_pr_manager_find_by_head.py` — needs explicit listing.
- [Step 2] GraphQL `reviews(states: CHANGES_REQUESTED)` is not a valid arg — must filter client-side (DESIGN).
- [Step 2] "Latest review per reviewer" dedup not implemented — issue body wording vs. simpler approach (DESIGN).
- [Step 2] `@_handle_github_errors` `default_return` should be a lambda factory, matching existing pattern.
- [Step 2] Thread `path/line/author/body/diffHunk` source ("first comment") not stated explicitly.
- [Step 3] `_MAX_FEEDBACK_ITEMS=20` cap-ordering can drop alerts when unresolved threads fill the cap.
- [Step 3] `_MAX_LINES_PER_COMMENT` does not bound `diff_hunk` — needs explicit decision note.
- [Step 4] Missing explicit test for `rebase_needed=True` + `pr_mergeable=True` + `pr_feedback_blocks_merge=True` priority.
- [Step 4] `Mergeable_State=` rendering location and exact format string underspecified.

**Decisions**:
- Auto-accept (straightforward): Step 1 test-file listing; Step 2 lambda factory + first-comment clarification; Step 3 cap-order note + diff_hunk no-truncation note; Step 4 priority test + exact format string.
- Escalate (design): combined into one user question covering GraphQL syntax + per-reviewer dedup semantics.
- Skip: 5-tuple → struct refactor (out of scope, accepted as-is).

**User decisions**:
- Q: How should reviews be fetched/filtered? Options A=dedup-by-author then filter, B=fetch unfiltered, client-side filter to CHANGES_REQUESTED with no per-reviewer dedup, C=other.
- A: **B** — accept stale-CHANGES_REQUESTED-from-since-approved-reviewer as known limitation in exchange for simplicity.

**Changes**:
- `pr_info/steps/step_1.md` — added `test_pr_manager_find_by_head.py` to mergeable_state test file list.
- `pr_info/steps/step_2.md` — GraphQL query: `reviews(first: 50)` (unfiltered), client-side filter to `CHANGES_REQUESTED`, accepted-limitation note on no per-reviewer dedup; lambda factory for `default_return`; first-comment clarification for thread metadata extraction.
- `pr_info/steps/step_3.md` — feedback-cap drop-order documented; `diff_hunk` no-truncation marked as deliberate.
- `pr_info/steps/step_4.md` — new test `test_feedback_blocks_take_precedence_over_rebase_and_mergeable`; explicit `Mergeable_State=` format string for LLM and human renderings.

**Status**: changes applied to plan files; commit pending via commit agent.


## Round 2 — 2026-04-29

**Findings**:
- [Step 2] Lambda factory rationale ("shared mutable state across invocations") is incorrect — `_handle_github_errors` returns `default_return` directly via `return cast(T, default_return)` without invoking it. The pattern matches existing pr_manager.py precedent but the justification is misleading. INFO/cosmetic.
- [Step 4] New test `test_feedback_blocks_take_precedence_over_rebase_and_mergeable` documented as "locking in the `_apply_pr_merge_override` interaction" — but it exercises `_generate_recommendations` directly, not the override path. STRAIGHTFORWARD wording fix.
- [Cross-cut] `test_branch_status_polling.py` patches `find_pull_request_by_head` directly, so 4-tuple → 5-tuple expansion in `_collect_pr_info` does not affect it. INFO only.
- [Step 1, Summary] Naming convention and decision references verified — no drift.

**Decisions**:
- Auto-accept (straightforward): Step 2 rationale rewording + Step 4 test docstring softening.
- No design escalations needed in round 2.
- Skip: lambda factory pattern itself (out-of-scope; treat as separate cleanup if pursued).

**User decisions**: none required this round.

**Changes**:
- `pr_info/steps/step_2.md` — replaced misleading "shared mutable state" justification with accurate "matches existing pr_manager.py precedent" rationale; lambda usage unchanged.
- `pr_info/steps/step_4.md` — softened test docstring to clarify it verifies `_generate_recommendations` priority, not `_apply_pr_merge_override` directly.

**Status**: changes applied; commit pending via commit agent.


## Round 3 — 2026-04-29

**Findings**: none — plan verified internally consistent across summary.md and step_1.md–step_4.md. Round-2 wording fixes landed cleanly (Step 2 lambda rationale, Step 4 test docstring).

**Decisions**: no changes needed.

**User decisions**: none required.

**Changes**: none.

**Status**: review loop terminates — plan ready for approval.

## Final Status

**Rounds run:** 3 (1 with design escalation, 1 wording cleanup, 1 confirmation).

**Commits produced (plan files):**
- `c7950f9` — round 1: GraphQL reviews unfiltered + client-side CHANGES_REQUESTED filter; lambda factory for `default_return`; first-comment thread metadata; `test_pr_manager_find_by_head.py` listing; feedback-cap drop order; diff_hunk no-truncation; priority test; exact `Mergeable_State=` format.
- `5eebaba` — round 2: corrected misleading "shared mutable state" rationale → "matches existing precedent"; softened new test's docstring to reference `_generate_recommendations`, not `_apply_pr_merge_override`.

**Design decisions resolved:**
- Reviews fetched unfiltered, client-side filter to `CHANGES_REQUESTED`, no per-reviewer dedup (Option B — accepts stale `CHANGES_REQUESTED` from since-approved reviewers as a known limitation in exchange for simplicity).

**Outcome:** plan files in `pr_info/steps/` are ready for implementation. No further plan changes recommended.
