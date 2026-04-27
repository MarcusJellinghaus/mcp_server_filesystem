# Issue #158: Cache collision risk — cache_safe_name does not include hostname

## Problem
`RepoIdentifier.cache_safe_name` returns `"{owner}_{repo_name}"` without the hostname. Repos with the same `owner/repo` on different GitHub hosts (e.g., `github.com` vs `ghe.corp.com`) write to the same cache file, causing data corruption.

## Design Changes

### Architectural Change
The cache key namespace is expanded from `{owner}_{repo}` to `{hostname}_{owner}_{repo}` (dots replaced with underscores). This is a **one-line property change** in `RepoIdentifier` that ripples through the cache filename generation automatically.

### API Change
`update_issue_labels_in_cache()` and `get_all_cached_issues()` currently accept `repo_full_name: str` and internally construct a `RepoIdentifier` via `from_full_name()`. A plain string cannot carry hostname information, so these functions are changed to accept `repo_identifier: RepoIdentifier` directly. This is a **breaking change** to the public API — acceptable because GHE support is new and there are no in-repo callers beyond definitions/re-exports.

### Cache Invalidation
Existing `github.com` caches change from `owner_repo.issues.json` to `github_com_owner_repo.issues.json`. This invalidates caches once (one extra API fetch), which is acceptable since the cache is transient and self-healing.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/utils/repo_identifier.py` | `cache_safe_name` property: prepend hostname with dots→underscores |
| `src/mcp_workspace/github_operations/issues/cache.py` | `update_issue_labels_in_cache`: param `repo_full_name: str` → `repo_identifier: RepoIdentifier` |
| `src/mcp_workspace/github_operations/issues/cache.py` | `get_all_cached_issues`: param `repo_full_name: str` → `repo_identifier: RepoIdentifier` |
| `tests/github_operations/test_issue_cache.py` | Update all call sites to pass `RepoIdentifier` instead of strings |

No new files created.

## Implementation Steps

| Step | Commit | Summary |
|------|--------|---------|
| 1 | `fix: include hostname in cache_safe_name to prevent cache collisions` | Update `cache_safe_name` property + update `TestCacheFilePath` tests |
| 2 | `refactor: change update_issue_labels_in_cache to accept RepoIdentifier` | Change function signature + update `TestCacheIssueUpdate` and `TestCacheUpdateIntegration` tests |
| 3 | `refactor: change get_all_cached_issues to accept RepoIdentifier` | Change function signature + update `TestAdditionalIssuesParameter`, `TestApiFailureHandling`, `TestLastFullRefresh` tests |
