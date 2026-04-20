# Plan Review Log — Issue #78

## Round 1 — 2026-04-20
**Findings**:
- [CRITICAL] Step 1 references non-existent test file `test_issue_manager_core.py` — should be `tests/github_operations/issues/test_list_issues.py` (matching existing topic-specific pattern)
- [CRITICAL] Step 1 claims PyGithub `labels` accepts `List[str]` for `get_issues()` — needs verification, may require `Label` objects
- [CRITICAL] Step 5 accesses private `_github_client` and `_get_repository()` — pragmatic but noted
- [ACCEPT] Step 4 `get_issue()` returns empty IssueData on 404 due to decorator — check pattern works but is a workaround
- [ACCEPT] Step 5 repo scoping can be simplified using `repo.full_name` instead of separate utility calls
- [ACCEPT] Steps 2-3 formatters `__init__.py` — no changes needed, direct import works
- [ACCEPT] Step 3 `Dict[str, Any]` vs `PullRequestData` — pragmatic given manual dict construction in step 5
- [SKIP] Steps 2-3 could be merged but are reasonable as separate small steps
- [SKIP] Plan covers all 4 tools from issue — no over/under-scoping

**Decisions**:
- Test file path: ACCEPT — fixed to `tests/github_operations/issues/test_list_issues.py`
- PyGithub labels: ACCEPT — added verification note with fallback approach
- Private access: SKIP — pragmatic for thin server layer, no clean public API exists
- Decorator behavior: ACCEPT — added explanatory comment in algorithm
- Repo scoping: ACCEPT — simplified to use `repo.full_name`

**User decisions**: None needed this round

**Changes**:
- `step_1.md`: Fixed test path, added labels verification note
- `step_4.md`: Added comment explaining decorator/empty-IssueData behavior
- `step_5.md`: Simplified search repo scoping to use `repo.full_name`

**Status**: Changes applied, re-review needed

## Round 2 — 2026-04-20
**Findings**:
- [CRITICAL] Step 5 `github_search` missing `None` check for `_get_repository()` return value — would crash with confusing AttributeError
- Round 1 fixes verified correct and consistent

**Decisions**:
- Repo None check: ACCEPT — added guard matching `github_pr_view`'s pattern

**User decisions**: None needed

**Changes**:
- `step_5.md`: Added `if not repo: return "Error: Could not access repository"` to `github_search` algorithm

**Status**: Changes applied, re-review needed

## Round 3 — 2026-04-20
**Findings**: None — all prior fixes verified correct and consistent
**Decisions**: N/A
**User decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Final Status

Plan review complete. 3 rounds, 2 with changes. Plan is ready for approval.

**Summary of changes made:**
- `step_1.md`: Fixed test path to `tests/github_operations/issues/test_list_issues.py`, added PyGithub labels verification note
- `step_4.md`: Added comment explaining `_handle_github_errors` decorator behavior for not-found case
- `step_5.md`: Simplified repo scoping to `repo.full_name`, added `None` guard for `_get_repository()`

