# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Include hostname in cache_safe_name
- [x] Implementation: update `cache_safe_name` property and tests (`TestCacheFilePath`, `test_cache_safe_name_property`, add GHE test)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit: `fix: include hostname in cache_safe_name to prevent cache collisions`

### Step 2: Change update_issue_labels_in_cache to accept RepoIdentifier
- [ ] Implementation: change function signature and update `TestCacheIssueUpdate` / `TestCacheUpdateIntegration` call sites
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: change update_issue_labels_in_cache to accept RepoIdentifier`

### Step 3: Change get_all_cached_issues to accept RepoIdentifier
- [ ] Implementation: change function signature and update `TestAdditionalIssuesParameter` / `TestApiFailureHandling` / `TestLastFullRefresh` call sites
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit: `refactor: change get_all_cached_issues to accept RepoIdentifier`

## Pull Request
- [ ] Review all changes for correctness and consistency
- [ ] Write PR summary
