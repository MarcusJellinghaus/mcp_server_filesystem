# Step 2: Update `_collect_pr_info()` to return `mergeable` + update tests

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: extend
> `_collect_pr_info()` to return `mergeable` as a 4th tuple element.
> Update existing tests first, then update the function. Run all checks after.

## WHERE

- `src/mcp_workspace/checks/branch_status.py` — modify `_collect_pr_info()`
- `tests/checks/test_branch_status.py` — update `TestCollectPRInfo` class

## WHAT

Change return type:

```python
def _collect_pr_info(
    pr_manager: PullRequestManager, branch_name: str
) -> tuple[Optional[int], Optional[str], Optional[bool], Optional[bool]]:
    """Collect PR info for the branch.

    Returns:
        Tuple of (pr_number, pr_url, pr_found, pr_mergeable).
    """
```

## ALGORITHM

```
try:
    prs = pr_manager.find_pull_request_by_head(branch_name)
    if prs:
        pr = prs[0]
        return (pr["number"], pr["url"], True, pr.get("mergeable"))
    return (None, None, False, None)
except Exception:
    return (None, None, None, None)
```

## DATA

- Before: `tuple[Optional[int], Optional[str], Optional[bool]]`
- After: `tuple[Optional[int], Optional[str], Optional[bool], Optional[bool]]`
- 4th element: `mergeable` from `PullRequestData` (True/False/None)

## TEST CHANGES

Update `TestCollectPRInfo`:
1. `test_pr_found` — mock PR dict includes `mergeable: True`, assert 4th element is `True`
2. `test_no_pr` — assert 4th element is `None`
3. `test_exception` — assert 4th element is `None`
4. Add `test_pr_found_mergeable_none` — PR exists but `mergeable` is `None`, assert 4th element is `None`
5. Add `test_pr_found_mergeable_false` — PR exists but `mergeable` is `False`, assert 4th element is `False`
