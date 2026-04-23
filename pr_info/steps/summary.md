# Summary: PR Mergeable Override for Branch Status (Issue #149)

## Problem

`check_branch_status` reports rebase status based on local git state, producing misleading
"Rebase onto origin/main" recommendations even when the PR is perfectly mergeable on GitHub
(e.g. after PR automation pushes a commit). The user gets told to rebase when a squash-merge
would work fine.

## Solution

Use the existing `mergeable` bool from `PullRequestData` (already fetched by PyGithub) to
override the local rebase check when a PR exists and GitHub confirms mergeability.

## Design Changes

### Data flow change

```
Before:  _collect_pr_info() → (number, url, found)
After:   _collect_pr_info() → (number, url, found, mergeable)
```

The 4th tuple element carries the `mergeable` field from `PullRequestData` through to the
orchestrator without changing the existing unpacking pattern.

### New pure function

```python
_apply_pr_merge_override(rebase_needed, rebase_reason, pr_mergeable) → (rebase_needed, rebase_reason)
```

Called in `collect_branch_status()` after both rebase and PR info are collected. Only acts
when `rebase_needed=True` AND `pr_mergeable=True` — overrides rebase to "UP TO DATE" with
descriptive reason. All other cases (False, None, rebase not needed) pass through unchanged.

### Report dataclass

Add `pr_mergeable: Optional[bool] = None` field to `BranchStatusReport`.

### Formatter additions

New `Merge Status:` line under PR section in both formatters:
- Human: `Merge Status: ✅ Mergeable (squash-merge safe)` / `❌ Not mergeable (has conflicts)` / `⏳ Pending`
- LLM: `Mergeable=True/False/None` token in status summary
- Omitted entirely when no PR exists

### Recommendation change

When override applies: "Ready to merge (squash-merge safe)" instead of "Rebase onto origin/main".

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_workspace/checks/branch_status.py` | Add `_apply_pr_merge_override()`, update `_collect_pr_info()` return, add `pr_mergeable` to dataclass, update formatters and recommendations |
| `tests/checks/test_branch_status.py` | Tests for override function, updated `_collect_pr_info` tests, updated orchestrator mock, updated recommendation tests |
| `tests/checks/test_branch_status_pr_fields.py` | Tests for `Merge Status:` line in both formatters |

No new files or modules are created.
