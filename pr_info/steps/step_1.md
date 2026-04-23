# Step 1: Add `_apply_pr_merge_override()` pure function + tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: add the
> `_apply_pr_merge_override()` pure function to `branch_status.py` with unit tests.
> Follow TDD — write tests first, then implement. Run all checks after.

## WHERE

- `src/mcp_workspace/checks/branch_status.py` — add new function
- `tests/checks/test_branch_status.py` — add `TestApplyPrMergeOverride` class

## WHAT

```python
def _apply_pr_merge_override(
    rebase_needed: bool,
    rebase_reason: str,
    pr_mergeable: Optional[bool],
) -> tuple[bool, str]:
```

## ALGORITHM

```
if not rebase_needed:
    return (rebase_needed, rebase_reason)  # nothing to override
if pr_mergeable is True:
    return (False, "Behind base branch but PR is mergeable (squash-merge safe)")
# pr_mergeable is False or None — keep local result
return (rebase_needed, rebase_reason)
```

## DATA

- Input: `(bool, str, Optional[bool])`
- Output: `(bool, str)` — adjusted rebase status

## TEST CASES

1. `rebase_needed=False` → passthrough (no override needed)
2. `rebase_needed=True, mergeable=True` → `(False, "Behind base branch but PR is mergeable (squash-merge safe)")`
3. `rebase_needed=True, mergeable=False` → unchanged `(True, original_reason)`
4. `rebase_needed=True, mergeable=None` → unchanged `(True, original_reason)`
