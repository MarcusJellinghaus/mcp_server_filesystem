# Implementation Review Log — Issue #173

Branch: `173-check-branch-status-surface-unresolved-pr-review-threads-conversation-comments-and-code-scanning-alerts`
Started: 2026-04-29
Supervisor: `/implementation_review_supervisor`

## Round 1 — 2026-04-29

**Findings** (from review subagent):

- F1 — `pr_manager.py:525` `@_handle_github_errors(default_return=_empty_pr_feedback)` passes the function object instead of calling it; the decorator does `cast(T, default_return)` and won't invoke callables. Pre-existing pattern across the file (other call sites use `lambda: cast(...)` with the same flaw); unreachable in `get_pr_feedback` because the body catches every exception per-section.
- F2 — `pr_feedback.py:51` & `:74` would render `path:None` literally when GraphQL returns `line: null` (outdated/file-level threads, alerts without a specific line). Cosmetic.
- F3 — `branch_status.py` at 743 lines, close to the 750-line CI ceiling.
- F4 — `pr_manager.py` at 615 lines, over the 600-line warning threshold but under the 750 hard limit.
- F5 — When only `unavailable` has entries, the rendered output is just a `PR Reviews:` header followed by `[unavailable] ...:`. Behaves as designed per spec.

**Quality checks** (all green):
- pylint: clean
- pytest: 1426 passed, 2 skipped
- mypy: clean
- lint-imports: 9 contracts kept, 0 broken
- vulture: 1 finding at 60% confidence — `resolved_thread_count` (TypedDict field, false positive)

**Decisions**:

- F1 — **Skip**. Pre-existing decorator pattern; the actual code path for `get_pr_feedback` catches exceptions per-section so the unreachable branch is harmless. Out of scope for #173.
- F2 — **Accept**. Small, bounded user-facing fix.
- F3 — **Skip**. Under CI limit; splitting `branch_status.py` is out of scope for #173.
- F4 — **Skip**. Under CI hard limit (750).
- F5 — **Skip**. Behaves as designed.

**Changes**:

The engineer subagent verified that the F2 fix is **already implemented** in the working tree:

- `src/mcp_workspace/checks/pr_feedback.py` already uses `location = f"{path}:{line_no}" if line_no else path` at both call sites (unresolved threads and alerts).
- `tests/checks/test_branch_status_pr_feedback.py` already covers both `line_no is None` cases (`test_unresolved_thread_without_line_no`, `test_alert_without_line_no`) and explicitly asserts `:None not in result`.

No edits needed. Round 1 produced **zero code changes** — loop exit condition met.

**Status**: No changes — loop exits after one round.

## Final Status

**Rounds run**: 1 (zero-change round, loop exited).
**Commits produced**: none — no code changes accepted that weren't already implemented.
**Issue #173 requirements**: fully covered (verified by review subagent against the issue spec and decisions table).

**Final checks**:
- pylint: clean
- pytest: 1426 passed, 2 skipped, 0 failures
- mypy: clean
- lint-imports: 9 contracts kept, 0 broken
- vulture: 1 known TypedDict false positive at 60% confidence (`resolved_thread_count`). Not worth introducing whitelist infrastructure for a single 60%-confidence finding; informational only.

**Architecture**: layered-architecture, library-isolation, and source/tests independence contracts all kept. No new modules outside the planned shape (`_pr_feedback_sources.py`, `pr_feedback.py`).

**Implementation is ready for PR review.**
