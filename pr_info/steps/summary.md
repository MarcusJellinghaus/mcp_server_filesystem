# Summary — Surface PR review threads, conversation comments, and code-scanning alerts in `check_branch_status`

Issue: [#173](https://github.com/MarcusJellinghaus/mcp-tools-py/issues/173)

## Goal

Today `mcp__workspace__check_branch_status` reports CI status, rebase state, task completion, GitHub label, and mergeability — but is silent about unresolved PR review threads, conversation comments, and code-scanning alerts (e.g. CodeQL). This produces false-positive "Ready to merge" recommendations when reviewers have left open suggestions.

This implementation extends `BranchStatusReport` and the PR collection path to fetch and render this feedback alongside CI/task/rebase data. Recommendations are gated so "Ready to merge" only surfaces when reviews are clean, and "Address review comments" appears when CI passes and tasks are complete.

## Architecture / Design Changes

The change is **purely additive** within existing layer boundaries — no new modules, no changes to `tach.toml` / `.importlinter`.

| Layer | Change |
|-------|--------|
| `github_operations/pr_manager.py` | Add `mergeable_state` to `PullRequestData` TypedDict; add one new public method `get_pr_feedback()` returning a single `PRFeedback` TypedDict. Three private helpers (GraphQL threads+reviews, REST conversation comments, REST code-scanning alerts) live inside this module. Reuses existing `_handle_github_errors` decorator and `_Github__requester.graphql_query` plumbing already established in `get_closing_issue_numbers`. |
| `checks/branch_status.py` | Add 2 fields to `BranchStatusReport` (`pr_mergeable_state`, `pr_feedback_text`) and 1 boolean (`pr_feedback_blocks_merge`). Add 1 pure formatter `_format_pr_feedback()` and 1 collector `_collect_pr_feedback()`. Wire into `collect_branch_status()` and splice text into both `format_for_human` / `format_for_llm`. Gate `_generate_recommendations()` on the new boolean. |

### Why this shape (KISS choices)

- **One public API method** (`get_pr_feedback`) instead of four: callers always need all three sources together; private helpers are an implementation detail.
- **One TypedDict** (`PRFeedback`) instead of per-item TypedDicts: lists of plain dicts are sufficient and match existing patterns in this codebase.
- **Format once, store as text** on the report (decision #18 in the issue says human and LLM show identical content): avoids duplicated formatting logic. Recommendation logic uses a single boolean flag (`pr_feedback_blocks_merge`).
- **Inline "unavailable (API error)" placeholders** in the formatted text: no separate structured field for unavailable sections.

### Hard-coded constants (per issue decision #5)

```python
_MAX_FEEDBACK_ITEMS = 20         # max comments shown
_MAX_LINES_PER_COMMENT = 10      # body truncation per comment
```

### Recommendation rules (per issue decisions #6 and #16)

- Unresolved threads OR `CHANGES_REQUESTED` reviews OR open code-scanning alerts → block "Ready to merge".
- "Address review comments" recommendation appears **only when CI passes AND tasks are complete** (avoid stacking on top of CI/task fixes which take precedence).
- Code-scanning alerts: silent skip on 403 (most PATs lack `security_events: read`); other failures render as inline "unavailable (API error)".

## Files to be created or modified

### Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/github_operations/pr_manager.py` | Add `mergeable_state` field; add `PRFeedback` TypedDict; add `get_pr_feedback()` method with private helpers. |
| `src/mcp_workspace/checks/branch_status.py` | Add 3 fields to `BranchStatusReport`; add `_format_pr_feedback`, `_collect_pr_feedback`; wire into `collect_branch_status`; update both formatters and `_generate_recommendations`. |
| `tests/github_operations/test_pr_manager.py` | Extend with `mergeable_state` assertions on existing PR builders. |
| `tests/checks/test_branch_status_pr_fields.py` | Extend with `mergeable_state` and `pr_feedback_text` rendering tests. |
| `tests/checks/test_branch_status_recommendations.py` | Extend with feedback-blocking tests for `_generate_recommendations`. |

### Created

| File | Purpose |
|------|---------|
| `tests/github_operations/test_pr_manager_feedback.py` | Mock-only tests for `get_pr_feedback()` (success, empty, 403 silent skip, error → "unavailable"). |
| `tests/checks/test_branch_status_pr_feedback.py` | Tests for `_format_pr_feedback()` (clean, threads, comments, alerts, truncation, unavailable placeholders). |

## Implementation Steps

1. **Step 1** — Add `mergeable_state` field to `PullRequestData` and populate in all 5 builders.
2. **Step 2** — Add `PRFeedback` TypedDict + `get_pr_feedback()` method on `PullRequestManager`.
3. **Step 3** — Add `_format_pr_feedback()` pure formatting helper in `branch_status.py`.
4. **Step 4** — Wire `_collect_pr_feedback` into `collect_branch_status`, extend `BranchStatusReport`, splice formatted text into both formatters, gate recommendations.

Each step is self-contained with tests + implementation + all checks (pylint, pytest, mypy) green = one commit.
