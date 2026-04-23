# Step 3: Add `pr_mergeable` to `BranchStatusReport` + wire override in orchestrator

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 3: add `pr_mergeable`
> field to `BranchStatusReport`, wire the override into `collect_branch_status()`,
> and update `_generate_recommendations()`. Update tests first, then implementation.
> Run all checks after.

## WHERE

- `src/mcp_workspace/checks/branch_status.py` — modify dataclass, orchestrator, recommendations
- `tests/checks/test_branch_status.py` — update `TestCollectBranchStatus`, `TestGenerateRecommendations`

## WHAT

### 3A: Dataclass change

```python
@dataclass(frozen=True)
class BranchStatusReport:
    ...
    pr_found: Optional[bool] = None
    pr_mergeable: Optional[bool] = None  # NEW — add after pr_found
```

### 3B: Orchestrator wiring in `collect_branch_status()`

After step 8 (PR info collection), unpack the 4th element and call override:

```python
# 8. Collect PR info
pr_number, pr_url, pr_found, pr_mergeable = (
    _collect_pr_info(pr_manager, branch_name)
    if pr_manager
    else (None, None, None, None)
)

# 9. Apply PR merge override
rebase_needed, rebase_reason = _apply_pr_merge_override(
    rebase_needed, rebase_reason, pr_mergeable if pr_found else None
)
```

Note: only pass `pr_mergeable` when `pr_found` is truthy — if PR lookup failed (`pr_found=None`)
or no PR exists (`pr_found=False`), pass `None` to skip override.

### 3C: Recommendations update

In `_generate_recommendations()`, add `pr_mergeable` to the input dict and update the
"Ready to merge" logic:

```python
pr_mergeable = report_data.get("pr_mergeable")

# In the final "ready" check, when rebase is not needed:
if (
    ci_status in [CIStatus.PASSED, CIStatus.NOT_CONFIGURED]
    and tasks_ok
    and not rebase_needed
):
    if pr_mergeable is True:
        recommendations.append("Ready to merge (squash-merge safe)")
    else:
        recommendations.append("Ready to merge")
```

## DATA

- `BranchStatusReport.pr_mergeable`: `Optional[bool]`, default `None`
- `report_data` dict gains `"pr_mergeable"` key

## TEST CHANGES

1. `TestCollectBranchStatus.test_full_collection` — update `mock_pr_info.return_value` to 4-tuple, assert `report.pr_mergeable`
2. `TestCollectBranchStatus.test_github_init_failure` — assert `pr_mergeable is None`
3. `TestGenerateRecommendations` — add test: when `rebase_needed=False` due to override + `pr_mergeable=True`, recommendation is "Ready to merge (squash-merge safe)"
4. `TestGenerateRecommendations` — add test: rebase behind + mergeable=True in input → after override in orchestrator, recommendation should say squash-merge safe (this tests the integration path)
5. `create_empty_report()` — no change needed (new field defaults to `None`)
