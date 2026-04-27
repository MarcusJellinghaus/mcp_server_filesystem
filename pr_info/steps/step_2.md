# Step 2: Change update_issue_labels_in_cache to accept RepoIdentifier

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #158).
> **Depends on**: Step 1 (cache_safe_name already includes hostname).

## Goal
Change `update_issue_labels_in_cache()` to accept a `RepoIdentifier` directly instead of a plain string, eliminating the internal `from_full_name()` call that can't carry hostname info.

## Commit Message
`refactor: change update_issue_labels_in_cache to accept RepoIdentifier`

## WHERE
- `src/mcp_workspace/github_operations/issues/cache.py` — `update_issue_labels_in_cache()` (~line 145)
- `tests/github_operations/test_issue_cache.py` — `TestCacheIssueUpdate` class (~lines 349-667) and `TestCacheUpdateIntegration` class (~lines 669-827)

## WHAT

### Function signature change
```python
# BEFORE
def update_issue_labels_in_cache(
    repo_full_name: str, issue_number: int, old_label: str, new_label: str
) -> None:

# AFTER
def update_issue_labels_in_cache(
    repo_identifier: RepoIdentifier, issue_number: int, old_label: str, new_label: str
) -> None:
```

### Internal changes in function body
- Remove: `repo_identifier = RepoIdentifier.from_full_name(repo_full_name)` (~line 169)
- Update log messages: replace `repo_full_name` with `repo_identifier.full_name`

## HOW
- `RepoIdentifier` is already imported in `cache.py`
- No changes to `__init__.py` exports needed (function name unchanged)

## ALGORITHM
```
1. Remove repo_identifier = RepoIdentifier.from_full_name(repo_full_name)
2. Use repo_identifier parameter directly
3. Replace repo_full_name references in log messages with repo_identifier.full_name
4. Remove the `except ValueError` clause — the broad `except Exception` handler must remain
```

## DATA
- Input: `repo_identifier: RepoIdentifier` (fully qualified with hostname)
- Output: unchanged (`None`)

## Test Changes

All call sites in `TestCacheIssueUpdate` and `TestCacheUpdateIntegration` that pass a string like `"test/repo"` must pass `RepoIdentifier.from_full_name("test/repo")` instead.

**Affected test methods** (11 call sites across these methods):
- `test_update_issue_labels_success` (line 386)
- `test_update_issue_labels_remove_only` (line 432)
- `test_update_issue_labels_add_only` (line 475)
- `test_update_issue_labels_missing_issue` (line 524)
- `test_update_issue_labels_invalid_cache_structure` (line 555)
- `test_update_issue_labels_file_permission_error` (line 604)
- `test_update_issue_labels_logging` (line 647)
- `test_dispatch_workflow_updates_cache` (line 710)
- `test_multiple_dispatches_update_cache_correctly` (lines 770, 776)
- `test_cache_update_failure_does_not_break_dispatch` (line 812)

### Pattern
```python
# BEFORE
update_issue_labels_in_cache("test/repo", 123, "old-label", "new-label")

# AFTER
update_issue_labels_in_cache(
    RepoIdentifier.from_full_name("test/repo"), 123, "old-label", "new-label"
)
```

**Note**: The `test_update_issue_labels_missing_issue` test asserts on log message `"Issue #123 not found in cache for test/repo"`. After the change, `repo_identifier.full_name` still returns `"test/repo"`, so log assertions remain valid.

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for full context.

Implement Step 2 of Issue #158: Change `update_issue_labels_in_cache()` in
`src/mcp_workspace/github_operations/issues/cache.py` to accept
`repo_identifier: RepoIdentifier` instead of `repo_full_name: str`.
Remove the internal `RepoIdentifier.from_full_name()` call. Then update
all call sites in `TestCacheIssueUpdate` and `TestCacheUpdateIntegration`
in `tests/github_operations/test_issue_cache.py` to pass RepoIdentifier
instances. Run all quality checks after.
```
