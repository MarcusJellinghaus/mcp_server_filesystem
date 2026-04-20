# Step 1: Extend `IssueManager.list_issues()` with `labels`, `assignee`, `max_results`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

> Implement Step 1 of issue #78 (see `pr_info/steps/summary.md`).
> Extend `IssueManager.list_issues()` and `_list_issues_no_error_handling()` in `src/mcp_workspace/github_operations/issues/manager.py` with three new optional parameters: `labels`, `assignee`, and `max_results`. All three are natively supported by PyGithub's `repo.get_issues()`. Write tests first (TDD), then implement. Run all code quality checks before committing.

## WHERE

- **Modify**: `src/mcp_workspace/github_operations/issues/manager.py`
- **Modify**: `tests/github_operations/test_issue_manager_core.py` (add tests)

## WHAT

### Modified signatures

```python
# In _list_issues_no_error_handling and list_issues:
def _list_issues_no_error_handling(
    self,
    state: str = "open",
    include_pull_requests: bool = False,
    since: Optional[datetime] = None,
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[IssueData]:

def list_issues(
    self,
    state: str = "open",
    include_pull_requests: bool = False,
    since: Optional[datetime] = None,
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[IssueData]:
```

## HOW

- Parameters forwarded to PyGithub's `repo.get_issues()` via `kwargs` dict built conditionally
- `max_results` applied as early-break in the iteration loop (count items added, break when limit reached)
- `labels` passed directly (PyGithub accepts `List[str]`)
- `assignee` passed directly (PyGithub accepts username, `"none"`, or `"*"`)

## ALGORITHM

```
kwargs = {state: state}
if since: kwargs[since] = since
if labels: kwargs[labels] = labels
if assignee: kwargs[assignee] = assignee
issues_iterator = repo.get_issues(**kwargs)
for issue in issues_iterator:
    if not include_pull_requests and issue.pull_request: continue
    issues_list.append(convert_to_issue_data(issue))
    if max_results and len(issues_list) >= max_results: break
```

## DATA

- Input: existing params + `labels: Optional[List[str]]`, `assignee: Optional[str]`, `max_results: Optional[int]`
- Output: `List[IssueData]` (unchanged structure, just filtered/capped)

## TESTS

Add to `tests/github_operations/test_issue_manager_core.py` (or new class within):

1. `test_list_issues_with_labels` — Verify `labels` param forwarded to `repo.get_issues()`
2. `test_list_issues_with_assignee` — Verify `assignee` param forwarded to `repo.get_issues()`
3. `test_list_issues_with_max_results` — Verify iteration stops at `max_results` limit
4. `test_list_issues_max_results_with_pr_filtering` — Verify `max_results` counts only non-PR issues when `include_pull_requests=False`
5. `test_list_issues_combined_params` — Verify all params work together

## COMMIT

```
feat(github): extend IssueManager.list_issues with labels, assignee, max_results (#78)
```
