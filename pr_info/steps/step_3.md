# Step 3: Change get_all_cached_issues to accept RepoIdentifier

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #158).
> **Depends on**: Step 1 (cache_safe_name already includes hostname).

## Goal
Change `get_all_cached_issues()` to accept a `RepoIdentifier` directly instead of a plain string, completing the API migration for Issue #158.

## Commit Message
`refactor: change get_all_cached_issues to accept RepoIdentifier`

## WHERE
- `src/mcp_workspace/github_operations/issues/cache.py` — `get_all_cached_issues()` (~line 264)
- `tests/github_operations/test_issue_cache.py` — `TestAdditionalIssuesParameter` (~lines 829-1192), `TestApiFailureHandling` (~lines 1194-1429), `TestLastFullRefresh` (~lines 1432-1601)

## WHAT

### Function signature change
```python
# BEFORE
def get_all_cached_issues(
    repo_full_name: str,
    issue_manager: "IssueManager",
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
    additional_issues: list[int] | None = None,
) -> List[IssueData]:

# AFTER
def get_all_cached_issues(
    repo_identifier: RepoIdentifier,
    issue_manager: "IssueManager",
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
    additional_issues: list[int] | None = None,
) -> List[IssueData]:
```

### Internal changes in function body
- Remove: `repo_identifier = RepoIdentifier.from_full_name(repo_full_name)` (~line 289)
- Use `repo_identifier` parameter directly (already used for `cache_safe_name` and `repo_name`)

## HOW
- `RepoIdentifier` is already imported in `cache.py`
- No changes to `__init__.py` exports needed (function name unchanged)

## ALGORITHM
```
1. Remove repo_identifier = RepoIdentifier.from_full_name(repo_full_name)
2. Use repo_identifier parameter directly
3. Update docstring: "repo_full_name: ..." → "repo_identifier: ..."
```

## DATA
- Input: `repo_identifier: RepoIdentifier` (fully qualified with hostname)
- Output: unchanged (`List[IssueData]`)

## Test Changes

All call sites that pass a string like `"owner/repo"` or `"test/repo"` must pass `RepoIdentifier.from_full_name(...)` instead.

**Affected test methods** (13 call sites):

### TestAdditionalIssuesParameter
- `test_additional_issues_fetched_and_cached` (line 899)
- `test_additional_issues_always_refreshed` (line 990)
- `test_no_additional_issues_backward_compatible` (line 1053)
- `test_additional_issues_with_api_failure` (line 1120)
- `test_additional_issues_empty_list` (line 1180)

### TestApiFailureHandling
- `test_api_failure_does_not_advance_last_checked` (line 1248)
- `test_api_failure_returns_stale_cached_issues` (line 1292)
- `test_api_failure_restores_snapshot_on_full_refresh` (line 1334)
- `test_repo_lookup_failure_does_not_advance_last_checked` (line 1377)
- `test_successful_fetch_still_advances_last_checked` (line 1419)

### TestLastFullRefresh
- `test_full_refresh_updates_last_full_refresh` (line 1477)
- `test_incremental_refresh_does_not_update_last_full_refresh` (line 1529)
- `test_full_refresh_triggers_when_last_full_refresh_is_old` (line 1580)

### Pattern
```python
# BEFORE
result = get_all_cached_issues("owner/repo", mock_cache_issue_manager, ...)

# AFTER
result = get_all_cached_issues(
    RepoIdentifier.from_full_name("owner/repo"), mock_cache_issue_manager, ...
)
```

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Implement Step 3 of Issue #158: Change `get_all_cached_issues()` in
`src/mcp_workspace/github_operations/issues/cache.py` to accept
`repo_identifier: RepoIdentifier` instead of `repo_full_name: str`.
Remove the internal `RepoIdentifier.from_full_name()` call. Then update
all call sites in `TestAdditionalIssuesParameter`, `TestApiFailureHandling`,
and `TestLastFullRefresh` in `tests/github_operations/test_issue_cache.py`
to pass RepoIdentifier instances. Run all quality checks after.
```
